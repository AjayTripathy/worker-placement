"""mailer — the single SMTP rail + the house email-legibility standard
(2026-07-30 user directive: "all emails should strive to be legible").

THE STANDARD — every email any desk module sends:
  1. The SUBJECT states the specific event, never the module name. "LOUD — WAL: new 8-K"
     tells the story from the inbox list; "catalyst event" tells nothing.
  2. FACTS FIRST: what happened, when, and the link come before any doctrine. Internal
     doctrine/reminders go last, clearly labeled.
  3. PLAIN LANGUAGE: form codes, detector names, and state enums are expanded or dropped.
     The reader is a person deciding whether to care, not a parser.
  4. LIVE STATE: position/stake lines come from live caches (positions_cache.json), never
     hand-written strings — those go stale the day an order fills.
  5. Every email ships a simple HTML alternative (bold section headers, clickable links);
     the plain-text part stays canonical and complete.

Senders on this rail: disclosure_watch, band_watch, gauntlet_sentinel (and every module
routing through its _notify), morning_brief. New watches must use mailer, not raw smtplib.
"""
from __future__ import annotations

import html as _html
import re
from pathlib import Path

EMAIL = "4tripathy@gmail.com"
_CRED = Path.home() / ".signalos_smtp"


def _linkify(text: str) -> str:
    """Escape for HTML, then make bare URLs clickable."""
    esc = _html.escape(text)
    return re.sub(r"(https?://[^\s<]+)", r'<a href="\1">\1</a>', esc)


def _send_mime(subject: str, plain: str, html: str | None):
    if not _CRED.exists():
        return False
    try:
        import smtplib
        from email.mime.text import MIMEText
        if html:
            from email.mime.multipart import MIMEMultipart
            m = MIMEMultipart("alternative")
            m.attach(MIMEText(plain))
            m.attach(MIMEText(html, "html"))
        else:
            m = MIMEText(plain)
        m["Subject"] = subject
        m["From"] = m["To"] = EMAIL
        pw = _CRED.read_text().strip().replace(" ", "")   # Google shows app passwords with spaces
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as srv:
            srv.login(EMAIL, pw)
            srv.send_message(m)
        return True
    except Exception as ex:
        print(f"[mailer] email failed: {ex}")
        return False


def send_with_attachment(subject: str, body: str, paths: list[str]) -> bool:
    """send_raw + file attachments (PDF decks etc.). Body stays legible plain text;
    attachments are the artifacts (2026-09-01: principal expects the deck PDF ON the email,
    not a repo path)."""
    if not _CRED.exists():
        return False
    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.application import MIMEApplication
        m = MIMEMultipart()
        m["Subject"] = subject
        m["From"] = m["To"] = EMAIL
        m.attach(MIMEText(body))
        for p in paths:
            pp = Path(p)
            part = MIMEApplication(pp.read_bytes(), Name=pp.name)
            part["Content-Disposition"] = f'attachment; filename="{pp.name}"'
            m.attach(part)
        pw = _CRED.read_text().strip().replace(" ", "")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as srv:
            srv.login(EMAIL, pw)
            srv.send_message(m)
        return True
    except Exception as ex:
        print(f"[mailer] attachment email failed: {ex}")
        return False


def send(subject: str, sections: list[tuple[str, object]], footer: str | None = None) -> bool:
    """Structured send. sections = [(header, body)] where body is a string or list of lines.
    Renders canonical plain text + an HTML alternative with bold headers and live links."""
    txt, htm = [], []
    for head, body in sections:
        lines = body if isinstance(body, list) else [body]
        lines = [str(x) for x in lines if str(x).strip()]
        if not lines:
            continue
        txt.append(head.upper())
        txt.extend(f"  {x}" for x in lines)
        txt.append("")
        htm.append(f"<p style='margin:8px 0 2px'><b>{_html.escape(head)}</b></p>"
                   + "<div style='margin:0 0 4px'>" + "<br>".join(_linkify(x) for x in lines) + "</div>")
    if footer:
        txt.append(footer)
        htm.append(f"<p style='margin:10px 0 0;color:#666'>{_linkify(footer)}</p>")
    return _send_mime(subject, "\n".join(txt), "".join(htm))


def send_raw(subject: str, body: str, mono: bool = True) -> bool:
    """Prebuilt-body send (briefs, sentinel one-liners). Adds an HTML alternative that
    preserves layout (<pre> when mono) and makes URLs clickable."""
    inner = _linkify(body)
    html = (f"<pre style='font-family:ui-monospace,Menlo,monospace;font-size:13px'>{inner}</pre>"
            if mono else inner.replace("\n", "<br>"))
    return _send_mime(subject, body, html)


def send_prebuilt(subject: str, plain: str, html: str) -> bool:
    """For modules that compose their own HTML (disclosure_watch)."""
    return _send_mime(subject, plain, html)


def event_subject(msg: str, prefix: str = "SignalOS") -> str:
    """A subject that carries the event: first line of the message, trimmed to inbox width."""
    first = msg.strip().splitlines()[0] if msg.strip() else "event"
    first = re.sub(r"\s+", " ", first)
    return f"{prefix}: {first[:110]}" + ("…" if len(first) > 110 else "")
