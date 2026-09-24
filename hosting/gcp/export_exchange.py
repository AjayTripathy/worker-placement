"""Commit the central exchange's contributions to the open-source corpus.

Operator-run. Reads admitted general research from the hosted store and writes
it into the repository's exchange directory, one immutable file per record,
then commits under the exchange's neutral identity. Contributor bindings
(key -> account) are never read here and never leave the service.

    python hosting/gcp/export_exchange.py research_exchange            # write + commit locally
    python hosting/gcp/export_exchange.py research_exchange --push     # ...and publish

Export checks record structure and the retained publisher review's integrity.
The exported receipt asserts that review; it is not an independent new audit
or a cryptographic signature.
"""
import argparse
import os
from pathlib import Path


def export(store, root, include_private=False):
    from hosting.app.exchange import Exchange
    from officekit_research import exchange as corpus
    root = corpus.init(root)
    changed, skipped = [], 0
    for record, envelopes in Exchange(store).export(include_private):
        try:
            from officekit_research.admission import Admission, check_receipt
            review, _ = store.get('exchange/reviews/' + record['id'])
            check_receipt(record, review and review.get('receipt'))
            admission = Admission(record['id'], review['report'])
            if admission.receipt() != review['receipt']:
                raise ValueError('Stored admission report changed')
            for envelope in envelopes or [{'contributor': None, 'attribution': 'anonymous'}]:
                changed += corpus.write(root, record, envelope.get('contributor'),
                                        'verified' if envelope.get('attribution') == 'verified' else 'claimed',
                                        released=include_private, review=admission)
        except ValueError:
            skipped += 1                                   # never publish what fails admission today
    if changed:
        corpus.catalog(root)
        changed.append(root / 'catalog.json')
    sha = corpus.commit(root, changed, 'research: %d contribution file(s) from the central exchange' % len(changed))
    return {'files': len(changed), 'skipped': skipped, 'commit': sha}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path)
    p.add_argument('--push', action='store_true', help='Publish after committing (outward-facing; off by default)')
    p.add_argument('--include-private', action='store_true', help='EXPLICITLY include released private-deal research')
    a = p.parse_args()
    from hosting.app.store import CloudStore
    result = export(CloudStore(os.environ['OFFICE_BUCKET'], os.environ['OFFICE_KMS_KEY']), a.root, a.include_private)
    print(result)
    if a.push and result['commit']:
        from officekit_research import exchange as corpus
        corpus.push(a.root)
        print('Pushed.')
