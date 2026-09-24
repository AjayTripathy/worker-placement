"""Real local-client session handshake; hostile-request tests deliberately omit it."""
from urllib.parse import urlsplit
from urllib.request import urlopen


def headers(url):
    parsed = urlsplit(url)
    origin = parsed.scheme + '://' + parsed.netloc
    with urlopen(origin + '/local-session', timeout=10) as response:
        token = response.headers['X-Office-Local-CSRF']
    assert token
    return {'Origin': origin, 'X-Office-Local-CSRF': token}
