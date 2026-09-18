"""Build an explicit hosted source tree, never a copy of the monorepo."""
import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
# Code packages only: no household folders, datasets, credentials or Git history.
PACKAGES = ('officekit', 'officekit_ai', 'officekit_signals', 'officekit_research', 'officekit_adapters', 'officekit_agents')
FILES = [str(p.relative_to(ROOT)) for package in PACKAGES
         for p in sorted((ROOT / package).rglob('*.py')) if not {'__pycache__', 'evals'} & set(p.parts)]
FILES += [str(p.relative_to(ROOT)) for p in sorted((ROOT / 'officekit_agents').rglob('*.md'))]
FILES += ['officekit/INTAKE_AGENT.md']
FILES += ['officekit/public/' + name for name in
          ('landing.html', 'site.css', 'site.js', 'auth.js', 'mark.svg', 'install.sh')]
FILES += [str(p.relative_to(ROOT)) for p in sorted((ROOT / 'hosting/app').glob('*.py'))]
FILES += [str(p.relative_to(ROOT)) for p in sorted((ROOT / 'strategies').rglob('*'))
          if p.is_file() and p.name in {'pack.json', 'DECK.md'}]


def stage(destination):
    destination = Path(destination).resolve()
    if destination.exists():
        raise ValueError('Use a new, empty deployment directory')
    destination.mkdir(parents=True)
    for name in FILES:
        src = ROOT / name
        if src.is_symlink() or not src.is_file():
            raise ValueError('Deployment sources must be regular files')
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
    (destination / 'hosting/__init__.py').write_text('')
    for name in ('Dockerfile', 'requirements.txt'):
        shutil.copy2(ROOT / 'hosting/app' / name, destination / name)
    (destination / '.gcloudignore').write_text('.git\n__pycache__\n*.pyc\n')
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination')
    print(stage(parser.parse_args().destination))
