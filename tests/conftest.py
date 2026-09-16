import sys, json, pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


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
