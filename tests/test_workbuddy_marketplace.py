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
                self.assertFalse(plugin['strict'])
                self.assertEqual(plugin['skills'], ['./'])
                self.assertNotIn('mcpServers', plugin)
                self.assertNotIn('hooks', plugin)

    def test_each_install_unit_survives_isolated_copy(self):
        for plugin in builder.build(ROOT)['plugins']:
            with self.subTest(plugin=plugin['name']), tempfile.TemporaryDirectory() as temporary:
                source = (ROOT / plugin['source']).resolve()
                self.assertTrue(source.is_relative_to(ROOT / 'skills'))
                for item in source.rglob('*'):
                    if item.is_symlink():
                        self.assertTrue(item.resolve().is_relative_to(source), str(item))
                cache = Path(temporary) / plugin['name']
                shutil.copytree(source, cache)
                self.assertTrue((cache / plugin['skills'][0] / 'SKILL.md').is_file())
                source_files = {p.relative_to(source): p.read_bytes() for p in source.rglob('*') if p.is_file()}
                cache_files = {p.relative_to(cache): p.read_bytes() for p in cache.rglob('*') if p.is_file()}
                self.assertEqual(source_files, cache_files)


if __name__ == '__main__':
    unittest.main()
