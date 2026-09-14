"""Keep the marketplace install paths, versions and complete payloads honest."""

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('marketplace_builder', ROOT / 'scripts/build_workbuddy_marketplace.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class WorkBuddyMarketplaceTest(unittest.TestCase):
    def test_catalog_matches_registry_and_docs(self):
        actual = json.loads((ROOT / builder.OUTPUT).read_text())
        self.assertEqual(actual, builder.build(ROOT))
        records = {r['name']: r for r in json.loads((ROOT / 'registry/skills.json').read_text())['skills'] if r['lifecycle'] == 'active'}
        self.assertEqual(set(records), {p['name'] for p in actual['plugins']})
        for plugin in actual['plugins']:
            with self.subTest(plugin=plugin['name']):
                self.assertEqual(plugin['version'], records[plugin['name']]['version'])
                self.assertTrue(plugin['strict'])
                self.assertEqual(plugin['skills'], ['./skills/' + plugin['name']])
                self.assertNotIn('mcpServers', plugin)
                self.assertNotIn('hooks', plugin)
        for path, expected in builder.artifacts(ROOT).items():
            self.assertEqual((ROOT / path).read_text(), expected)

    def test_each_install_unit_survives_isolated_copy(self):
        for plugin in builder.build(ROOT)['plugins']:
            with self.subTest(plugin=plugin['name']), tempfile.TemporaryDirectory() as temporary:
                source = (ROOT / plugin['source']).resolve()
                self.assertTrue(source.is_relative_to(ROOT / 'plugins'))
                payload = (source / plugin['skills'][0]).resolve()
                self.assertEqual(payload, ROOT / 'skills' / plugin['name'])
                for item in payload.rglob('*'):
                    if item.is_symlink():
                        self.assertTrue(item.resolve().is_relative_to(payload), str(item))
                cache = Path(temporary) / plugin['name']
                shutil.copytree(source, cache)
                self.assertTrue((cache / plugin['skills'][0] / 'SKILL.md').is_file())
                installed = cache / plugin['skills'][0]
                self.assertFalse(installed.is_symlink())
                self.assertTrue((cache / '.codebuddy-plugin/plugin.json').is_file())
                source_files = {p.relative_to(payload): p.read_bytes() for p in payload.rglob('*') if p.is_file()}
                cache_files = {p.relative_to(installed): p.read_bytes() for p in installed.rglob('*') if p.is_file()}
                self.assertEqual(source_files, cache_files)


if __name__ == '__main__':
    unittest.main()
