"""Firebase email-link authentication; secrets and OOB codes never enter logs."""
from datetime import timedelta
import hashlib
import json
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class AuthFailure(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


class RateLimit:
    """Bounded process-local abuse budget, in addition to Firebase's quotas.

    Deployed with one worker/instance and max two instances. This is not a
    distributed quota; the limits can multiply by instance count and reset on
    restart. No raw email addresses or authentication codes are retained.
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.events = {}

    def claim(self, email, operation):
        now = time.monotonic()
        key = operation + ':' + hashlib.sha256(email.casefold().encode()).hexdigest()
        with self.lock:
            self.events = {k: [t for t in times if now - t < 3600]
                           for k, times in self.events.items() if times and now - times[-1] < 3600}
            own = self.events.get(key, [])
            recent = sum(now - t < 60 for t in own)
            limit = 1 if operation == 'email' else (60 if operation == 'poll' else 10)
            all_events = self.events.get('global:' + operation, [])
            budget = 120 if operation == 'email' else (7200 if operation == 'poll' else 600)
            if recent >= limit or len(all_events) >= budget:
                raise AuthFailure('Please wait a minute before trying again.', 429)
            self.events.setdefault(key, []).append(now)
            self.events.setdefault('global:' + operation, []).append(now)


class FirebaseBackend:
    def __init__(self, project, api_key, origin):
        import firebase_admin
        self.origin, self.api_key = origin, api_key
        self.app = firebase_admin.initialize_app(options={'projectId': project}, name='worker-placement-web')

    def _request(self, action, data):
        # API key is a project identifier, never a user credential.
        from urllib.parse import urlencode
        url = 'https://identitytoolkit.googleapis.com/v1/accounts:' + action + '?' + urlencode({'key': self.api_key})
        request = Request(url, data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'})
        try:
            with urlopen(request, timeout=20) as response:
                return json.load(response)
        except HTTPError as error:
            try:
                reason = json.loads(error.read()).get('error', {}).get('message', '').split(' : ')[0]
            except (ValueError, AttributeError):
                reason = ''
            if reason in {'INVALID_OOB_CODE', 'EXPIRED_OOB_CODE', 'INVALID_EMAIL', 'EMAIL_NOT_FOUND', 'USER_DISABLED'}:
                raise AuthFailure('This link is invalid, expired or already used. Check your email address, or request a new sign-in link.', 400) from None
            if reason in {'TOO_MANY_ATTEMPTS_TRY_LATER', 'QUOTA_EXCEEDED'}:
                raise AuthFailure('Email sign-in is temporarily rate-limited. Please try again later.', 429) from None
            raise AuthFailure('The email provider could not complete the request. Please try again shortly.', 502) from None
        except (URLError, TimeoutError, ValueError):
            raise AuthFailure('The email provider could not be reached. Please try again shortly.', 502) from None

    def send_email(self, email):
        self._request('sendOobCode', {'requestType': 'EMAIL_SIGNIN', 'email': email,
                                     'continueUrl': self.origin + '/auth/finish', 'canHandleCodeInApp': True})

    def complete(self, email, code):
        from firebase_admin import auth, exceptions
        response = self._request('signInWithEmailLink', {'email': email, 'oobCode': code})
        token = response.get('idToken')
        if not token:
            raise AuthFailure('This account requires an additional sign-in step that is not yet supported.', 401)
        try:
            claims = auth.verify_id_token(token, app=self.app, check_revoked=True)
            if claims.get('email_verified') is not True or str(claims.get('email', '')).casefold() != email.casefold():
                raise AuthFailure('A verified email address is required.', 401)
            age = time.time() - claims.get('auth_time', 0)
            if not 0 <= age <= 300:
                raise AuthFailure('Please sign in again with a fresh email link.', 401)
            return auth.create_session_cookie(token, expires_in=timedelta(days=5), app=self.app)
        except (auth.InvalidIdTokenError, auth.RevokedIdTokenError, auth.UserDisabledError, auth.UserNotFoundError):
            raise AuthFailure('Please request a new sign-in link.', 401) from None
        except exceptions.FirebaseError:
            raise AuthFailure('Your email was verified, but the session could not be created. Please request a new sign-in link.', 502) from None

    def verify(self, cookie):
        from firebase_admin import auth, exceptions
        try:
            claims = auth.verify_session_cookie(cookie, app=self.app, check_revoked=True)
        except (auth.InvalidSessionCookieError, auth.RevokedSessionCookieError, auth.UserDisabledError, auth.UserNotFoundError):
            raise AuthFailure('Sign in again to continue.', 401) from None
        except exceptions.FirebaseError:
            raise AuthFailure('Sign-in could not be checked. Please try again shortly.', 502) from None
        if claims.get('email_verified') is not True or not claims.get('uid') or not claims.get('email'):
            raise AuthFailure('A verified email address is required.', 401)
        return claims
