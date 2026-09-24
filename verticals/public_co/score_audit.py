"""Inventory unbound historical local scores without relabeling their findings.

Run before comparing old cohorts with newly bound results. Review each original
input, filing and evidence; never add a binding to old scores automatically.
"""
import argparse
import hashlib
import json
from pathlib import Path


def audit(root):
    rows = []
    for path in sorted(Path(root).rglob('*.scores.json')):
        raw = path.read_bytes()
        try:
            data = json.loads(raw)
            binding = data.get('binding') if isinstance(data, dict) else None
            bound = isinstance(binding, dict) and binding.get('v') == 2 and binding.get('ticker') == path.name.removesuffix('.scores.json')
        except (ValueError, TypeError):
            bound = False
        rows.append({'path': str(path.relative_to(root)), 'sha256': hashlib.sha256(raw).hexdigest(),
                     'status': 'binding_present_requires_input_validation' if bound else 'excluded_unbound_legacy'})
    return {'schema': 1, 'scores': len(rows), 'excluded_unbound': sum(r['status'] == 'excluded_unbound_legacy' for r in rows),
            'policy': 'Historical outputs derived from unbound scores require evidence review before correctness or performance claims.', 'records': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.write_text(json.dumps(audit(args.root), indent=2) + '\n', encoding='utf-8')
