"""Research exchange inside the shared revision-gated office transport."""
import json
from officekit.migration import parse_json
from officekit.mandates import require_revision
from officekit.commitments import revision
from officekit.office_lock import locked
from officekit_research.cases import MAX_BYTES, approve, digest, import_bundle, prepare_case

POSTS = {'/research/import', '/research/prepare', '/research/approve'}


def handle(route, folder, get):
    from officekit.render_research import draft_page
    from officekit.strategy_proposals import load
    with locked(folder):
        answers = json.loads((folder / 'answers.json').read_text())
        require_revision(answers, get('revision'))
        if route == '/research/prepare':
            p = load(folder, get('pid'))
            if p['status'] in {'queued', 'running'}:
                raise ValueError('Wait for the current review to finish before preparing a contribution')
            return draft_page(prepare_case(p, get('symbol')), revision(answers)), 'text/html; charset=utf-8'
        if route == '/research/approve':
            if get('reviewed') != 'yes':
                raise ValueError('Review the case projection and source permissions before exchanging it')
            raw = get('projection')
            if len(raw.encode()) > MAX_BYTES:
                raise ValueError('Research case exceeds its size limit')
            case = parse_json(raw)
            grants = parse_json(get('grants') or '[]')
            bundle = approve({'case': case}, digest(case), grants)
            return json.dumps(bundle, indent=2, ensure_ascii=False), 'application/json; charset=utf-8'
        raw = get('bundle_file') or get('bundle')
        if isinstance(raw, bytes):
            if len(raw) > MAX_BYTES:
                raise ValueError('Research case exceeds its size limit')
            try:
                raw = raw.decode('utf-8')
            except UnicodeDecodeError:
                raise ValueError('Choose a UTF-8 research case JSON file') from None
        if len(raw.encode()) > MAX_BYTES:
            raise ValueError('Research case exceeds its size limit')
        import_bundle(folder, parse_json(raw))
        return None, None
