"""Google OAuth through Identity Platform; provider credentials never enter logs."""
from datetime import timedelta
import hashlib
import json
import secrets
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlparse


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
                raise AuthFailure('This old link is invalid, expired or already used. Continue with Google from the sign-in page.', 400) from None
            if reason in {'TOO_MANY_ATTEMPTS_TRY_LATER', 'QUOTA_EXCEEDED'}:
                raise AuthFailure('Sign-in is temporarily rate-limited. Please try again later.', 429) from None
            if reason in {'INVALID_IDP_RESPONSE', 'INVALID_SESSION_INFO', 'INVALID_PENDING_TOKEN'}:
                raise AuthFailure('This sign-in attempt expired or could not be verified. Start again with Google.', 401) from None
            if reason in {'EMAIL_EXISTS', 'FEDERATED_USER_ID_ALREADY_LINKED'}:
                raise AuthFailure('Google could not safely connect this identity to the existing account. Contact the office administrator for account recovery.', 409) from None
            raise AuthFailure('The sign-in provider could not complete the request. Please try again shortly.', 502) from None
        except (URLError, TimeoutError, ValueError):
            raise AuthFailure('The sign-in provider could not be reached. Please try again shortly.', 502) from None

    def begin_google(self):
        # Identity Platform binds its OAuth state to this browser-only proof and
        # validates both during signInWithIdp. No Google secret is held by the app.
        proof = secrets.token_urlsafe(32)
        response = self._request('createAuthUri', {
            'providerId': 'google.com', 'continueUri': self.origin + '/auth/google/finish',
            'authFlowType': 'CODE_FLOW', 'sessionId': proof,
            'customParameter': {'prompt': 'select_account'},
        })
        url = response.get('authUri', '')
        parsed = urlparse(url)
        if (response.get('sessionId') != proof or parsed.scheme != 'https'
                or parsed.netloc != 'accounts.google.com' or parsed.fragment):
            raise AuthFailure('Google sign-in is not configured correctly. Please try again shortly.', 502)
        return url, proof

    def complete_google(self, callback, proof):
        response = self._request('signInWithIdp', {
            'requestUri': callback, 'sessionId': proof, 'returnSecureToken': True,
            'returnIdpCredential': False, 'returnRefreshToken': False,
        })
        if response.get('needConfirmation') or response.get('errorMessage'):
            raise AuthFailure('Google could not safely connect this identity to the existing account. Contact the office administrator for account recovery.', 409)
        return self._session(response, provider='google.com')

    def complete(self, email, code):
        response = self._request('signInWithEmailLink', {'email': email, 'oobCode': code})
        return self._session(response, email=email)

    def _session(self, response, email=None, provider=None):
        from firebase_admin import auth, exceptions
        token = response.get('idToken')
        if not token:
            raise AuthFailure('This account requires an additional sign-in step that is not yet supported.', 401)
        try:
            claims = auth.verify_id_token(token, app=self.app, check_revoked=True)
            if (claims.get('email_verified') is not True or not claims.get('uid') or not claims.get('email')
                    or (email and str(claims['email']).casefold() != email.casefold())):
                raise AuthFailure('A verified email address is required.', 401)
            if provider and claims.get('firebase', {}).get('sign_in_provider') != provider:
                raise AuthFailure('Sign in with your Google account to continue.', 401)
            age = time.time() - claims.get('auth_time', 0)
            if not 0 <= age <= 300:
                raise AuthFailure('This sign-in attempt expired. Please sign in again.', 401)
            return auth.create_session_cookie(token, expires_in=timedelta(days=5), app=self.app)
        except (auth.InvalidIdTokenError, auth.RevokedIdTokenError, auth.UserDisabledError, auth.UserNotFoundError):
            raise AuthFailure('Please sign in again.', 401) from None
        except exceptions.FirebaseError:
            raise AuthFailure('Your identity was verified, but the session could not be created. Please sign in again.', 502) from None

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
