from requests.exceptions import HTTPError, ConnectionError
from urllib.parse import urlparse
from pathlib import PurePath, Path
from zipfile import ZipFile
from typing import Final
from io import BytesIO
import requests
import hashlib
import shutil
import yaml
import os

HTTP_CHUNK_SIZE: Final[int] = 1024*10

class Manifest:
    """
    The Manifest class parses and executes a manifest in the
    'Racoon Manifest v1' format.
    """
    def __init__(self, allow_directory_traversal=False):
        self.__manifest = {}
        self.__submanifests = []
        self.__status_hooks = []

        self.__used_submanifest_urls = []

        self.__allow_directory_traversal = allow_directory_traversal

    def evaluate(self, manifest=None):
        if manifest is None:
            manifest = self.__manifest

        name = manifest.get('name')
        self.__hook_manifest_parsing_start(name)
        self.__parse_files(manifest)
        self.__hook_manifest_parsing_end(name)
        self.__parse_submanifests(manifest)

    def __parse_submanifests(self, manifest):
        if 'includes' not in manifest:
            return
        for include in manifest['includes']:
            url = urlparse(include.get('url'))
            for used_url in self.__used_submanifest_urls:
                if url.geturl() != used_url.geturl():
                    continue
                raise ValueError('A single manifest can only be imported once.')
            self.__used_submanifest_urls.append(url)

            try:
                with self.__parse_file(include, save_file=False) as f:
                    parsed = yaml.safe_load(f)
            except FileNotFoundError:
                continue
            if not isinstance(parsed, dict):
                raise ValueError('Manifest format invalid')

            self.__submanifests.append(parsed)
            self.evaluate(parsed)

    def __parse_files(self, manifest):
        for file in manifest.get('before', {}).get('files', []):
            self.__parse_file(file)
        for file in manifest.get('files', []):
            self.__parse_file(file)
        for file in manifest.get('after', {}).get('files', []):
            self.__parse_file(file)

    def __parse_file(self, file, save_file=True):
        if 'url' not in file:
            raise ValueError('Manifest format invalid, URL is a required for files.')
        url = urlparse(file.get('url'))
        destination_path = PurePath(file.get('destination')) if save_file else PurePath()
        headers = file.get('headers', {})
        verify_section = file.get('verify', {})

        relative_path_1 = destination_path.parent.name == '.'
        relative_path_2 = destination_path.name == str(destination_path)
        absolute_path = destination_path.parent == Path.cwd()
        if (
            not (relative_path_1 or relative_path_2 or absolute_path) and
            not self.__allow_directory_traversal and
            save_file
        ):
            raise ValueError('Directory traversal is disabled!')

        self.__hook_file_start(url.geturl(), str(destination_path), save_file)

        file = None
        match url.scheme:
            case 'http' | 'https':
                try:
                    file = retrieve_file_http(url.geturl(), headers, str(destination_path), save_file)
                except HTTPError as e:
                    self.__hook_file_end(url.geturl(), str(destination_path), save_file, error=True)
                    if not save_file:
                        raise
                    return
                except ConnectionError as e:
                    self.__hook_file_end(url.geturl(), str(destination_path), save_file, error=True)
                    if not save_file:
                        raise
                    return

            case 'file':
                if url.hostname is not None:
                    raise ValueError('Invalid file URL, hostname must be empty.')

                source_path = PurePath(url.path)
                if not source_path.is_absolute():
                    raise ValueError('Invalid file URL, only absolute paths are supported.')

                if source_path.parent != Path.cwd() and not self.__allow_directory_traversal:
                    raise ValueError('Directory traversal is disabled!')

                try:
                    file = retrieve_file_fs(str(source_path), str(destination_path), save_file)
                except FileNotFoundError:
                    self.__hook_file_end(url.geturl(), str(destination_path), save_file, error=True)
                    if not save_file:
                        raise
                    return
            case _:
                raise ValueError('Manifest format invalid, URL scheme unsupported.')
        self.__hook_file_end(url.geturl(), str(destination_path), save_file)
        if save_file:
            try:
                self.__parse_verify(verify_section, str(destination_path))
            except (ValueError, HTTPError):
                if os.path.exists(str(destination_path)):
                    os.remove(str(destination_path))
                return
        return file

    def __parse_verify(self, verify_section={}, file_path=None):
        self.__hook_verify_start(file_path)

        digest_section = verify_section.get('digest', {})
        try:
            self.__parse_digest(digest_section, file_path)
        except (ValueError, HTTPError):
            self.__hook_verify_end(file_path, error=True)
            raise

        archive_section = verify_section.get('archive', {})
        try:
            self.__parse_archive(archive_section, file_path)
        except ValueError:
            self.__hook_verify_end(file_path, error=True)
            raise

        self.__hook_verify_end(file_path)

    def __parse_digest(self, digest_section={}, file_path=None):
        digest_algorithm = digest_section.get('algorithm')
        digest_text = digest_section.get('text')
        digest_file_section = digest_section.get('file')

        digest = None
        match digest_algorithm:
            case 'md5':
                digest = digest_file('md5', file_path)
            case 'sha256':
                digest = digest_file('sha256', file_path)
            case None:
                return
            case _:
                raise ValueError('Digest algorithm unsupported.')

        if digest_text is not None:
            if digest != digest_text:
                raise ValueError('Invalid file digest!')
        elif digest_file_section is not None:
            with self.__parse_file(digest_file_section, save_file=False) as f:
                file_content = f.read().decode()
                file_digest = file_content.split(' ')[0]
                if digest != file_digest:
                    raise ValueError('Invalid file digest!')

    def __parse_archive(self, archive_section={}, file_path=None):
        archive_contains = archive_section.get('contains', [])
        if len(archive_contains) == 0:
            return

        contains_files = zip_file_contains(file_path, archive_contains)
        if not contains_files:
            raise ValueError('Zip file does not contain specified files!')

    def load_dict(self, manifest_dict={}):
        if not isinstance(manifest_dict, dict):
            raise TypeError('The manifest_dict argument must be of type dict.')
        self.__manifest = manifest_dict

    def load_yaml(self, file=None):
        """Load YAML from a file or a stream."""
        if not isinstance(file, str):
            self.__load_yaml_stream(file)
        with open(file, 'r') as f:
            self.__load_yaml_stream(f)

    def __load_yaml_stream(self, stream):
        """Load YAML from a stream."""
        parsed = yaml.safe_load(stream)
        if isinstance(parsed, dict):
            self.__manifest = parsed
        else:
            raise TypeError('The parsed manifest must be of type dict.')

    def __hook_manifest_parsing_start(self, name):
        for status_hook in self.__status_hooks:
            status_hook.manifest_parsing_start(name)

    def __hook_manifest_parsing_end(self, name):
        for status_hook in self.__status_hooks:
            status_hook.manifest_parsing_end(name)

    def __hook_file_start(self, src, dst, save_file):
        for status_hook in self.__status_hooks:
            status_hook.file_start(src, dst, save_file)

    def __hook_file_end(self, src, dst, save_file, error=False):
        for status_hook in self.__status_hooks:
            status_hook.file_end(src, dst, save_file, error)

    def __hook_verify_start(self, file_name):
        for status_hook in self.__status_hooks:
            status_hook.verify_start(file_name)

    def __hook_verify_end(self, file_name, error=False):
        for status_hook in self.__status_hooks:
            status_hook.verify_end(file_name, error)

    def add_status_hook(self, status_hook=None):
        if status_hook is None:
            raise TypeError('The status_hook argument must not be None.')

        self.__status_hooks.append(status_hook)

