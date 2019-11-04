import os
import shutil
import tempfile
from pathlib import Path
from warnings import warn

import requests as requests_
from pooch import Pooch
from pooch.utils import check_version, file_hash
from requests_ftp.ftp import FTPSession

from .downloaders import Downloader
from .utils import infer_protocol_options


def create(path, base_url, version=None, version_dev='master', env=None, registry=None, urls=None):

    if isinstance(path, (list, tuple)):
        path = os.path.join(*path)
    if env is not None and env in os.environ and os.environ[env]:
        path = os.environ[env]
    if version is not None:
        version = check_version(version, fallback=version_dev)
        path = os.path.join(str(path), version)
        base_url = base_url.format(version=version)
    path = os.path.expanduser(str(path))
    # Check that the data directory is writable
    try:
        if not os.path.exists(path):
            os.makedirs(path)
        else:
            tempfile.NamedTemporaryFile(dir=path)
    except PermissionError:
        message = (
            "Cannot write to data cache '{}'. "
            'Will not be able to download remote data files. '.format(path)
        )
        if env is not None:
            message = (
                message + "Use environment variable '{}' to specify another directory.".format(env)
            )
        warn(message)
    pup = AletheiaPooch(path=Path(path), base_url=base_url, registry=registry, urls=urls)
    return pup


class AletheiaPooch(Pooch):
    def fetch(self, fname, processor=None, downloader=None):
        self._assert_file_in_registry(fname)

        # Create the local data directory if it doesn't already exist
        if not self.abspath.exists():
            os.makedirs(str(self.abspath))

        full_path = self.abspath / fname

        in_storage = full_path.exists()
        if not in_storage:
            action = 'download'
        elif in_storage and file_hash(str(full_path)) != self.registry[fname]:
            action = 'update'
        else:
            action = 'fetch'

        if action in ('download', 'update'):
            action_word = dict(download='Downloading', update='Updating')
            warn(
                "{} data file '{}' from remote data store '{}' to '{}'.".format(
                    action_word[action], fname, self.get_url(fname), str(self.path)
                )
            )
            if downloader is None:
                downloader = Downloader()
            # Stream the file to a temporary so that we can safely check its hash before
            # overwriting the original
            tmp = tempfile.NamedTemporaryFile(delete=False, dir=str(self.abspath))
            # Close the temp file so that the downloader can decide how to opened it
            tmp.close()
            try:
                downloader(self.get_url(fname), tmp.name, self)
                self._check_download_hash(fname, tmp.name)
                # Ensure the parent directory exists in case the file is in a
                # subdirectory. Otherwise, move will cause an error.
                if not os.path.exists(str(full_path.parent)):
                    os.makedirs(str(full_path.parent))
                shutil.move(tmp.name, str(full_path))
            finally:
                if os.path.exists(tmp.name):
                    os.remove(tmp.name)

        if processor is not None:
            return processor(str(full_path), action, self)

        return str(full_path)

    def is_available(self, fname):
        """
        Check availability of a remote file without downloading it.
        Use this method when working with large files to check if they are available for
        download.
        Parameters
        ----------
        fname : str
            The file name (relative to the *base_url* of the remote data storage) to
            fetch from the local storage.
        Returns
        -------
        status : bool
            True if the file is available for download. False otherwise.
        """
        self._assert_file_in_registry(fname)
        source = self.get_url(fname)
        options = infer_protocol_options(source)
        # For FTP, we use the requests_ftp library
        if options['protocol'] == 'ftp':
            requests = FTPSession()
        else:
            requests = requests_
        response = requests.head(source, allow_redirects=True)
        return bool(response.status_code == 200)
