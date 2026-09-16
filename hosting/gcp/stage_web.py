"""Build an explicit hosted source tree, never a copy of the monorepo."""
import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
FILES = ['officekit/render_landing.py', 'officekit/public/landing.html',
         'officekit/public/site.css', 'officekit/public/site.js',
         'officekit/public/auth.js', 'officekit/public/mark.svg',
         'officekit/public/install.sh', 'officekit/migration.py', 'officekit/schema.py', 'officekit_ai/models.py',
         'hosting/app/__init__.py', 'hosting/app/main.py', 'hosting/app/auth.py',
         'hosting/app/store.py', 'hosting/app/offices.py', 'hosting/app/routes.py', 'hosting/app/views.py', 'hosting/app/research.py']


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
    (destination / 'officekit/__init__.py').write_text('"""Public presentation only; no office engine is deployed."""\n')
    (destination / 'hosting/__init__.py').write_text('')
    (destination / 'officekit_ai/__init__.py').write_text('')
    for name in ('Dockerfile', 'requirements.txt'):
        shutil.copy2(ROOT / 'hosting/app' / name, destination / name)
    (destination / '.gcloudignore').write_text('.git\n__pycache__\n*.pyc\n')
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination')
    print(stage(parser.parse_args().destination))
