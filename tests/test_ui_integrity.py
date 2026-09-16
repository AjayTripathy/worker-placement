"""The render layer: structural guarantees that killed us on 2026-07-02."""
import re, subprocess, shutil


def test_nothing_after_html_close(root):
    s = (root / "desk" / "ui" / "static" / "index.html").read_text()
    assert s.rstrip().endswith("</html>")


def test_all_alert_buckets_render_inside_body(root):
    s = (root / "desk" / "ui" / "static" / "index.html").read_text()
    body = s[: s.find("</html>")]
    for marker in ("a.go||", "a.no_go||", "a.in_book||", "a.ready||"):
        assert marker in body, f"missing render section for {marker}"


def test_inline_js_parses(root):
    if not shutil.which("node"):
        import pytest
        pytest.skip("node not available")
    s = (root / "desk" / "ui" / "static" / "index.html").read_text()
    js = "\n".join(re.findall(r"<script>(.*?)</script>", s, re.S))
    p = subprocess.run(["node", "--check", "/dev/stdin"], input=js.encode(), capture_output=True)
    assert p.returncode == 0, p.stderr.decode()[:400]
