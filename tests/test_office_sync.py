import json
from copy import deepcopy
import pytest
from officekit import cloud_sync as sync
from officekit.hosting_ui import Hosting
from test_officekit_hosting_ui import bridge, settled, review
from test_hosted_migration import office, client, ORIGIN


def online(bridge):
    hosting, _, _, _ = bridge
    preview = review(hosting);hosting.upload(preview['id'])
    assert settled(hosting)['phase'] == 'complete'
    assert sync.enrollment(hosting.folder)['status'] == 'synced'
    return hosting.folder


def test_local_upload_hosted_download_deletions_and_restart(bridge):
    folder = online(bridge)
    path = folder/'research/memo.md';path.write_text('local edit')
    assert sync.tick(folder)['status'] == 'synced'
    auth = bridge[2];oid = sync.read(folder)['office_id']
    receipt, docs = sync.remote(auth, oid)
    assert docs['research/memo.md'] == b'local edit'
    path.unlink();sync.tick(folder)
    assert 'research/memo.md' not in sync.remote(auth, oid)[1]
    # A hosted update to retained research using the same snapshot API.
    state = sync.read(folder)
    other = folder.parent/'other';other.mkdir()
    for name, data in sync.remote(auth, oid)[1].items():
        p=other/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    (other/'research').mkdir(exist_ok=True);(other/'research/new.md').write_text('hosted edit')
    manifest, chunks, _ = sync.local(other)
    sync.cloud.upload_snapshot(manifest, chunks, auth, state['revision'])
    assert sync.tick(folder)['status'] == 'synced'
    assert (folder/'research/new.md').read_text() == 'hosted edit'
    assert list((folder/'.sync-backups').glob('*.json'))


def test_two_sided_conflict_and_stale_review_never_overwrite(bridge):
    folder = online(bridge);auth = bridge[2]
    path = folder/'research/memo.md';path.write_text('remote first')
    manifest,chunks,_=sync.local(folder)
    sync.cloud.upload_snapshot(manifest,chunks,auth,sync.read(folder)['revision'])
    path.write_text('local second')
    state=sync.tick(folder)
    assert state['status']=='conflict' and path.read_text()=='local second'
    path.write_text('local third')
    with pytest.raises(ValueError): sync.tick(folder, 'hosted', state['review'])
    state=sync.tick(folder)
    sync.tick(folder,'hosted',state['review'])
    assert path.read_text()=='remote first'


def test_changed_account_pauses_and_does_not_send_office(bridge):
    folder=online(bridge);bridge[2]['email']='bob@example.com'
    with pytest.raises(ValueError,match='account changed'):sync.tick(folder)


def test_transaction_rolls_back_files_and_rejects_symlinks(bridge, monkeypatch):
    folder=online(bridge);_,_,docs=sync.local(folder)
    page=folder/'pages/office.html';page.parent.mkdir(exist_ok=True);page.write_text('old page')
    after=dict(docs,**{'research/memo.md':b'new'})
    import officekit.serve
    def broken_render(*args):
        page.write_text('partial new page')
        raise RuntimeError('render failed')
    monkeypatch.setattr(officekit.serve,'render_saved_office',broken_render)
    with pytest.raises(RuntimeError):sync.apply(folder,docs,after)
    assert sync.local(folder)[2]==docs
    assert page.read_text()=='old page'
    path=folder/'research/memo.md';path.unlink();path.symlink_to(folder/'answers.json')
    with pytest.raises(ValueError):sync.apply(folder,docs,after)
