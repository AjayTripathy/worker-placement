"""The central research exchange: authenticated contributions of GENERAL research.

Offices contribute securities evaluated for no particular investor; everyone
reads them. This service is the one place an attribution can be VERIFIED: a
pseudonymous contributor key is bound, on first use, to the authenticated
account that presented it. Anyone can type a key, but only that account can
contribute under it afterwards — so a track record cannot be poisoned or
borrowed. The binding (key -> tenant hash) is private to the service and is
never returned, listed or exported.

Contributions pass schema, digest, privacy and independent claim-support checks
against publisher-owned evidence. A verified key means account binding, not
proof of authorship or truth. Contextual cases require separate human review.
"""
from datetime import datetime, timezone
import hashlib
import re

from .auth import AuthFailure
from .offices import tenant
from .store import Conflict, required_store
from officekit_research import exchange as corpus
from officekit_research.contributor import valid as valid_key

SYMBOL = re.compile(r'[A-Z0-9][A-Z0-9.^-]{0,14}\Z')
RECORD = re.compile(r'[a-f0-9]{64}\Z')
MAX_LISTING = 200


def configured_exchange(store):
    """Publisher credentials are deployment configuration, never tenant input.

    No configured reviewer means read-only exchange: submissions return 503.
    The source loader resolves the subject itself and cannot fetch caller URLs.
    """
    import os
    model = os.environ.get('RESEARCH_REVIEW_MODEL')
    key = os.environ.get('RESEARCH_REVIEW_API_KEY')
    if not model or not key:
        return Exchange(store)
    from officekit_ai.models import provider_client
    from officekit_research.admission import model_reviewer
    from officekit_research import build_pack, _cik, SOURCE_CLASSES
    from officekit_research.funds import FUND_PAGES
    contact = os.environ.get('RESEARCH_CONTACT')
    def evidence_loader(record):
        subject = record['subject']
        symbol = subject['symbol']
        if subject['instrument'] == 'etf':
            if symbol not in FUND_PAGES:
                raise ValueError('No trusted issuer source registered for this fund')
        elif subject['instrument'] == 'stock':
            if not contact or not _cik(symbol, contact):
                raise ValueError('No public registrant resolved for this stock')
        else:
            raise ValueError('Private release requires an operator-configured source resolver')
        sections = [e['section'] for e in record['evidence']]
        if any(SOURCE_CLASSES.get(s, 'private') == 'private' for s in sections):
            raise ValueError('Evidence is not declared public')
        return build_pack(symbol, contact=contact, sources=sections)
    provider = os.environ.get('RESEARCH_REVIEW_PROVIDER', 'openai')
    client = provider_client(provider, {'api_key_env': 'RESEARCH_REVIEW_API_KEY',
                                       'reasoning_effort': os.environ.get('RESEARCH_REVIEW_REASONING', 'medium')})
    return Exchange(store, evidence_loader=evidence_loader, reviewer=model_reviewer(client, model))


def today():
    return datetime.now(timezone.utc).date().isoformat()


class BoundExchange:
    """In-process equivalent of the HTTP client, bound to an authenticated UID."""
    def __init__(self, service, uid):
        self.service, self.uid = service, uid

    def submit(self, record, contributor=None):
        if corpus.is_private(record):
            raise ValueError('Private research requires a separate explicit release')
        try:
            return self.service.submit(self.uid, record, contributor)
        except AuthFailure as exc:
            raise ValueError(str(exc)) from None

    def find(self, symbol, instrument, protocol_hash, **kwargs):
        try:
            records = [self.service.read(symbol, r['id']) for r in self.service.listing(symbol)
                       if r['instrument'] == instrument and r['protocol_hash'] == protocol_hash]
            record, state = corpus.select(records, instrument, protocol_hash, **kwargs)
            return record, state, self.service.provenance(symbol, record['id']) if record else None
        except AuthFailure as exc:
            raise ValueError(str(exc)) from None


