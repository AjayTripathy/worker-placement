"""A pseudonymous contributor key: attribution without identity.

Shared research needs to answer "whose track record is this?" without ever
answering "who is this?". The key is

    HMAC-SHA256(key = office_id, msg = "officekit-contributor-v1:<epoch>")[:32]

`office_id` is a random UUID that lives only in the office's private records
(it is in cases.PRIVATE_KEYS and can never appear in shared research), so the
key cannot be reversed to an office, yet it is stable wherever that office
goes — local or hosted — with no extra secret to store, back up or migrate.

Two controls stay with the contributor:

  * ROTATE — bump the epoch to use a new identifier with no track record.
    Content and timing may still connect contributions across epochs.
  * ANONYMOUS — contribute with no key at all. The research is still useful;
    it just accrues to nobody's calibration.

LINKABILITY exists in BOTH layers: even a list of researched public symbols
can reveal an office's watchlist. General contributions are anonymous by
default; a stable public pseudonym is an explicit attribution choice. Rotation
changes the identifier, but content and timing can still link old and new keys.
Contextual cases carry additional household context and require disclosure review.

An identifier is not a signature. Anyone who sees a key can type it, so a
claim of authorship is only as strong as the channel it arrived on: the hosted
exchange binds a key to the authenticated account that first used it
("verified"); a key arriving by file or pull request is "claimed".
"""
import hashlib
import hmac
import re

KEY = re.compile(r"[a-f0-9]{32}\Z")
MODES = {"off", "general"}
IDENTITIES = {"pseudonymous", "anonymous"}
DEFAULTS = {"mode": "off", "contributor": "anonymous", "epoch": 0, "exchange": None, "auto_push": True}


def settings(answers):
    """The office's sharing choices. Sharing is OFF until someone turns it on."""
    raw = (answers or {}).get("research_sharing") or {}
    out = {**DEFAULTS, **{k: v for k, v in raw.items() if k in DEFAULTS}}
    if out["mode"] not in MODES or out["contributor"] not in IDENTITIES:
        raise ValueError("Invalid research sharing settings")
    if isinstance(out["epoch"], bool) or not isinstance(out["epoch"], int) or not 0 <= out["epoch"] < 10**6:
        raise ValueError("Invalid contributor epoch")
    if out["exchange"] is not None and not isinstance(out["exchange"], str):
        raise ValueError("Invalid exchange location")
    # Publishing public-equity research is the default once sharing is ON; an office turns it
    # off with auto_push:false. Sharing itself still starts OFF. Private deals never auto-push.
    out["auto_push"] = out["auto_push"] is not False
    return out


def contributor_key(answers):
    """This office's current pseudonym, or None when contributing anonymously."""
    chosen = settings(answers)
    if chosen["contributor"] == "anonymous":
        return None
    office_id = str((answers or {}).get("office_id") or "")
    if len(office_id) < 16:
        raise ValueError("This office has no identity yet; build it once before contributing research")
    message = ("officekit-contributor-v1:%d" % chosen["epoch"]).encode()
    return hmac.new(office_id.encode(), message, hashlib.sha256).hexdigest()[:32]


def rotate(answers):
    """Start a new key. Content/timing may still link it to older contributions."""
    chosen = settings(answers)
    sharing = dict((answers.get("research_sharing") or {}), epoch=chosen["epoch"] + 1)
    answers["research_sharing"] = sharing
    return contributor_key(answers)


def valid(key):
    return key is None or (isinstance(key, str) and bool(KEY.fullmatch(key)))