def retrieve_file_http(url, headers={}, file_path=None, save_file=False):
    with requests.request('GET', url, headers=headers, stream=True) as r:
        r.raise_for_status()
        if not save_file:
            f = BytesIO()
            for chunk in r.iter_content(chunk_size=HTTP_CHUNK_SIZE):
                f.write(chunk)
            f.seek(0)
            return f
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=HTTP_CHUNK_SIZE):
                f.write(chunk)

def retrieve_file_fs(file_path=None, dst_file_path=None, save_file=False):
    with open(file_path, 'rb') as f:
        if not save_file:
            f_dst = BytesIO()
            shutil.copyfileobj(f, f_dst)
            f_dst.seek(0)
            return f_dst
        with open(dst_file_path, 'wb') as f_dst:
            shutil.copyfileobj(f, f_dst)

def digest_file(name='sha256', file_path=None):
    h = hashlib.new(name)
    with open(file_path, 'rb') as f:
        block = f.read(h.block_size)
        while block:
            h.update(block)
            block = f.read(h.block_size)
        return h.hexdigest()

def zip_file_contains(file_path=None, files=[]):
    with ZipFile(file_path, 'r') as zip_file:
        zip_files = zip_file.namelist()
        for file in files:
            if file not in zip_files:
                return False
        return True
