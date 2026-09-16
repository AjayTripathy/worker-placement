"""Exercise the downloaded shell installer without network or app startup."""
import os
from pathlib import Path
import subprocess
import sys

import pytest

INSTALLER = Path(__file__).resolve().parents[1] / 'officekit/public/install.sh'
REPO = 'https://github.com/AjayTripathy/worker-placement.git'


@pytest.fixture
def run_installer(tmp_path):
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    fake_git = bin_dir / 'git'
    fake_git.write_text('#!' + sys.executable + '\n' + '''
import os, pathlib, sys
args = sys.argv[1:]
if args[0] == 'clone':
    assert args == ['clone', '--branch', 'main', 'https://github.com/AjayTripathy/worker-placement.git', 'worker-placement']
    if os.environ.get('TEST_CLONE_FAIL'):
        sys.exit(1)
    root = pathlib.Path('worker-placement')
    root.mkdir()
    (root / 'wp').touch()
    (root / '.test-origin').write_text(args[-2])
    start = root / 'start.sh'
    start.write_text('#!/bin/sh\\nprintf "started\\\\n" >> started.txt\\n')
    start.chmod(0o755)
elif args[:1] == ['-C']:
    print((pathlib.Path(args[1]) / '.test-origin').read_text())
else:
    sys.exit(2)
''')
    fake_git.chmod(0o755)
    env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ['PATH'])

    def run(**extra):
        return subprocess.run(['sh', str(INSTALLER)], cwd=tmp_path,
                              env=dict(env, **extra), text=True, capture_output=True)
    return tmp_path, run


def test_public_clone_and_repeat_preserve_office(run_installer):
    root, run = run_installer
    assert run().returncode == 0
    office = root / 'worker-placement/office'
    office.mkdir()
    saved = office / 'answers.json'
    saved.write_text('{"name":"saved office"}')
    assert run().returncode == 0
    assert saved.read_text() == '{"name":"saved office"}'
    assert (root / 'worker-placement/started.txt').read_text().splitlines() == ['started', 'started']


def test_installer_refuses_unrelated_checkout(run_installer):
    root, run = run_installer
    assert run().returncode == 0
    (root / 'worker-placement/.test-origin').write_text('https://example.invalid/unrelated.git')
    result = run()
    assert result.returncode != 0
    assert 'not the expected repository' in result.stderr
    assert (root / 'worker-placement/started.txt').read_text().splitlines() == ['started']


def test_failed_clone_does_not_start(run_installer):
    root, run = run_installer
    assert run(TEST_CLONE_FAIL='1').returncode != 0
    assert not (root / 'worker-placement/started.txt').exists()


def test_existing_folder_is_not_overwritten(run_installer):
    root, run = run_installer
    folder = root / 'worker-placement'
    folder.mkdir()
    (folder / 'keep.txt').write_text('keep me')
    assert run().returncode != 0
    assert (folder / 'keep.txt').read_text() == 'keep me'
