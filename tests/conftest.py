import sys, json, pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def pytest_addoption(parser):
    parser.addoption('--offline', action='store_true', help='Refuse external sockets, including session fixtures; allow loopback HTTP tests')


def pytest_configure(config):
    if not config.getoption('--offline'):
        return
    import socket
    import ipaddress
    original_connect, original_dns = socket.socket.connect, socket.getaddrinfo
    def local(host):
        if host in {'localhost', 'testserver'}:
            return True
        try:
            return ipaddress.ip_address(host).is_loopback
        except ValueError:
            return False
    def connect(sock, address):
        if isinstance(address, tuple) and not local(address[0]):
            raise RuntimeError('Offline test attempted an external network connection')
        return original_connect(sock, address)
    def dns(host, *args, **kwargs):
        if host is not None and not local(host):
            raise RuntimeError('Offline test attempted external DNS')
        return original_dns(host, *args, **kwargs)
    socket.socket.connect, socket.getaddrinfo = connect, dns
    config._offline_originals = original_connect, original_dns


def pytest_unconfigure(config):
    if hasattr(config, '_offline_originals'):
        import socket
        socket.socket.connect, socket.getaddrinfo = config._offline_originals


def pytest_collection_modifyitems(config, items):
    if config.getoption('--offline'):
        for item in items:
            if item.get_closest_marker('integration'):
                item.add_marker(pytest.mark.skip(reason='Live integration excluded by --offline'))


@pytest.fixture(scope="session")
def root():
    return ROOT


@pytest.fixture()
def tmp_record(root):
    """Context helper: temporarily mutate an edge_classifications record, restore after."""
    import shutil, contextlib

    @contextlib.contextmanager
    def _mut(ticker, mutator):
        p = root / "desk" / "data" / "edge_classifications" / f"{ticker}.json"
        bak = p.read_text()
        d = json.loads(bak)
        mutator(d)
        p.write_text(json.dumps(d))
        try:
            yield p
        finally:
            p.write_text(bak)
    return _mut
