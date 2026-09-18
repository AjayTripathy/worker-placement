"""Office-scoped encrypted credentials. Never part of an office revision/export."""
import re
from .auth import AuthFailure
from .store import Conflict

GROUPS = {
    'anthropic': ('ANTHROPIC_API_KEY',),
    'alpaca': ('APCA_API_KEY_ID', 'APCA_API_SECRET_KEY', 'APCA_API_BASE_URL'),
    'ibkr_flex': ('IBKR_FLEX_TOKEN', 'IBKR_FLEX_QUERY_ID'),
    'research': ('OFFICEKIT_CONTACT',),
}


class Credentials:
    def __init__(self, offices):
        self.offices = offices

    def key(self, uid, oid):
        self.offices.read(uid, oid)  # Ownership must be checked, even for metadata.
        return self.offices.prefix(uid, oid) + 'credentials'

    def read(self, uid, oid):
        value, generation = self.offices.db().get(self.key(uid, oid))
        return (value or {}), generation

    def status(self, uid, oid):
        value, generation = self.read(uid, oid)
        return {'revision': str(generation), 'connected': {
            group: all(value.get(k) for k in keys) for group, keys in GROUPS.items()}}

    def update(self, uid, oid, data):
        key = self.key(uid, oid)
        current, generation = self.offices.db().get(key)
        if data.get('credential_revision') != str(generation):
            raise AuthFailure('Connection settings changed. Reload before saving.', 409)
        group = data.get('provider')
        if group not in GROUPS:
            raise AuthFailure('Choose a supported connection.')
        values = dict(current or {})
        if data.get('remove') == '1':
            for name in GROUPS[group]:
                values.pop(name, None)
        else:
            for name in GROUPS[group]:
                value = data.get(name, '').strip()
                if not value or len(value) > 2048 or any(ord(c) < 32 for c in value):
                    raise AuthFailure('Complete all connection fields. Credentials are never displayed again.')
                if name == 'APCA_API_BASE_URL' and value not in {'https://api.alpaca.markets', 'https://paper-api.alpaca.markets'}:
                    raise AuthFailure('Choose Alpaca live or paper accounts.')
                if name == 'IBKR_FLEX_QUERY_ID' and not value.isdigit():
                    raise AuthFailure('Enter the numeric Flex query ID.')
                if name == 'OFFICEKIT_CONTACT' and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value):
                    raise AuthFailure('Enter your contact email for public research data requests.')
                values[name] = value
        try:
            self.offices.db().put(key, values, generation)
        except Conflict:
            raise AuthFailure('Connection settings changed. Reload before saving.', 409) from None
