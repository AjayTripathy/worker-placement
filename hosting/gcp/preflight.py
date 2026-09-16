"""Read-only inventory of the selected Worker Placement Google Cloud project.

Uses an already authenticated gcloud CLI; never logs in, enables APIs, creates
resources, reads secret values, changes IAM, or uploads source/office files.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys


class CheckFailed(Exception):
    pass


def read_json(gcloud, project, args):
    command = [gcloud, *args, '--project=' + project, '--format=json', '--quiet']
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=45)
    except subprocess.TimeoutExpired:
        raise CheckFailed('Google Cloud did not respond within 45 seconds.') from None
    except OSError:
        raise CheckFailed('The configured gcloud executable could not be started.') from None
    if result.returncode:
        # Preserve command family and status, not raw provider diagnostics which
        # may echo local paths or authentication data.
        raise CheckFailed('gcloud ' + ' '.join(args[:2]) + ' failed; check sign-in and project permissions.')
    try:
        return json.loads(result.stdout)
    except ValueError:
        raise CheckFailed('Google Cloud returned an unreadable inventory response.') from None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gcloud', default='gcloud', help='gcloud executable or absolute path')
    args = parser.parse_args(argv)
    config = json.loads(Path(__file__).with_name('project.json').read_text())
    project, region = config['project_id'], config['region']
    gcloud = shutil.which(args.gcloud)
    report = {'project_id': project, 'region': region, 'checks': {}, 'errors': []}
    if not gcloud:
        report['errors'].append('Install the Google Cloud CLI or pass --gcloud with its path.')
        print(json.dumps(report, indent=2))
        return 2
    try:
        accounts = read_json(gcloud, project, ['auth', 'list', '--filter=status:ACTIVE'])
        if not accounts:
            raise CheckFailed('Google Cloud sign-in is required. Run gcloud auth login before preflight.')
        info = read_json(gcloud, project, ['projects', 'describe', project])
        if info.get('projectId') != project or info.get('lifecycleState') != 'ACTIVE':
            raise CheckFailed('The selected project was not returned as ACTIVE; stop before deployment.')
        report['checks']['project'] = {k: info.get(k) for k in ('projectId', 'projectNumber', 'lifecycleState')}
    except CheckFailed as error:
        report['errors'].append(str(error))
        print(json.dumps(report, indent=2))
        return 2

    # Independent read failures remain distinct: lack of billing visibility must
    # not be mistaken for a project with billing disabled or no existing service.
    checks = [
        ('billing', ['billing', 'projects', 'describe', project],
         lambda value: {'billing_enabled': value.get('billingEnabled')}),
        ('services', ['services', 'list', '--enabled'],
         lambda value: {'missing': sorted(set(config['required_services']) - {
             item.get('config', {}).get('name') for item in value})}),
        ('cloud_run', ['run', 'services', 'list', '--region=' + region],
         lambda value: [{'name': item.get('metadata', {}).get('name'),
                         'url': item.get('status', {}).get('url')} for item in value]),
        ('cloud_sql', ['sql', 'instances', 'list'],
         lambda value: [{k: item.get(k) for k in ('name', 'region', 'databaseVersion', 'state')}
                        for item in value]),
        ('storage', ['storage', 'buckets', 'list'],
         lambda value: [{'name': item.get('name'), 'location': item.get('location')}
                        for item in value]),
    ]
    enabled = None
    inventory_services = {'cloud_run': 'run.googleapis.com',
                          'cloud_sql': 'sqladmin.googleapis.com',
                          'storage': 'storage.googleapis.com'}
    for name, command, summarize in checks:
        required = inventory_services.get(name)
        if required and (enabled is None or required not in enabled):
            # gcloud may offer to enable a disabled API. Never invoke that path
            # from a read-only check, even when prompts have been disabled.
            report['checks'][name] = {'status': 'not_queried',
                                      'reason': 'Required API is disabled or service inventory is unavailable.'}
            continue
        try:
            value = read_json(gcloud, project, command)
            report['checks'][name] = summarize(value)
            if name == 'services':
                enabled = {item.get('config', {}).get('name') for item in value}
        except (CheckFailed, AttributeError, TypeError) as error:
            report['errors'].append(name + ': ' + (str(error) if isinstance(error, CheckFailed)
                                                   else 'Unexpected inventory shape.'))
    print(json.dumps(report, indent=2))
    return 2 if report['errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
