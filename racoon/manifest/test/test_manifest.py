from racoon.manifest import Manifest, ConsoleOutput
import unittest


class TestManifest(unittest.TestCase):

    def test_manifest_dictionary_parsing(self):
        manifest = Manifest()

        manifest_dict = {
                'name': 'Test manifest',
        }
        manifest.load_dict(manifest_dict)

        manifest.evaluate()

    def test_manifest_status_hooks(self):
        manifest = Manifest()

        manifest_dict = {
                'name': 'Test manifest - status hooks',
        }
        manifest.load_dict(manifest_dict)
        manifest.add_status_hook(ConsoleOutput())

        manifest.evaluate()
