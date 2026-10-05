"""Small machine-only settings; never part of an office export or SaaS context."""
import os
from pathlib import Path
import re
import tempfile


def _path():
    return Path(os.environ.get('WORKER_PLACEMENT_CONFIG_DIR', Path.home() / '.config/worker-placement')) / 'research-contact.txt'


def research_contact():
    from officekit.runtime import hosted
    if hosted():
        return None
    try:
        return _path().read_text(encoding='utf-8').strip() or None
    except FileNotFoundError:
        return None


def save_research_contact(value):
    from officekit.runtime import hosted
    if hosted():
        raise ValueError('Use the hosted office connection settings')
    value = value.strip()
    if len(value) > 254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value):
        raise ValueError('Enter a valid contact email for SEC data requests')
    target = _path()
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=target.parent, delete=False) as output:
        output.write(value + '\n')
    try:
        os.replace(output.name, target)  # NamedTemporaryFile is mode 0600.
    finally:
        Path(output.name).unlink(missing_ok=True)
