#!/usr/bin/env python3
"""Build WorkBuddy's catalog from the canonical Registry and Chinese docs."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path('.codebuddy-plugin/marketplace.json')
REPOSITORY = 'https://github.com/zjp1997720/zhijian-skills'


def description(document: Path) -> str:
    text = document.read_text(encoding='utf-8')
    headline = re.search(r'<strong>(.*?)</strong>', text, re.S)
    if headline:
        return html.unescape(re.sub(r'<[^>]+>', '', headline.group(1))).strip()
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith(('#', '<', '>', '[', '!', '`', '|', '-')):
            return line
    raise ValueError(f'No description found: {document}')


def build(root: Path) -> dict:
    registry = json.loads((root / 'registry/skills.json').read_text(encoding='utf-8'))
    plugins = []
    for record in registry['skills']:
        if record['lifecycle'] != 'active':
            continue
        name = record['name']
        path = record['path']
        if path != f'skills/{name}' or not (root / path / 'SKILL.md').is_file():
            raise ValueError(f'Invalid Skill payload: {path}')
        summary = description(root / record['documentation_zh'])
        if record['harnesses'] == ['codex']:
            summary = '【需 Codex 宿主能力】' + summary
        plugins.append({
            'name': name,
            'source': './' + path,
            'description': summary,
            'version': record['version'],
            'author': {'name': '智见 AI'},
            'homepage': REPOSITORY + '/blob/main/' + record['documentation_zh'],
            'repository': REPOSITORY,
            # The existing self-contained Skill directory is the plugin payload.
            # No second copy or per-Skill manifest/version is maintained.
            'strict': False,
            'skills': ['./'],
        })
    return {
        'name': 'zhijian-skills',
        'owner': {'name': '智见 AI'},
        'description': '智见 AI 开源 Skills，按需安装；各项运行条件请查看文档。',
        'plugins': plugins,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail if the committed catalog is stale')
    args = parser.parse_args()
    rendered = json.dumps(build(ROOT), ensure_ascii=False, indent=2) + '\n'
    destination = ROOT / OUTPUT
    if args.check:
        if not destination.is_file() or destination.read_text(encoding='utf-8') != rendered:
            parser.exit(1, 'WorkBuddy catalog is stale; run scripts/build_workbuddy_marketplace.py\n')
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(rendered, encoding='utf-8')
    print(f'WorkBuddy catalog: {len(build(ROOT)["plugins"])} Skills; {"checked" if args.check else "written"}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
