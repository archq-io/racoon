from racoon.manifest import Manifest, ConsoleOutput
from urllib.parse import urlparse
from os.path import abspath
import argparse
import racoon
import sys

def setup_args():
    parser = argparse.ArgumentParser(description='Racoon')

    parser.add_argument('manifest', action='extend', nargs='+',
                        help='Path to the manifest file')
    parser.add_argument('-u', '--allow-directory-traversal', action='store_true',
                        help='Allow access to directories other than the current working directory (unsafe)')
    parser.add_argument('--version', action='version', version=racoon.__version__)

    return parser

def main():
    version = racoon.__version__
    BANNER_POS = 18
    spaces = ' ' * (BANNER_POS-(len(version)+1)//2)
    print(racoon._banner, '{0}v{1}\n'.format(spaces, version), sep='')

    parser = setup_args()
    args = parser.parse_args()

    manifest = Manifest(allow_directory_traversal=args.allow_directory_traversal)
    manifest.add_status_hook(ConsoleOutput())

    if len(args.manifest) == 1 and urlparse(args.manifest[0]).scheme == '':
        manifest.load_yaml(args.manifest[0])
    else:
        manifest_dict = {
                'name': 'Auto-generated top-level manifest',
                'includes': [],
        }
        for path in args.manifest:
            manifest_path = abspath(path) if urlparse(path).scheme == '' else path
            url = urlparse(manifest_path, scheme='file')
            manifest_dict['includes'].append({'url': url.geturl()})
        manifest.load_dict(manifest_dict)

    manifest.evaluate()

if __name__ == "__main__":
    main()
