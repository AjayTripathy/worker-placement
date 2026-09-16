"""Anonymize confirmed account IDs without changing research identifiers."""

BINARY = (b'%PDF', b'PK\x03\x04', b'\x89PNG', b'\xff\xd8\xff', b'GIF87a', b'GIF89a', b'\x1f\x8b')


class AccountRedactor:
    """Stable aliases from a private registry; the mapping is never published.

    This is targeted redaction, not an exhaustive secret scanner. Publication
    still requires reviewing unknown account identifiers and credential findings.
    """
    def __init__(self, identifiers):
        values = sorted({str(v).encode() for v in identifiers if v})
        self.aliases = {value: ('ACCOUNT_%03d' % (i + 1)).encode()
                        for i, value in enumerate(values)}

    def clean(self, data):
        present = [value for value in self.aliases if value in data]
        if not present:
            return data, 0
        if data.startswith(BINARY) or b'\x00' in data:
            # Editing arbitrary binary bytes can corrupt a source document.
            raise ValueError('Account identifier in a binary document; review required')
        count = 0
        for value in present:
            count += data.count(value)
            data = data.replace(value, self.aliases[value])
        return data, count
