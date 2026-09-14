#!/usr/bin/env python3
"""Install the catalog using a WorkBuddy CLI in an isolated config, then cold-load it."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def hashes(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cli', required=True, help='Path to the WorkBuddy-bundled codebuddy executable')
    parser.add_argument('--source', default=str(ROOT), help='Local repository or canonical GitHub source')
    args = parser.parse_args()
    catalog = json.loads((ROOT / '.codebuddy-plugin/marketplace.json').read_text())
    with tempfile.TemporaryDirectory(prefix='zhijian-workbuddy-verify-') as temporary:
        config = Path(temporary) / 'config'
        work = Path(temporary) / 'workspace'
        work.mkdir()
        env = {**os.environ, 'CODEBUDDY_CONFIG_DIR': str(config), 'DISABLE_TELEMETRY': '1'}

        def run(*arguments):
            result = subprocess.run([args.cli, 'plugin', *arguments], cwd=work, env=env,
                                    text=True, capture_output=True, timeout=120)
            if result.returncode:
                raise RuntimeError(f'{arguments}: {result.stdout}\n{result.stderr}')
            return result.stdout

        run('marketplace', 'add', args.source)
        for plugin in catalog['plugins']:
            run('install', plugin['name'] + '@zhijian-skills')
            print('Installed: ' + plugin['name'], flush=True)
        # A fresh process must discover the plugins from their immutable caches.
        installed = {p['id']: p for p in json.loads(run('list', '--json'))}
        expected = {p['name'] + '@zhijian-skills' for p in catalog['plugins']}
        if set(installed) != expected:
            raise RuntimeError(f'Cold-load catalog mismatch: {set(installed)} != {expected}')
        files = 0
        for plugin in catalog['plugins']:
            record = installed[plugin['name'] + '@zhijian-skills']
            if not record['enabled'] or record['version'] != plugin['version']:
                raise RuntimeError(f'Inactive or stale plugin: {record}')
            cache = Path(record['installPath'])
            if not cache.resolve().is_relative_to(config.resolve()):
                raise RuntimeError(f'Installation escaped isolated config: {cache}')
            payload = cache / 'skills' / plugin['name']
            if payload.is_symlink() or not (payload / 'SKILL.md').is_file():
                raise RuntimeError(f'Incomplete materialized Skill: {payload}')
            original = hashes(ROOT / 'skills' / plugin['name'])
            if hashes(payload) != original:
                raise RuntimeError(f'Payload hash mismatch: {plugin["name"]}')
            files += len(original)
        print(f'PASS: {len(installed)} plugins cold-loaded; {files} payload files match SHA-256.')


if __name__ == '__main__':
    main()