class Exchange:
    def __init__(self, store, *, evidence_loader=None, reviewer=None):
        self.store = store
        self.evidence_loader = evidence_loader
        self.reviewer = reviewer

    def db(self):
        return required_store(self.store)

    def _review(self, record):
        """Reuse only a current, intact review in the publisher's private store."""
        from officekit_research.admission import Admission, check_receipt
        review, generation = self.db().get('exchange/reviews/' + record['id'])
        try:
            check_receipt(record, review and review.get('receipt'))
            admission = Admission(record['id'], review['report'])
            if admission.receipt() == review['receipt']:
                return admission, generation
        except (ValueError, KeyError, TypeError):
            pass
        return None, generation

    def _bind(self, uid, contributor):
        """Trust on first use. Returns 'verified', or refuses a key owned by another account."""
        key = 'exchange/contributors/' + contributor
        owner, generation = self.db().get(key)
        mine = tenant(uid)
        if owner is None:
            try:
                self.db().put(key, {'tenant': mine, 'bound_on': today()}, generation)
            except Conflict:
                owner, _ = self.db().get(key)      # lost a race: whoever won owns it
                if not owner or owner.get('tenant') != mine:
                    raise AuthFailure('This contributor key belongs to another account.', 403) from None
        elif owner.get('tenant') != mine:
            raise AuthFailure('This contributor key belongs to another account.', 403)
        return 'verified'

    def submit(self, uid, record, contributor=None, release_private=False):
        try:
            record = corpus.admit(record)
        except ValueError as error:
            raise AuthFailure(str(error)) from None
        # Private-deal research is never accepted as a side effect of an agent's
        # routine contribution. The caller must say so, by name, for this record.
        if corpus.is_private(record) and release_private is not True:
            raise AuthFailure('Private-deal research is shared only by an explicit release.', 409)
        if not valid_key(contributor):
            raise AuthFailure('Invalid contributor key.')
        # A client-provided support verdict, source snapshot or visibility label
        # is not authority. Fetch/review through publisher-owned adapters only.
        admission, generation = self._review(record)
        if admission is None:
            if self.evidence_loader is None or self.reviewer is None:
                raise AuthFailure('Research admission is unavailable: configure publisher evidence and independent review.', 503)
            from officekit_research.admission import verify
            try:
                admission = verify(record, self.evidence_loader(record), self.reviewer)
            except ValueError as error:
                raise AuthFailure(str(error), 422) from None
            except Exception:
                raise AuthFailure('Publisher evidence is unavailable; research was not admitted.', 503) from None
            # Persist before exposing the record. A failed later write may leave
            # an orphan review, but cannot expose unreviewed research. A retry
            # reuses this exact content/policy approval without another model call.
            try:
                self.db().put('exchange/reviews/' + record['id'],
                              {'receipt': admission.receipt(), 'report': admission.report}, generation)
            except Conflict:
                admission, _ = self._review(record)
                if admission is None:
                    raise AuthFailure('Research admission changed concurrently; retry the submission.', 409) from None
        attribution = self._bind(uid, contributor) if contributor else 'anonymous'
        symbol, rid = record['subject']['symbol'], record['id']
        new = False
        try:
            self.db().put('exchange/general/' + symbol + '/' + rid, record)
            new = True
        except Conflict:
            pass                                     # identical research already contributed; add the attribution
        # An anonymous attribution is keyed by a per-record hash so one account
        # cannot inflate "N contributors" by resubmitting, yet cannot be linked across records.
        who = contributor or 'anonymous-' + hashlib.sha256((tenant(uid) + ':' + rid).encode()).hexdigest()[:16]
        try:
            self.db().put('exchange/attribution/' + rid + '/' + who, {
                'schema': corpus.ATTRIBUTION, 'record_id': rid, 'contributor': contributor,
                'attribution': attribution, 'protocol_hash': record['protocol_hash'], 'submitted_on': today()})
        except Conflict:
            pass
        return {'status': 'contributed' if new else 'already_present', 'record_id': rid, 'attribution': attribution}

    def listing(self, symbol):
        if not isinstance(symbol, str) or not SYMBOL.fullmatch(symbol.upper()):
            raise AuthFailure('Invalid symbol.')
        prefix = 'exchange/general/' + symbol.upper() + '/'
        out = []
        for name in sorted(self.db().names(prefix))[:MAX_LISTING]:
            record, _ = self.db().get(name)
            if record:
                try:
                    self.read(symbol.upper(), record['id'])
                except AuthFailure:
                    continue
                out.append({'id': record['id'], 'as_of': record['as_of'], 'instrument': record['subject']['instrument'],
                            'standing': record['assessment']['standing'], 'tier': record['tier'],
                            'models': record['models'], 'protocol_hash': record['protocol_hash'],
                            'contributors': len(self.db().names('exchange/attribution/' + record['id'] + '/'))})
        return sorted(out, key=lambda r: (r['as_of'], r['id']), reverse=True)

    def read(self, symbol, rid):
        if not isinstance(symbol, str) or not SYMBOL.fullmatch(symbol.upper()) or not isinstance(rid, str) or not RECORD.fullmatch(rid):
            raise AuthFailure('Invalid research identity.')
        record, _ = self.db().get('exchange/general/' + symbol.upper() + '/' + rid)
        if record is None:
            raise AuthFailure('Research not found.', 404)
        try:
            corpus.admit(record)
            if record['id'] != rid or record['subject']['symbol'] != symbol.upper():
                raise ValueError('Stored identity mismatch')
        except ValueError:
            raise AuthFailure('Research failed structural validation.', 409) from None
        admission, _ = self._review(record)
        if admission is None:
            raise AuthFailure('Research is awaiting claim admission.', 409) from None
        return record

    def provenance(self, symbol, rid):
        self.read(symbol, rid)
        # Only public attribution, never the account binding or exact request time.
        envelopes = []
        for key in self.db().names('exchange/attribution/' + rid + '/'):
            item, _ = self.db().get(key)
            envelopes.append(item)
        review, _ = self.db().get('exchange/reviews/' + rid)
        return {'record_id': rid, 'attributions': envelopes, 'admission': review['receipt']}

    def export(self, include_private=False):
        """Everything publishable, for the operator's commit to the open-source corpus.
        Yields (record, [attribution envelopes]). Contributor bindings are never included.
        Private-deal research is left out unless the operator asks for it by name."""
        for name in sorted(self.db().names('exchange/general/')):
            record, _ = self.db().get(name)
            if not record or (corpus.is_private(record) and not include_private):
                continue
            try:
                self.read(record['subject']['symbol'], record['id'])
            except AuthFailure:
                continue
            envelopes = []
            for who in sorted(self.db().names('exchange/attribution/' + record['id'] + '/')):
                envelope, _ = self.db().get(who)
                if envelope:
                    envelopes.append(envelope)
            yield record, envelopes
