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
    """
    Create a new :class:`~aletheia_data.AletheiaPooch` with sensible defaults to fetch data files.
    If a version string is given, the Pooch will be versioned, meaning that the local
    storage folder and the base URL depend on the project version. This is necessary
    if your users have multiple versions of your library installed (using virtual
    environments) and you updated the data files between versions. Otherwise, every time
    a user switches environments would trigger a re-download of the data. The version
    string will be appended to the local storage path (for example,
    ``~/.mypooch/cache/v0.1``) and inserted into the base URL (for example,
    ``https://github.com/fatiando/pooch/raw/v0.1/data``). If the version string contains
    ``+XX.XXXXX``, it will be interpreted as a development version.

    Parameters
    ----------
    path : str, PathLike, list or tuple
        The path to the local data storage folder. If this is a list or tuple, we'll
        join the parts with the appropriate separator. The *version* will be appended to
        the end of this path. Use :func:`pooch.os_cache` for a sensible default.
    base_url : str
        Base URL for the remote data source. All requests will be made relative to this
        URL. The string should have a ``{version}`` formatting mark in it. We will call
        ``.format(version=version)`` on this string. If the URL is a directory path, it
        must end in a ``'/'`` because we will not include it.
    version : str or None
        The version string for your project. Should be PEP440 compatible. If None is
        given, will not attempt to format *base_url* and no subfolder will be appended
        to *path*.
    version_dev : str
        The name used for the development version of a project. If your data is hosted
        on Github (and *base_url* is a Github raw link), then ``"master"`` is a good
        choice (default). Ignored if *version* is None.
    env : str or None
        An environment variable that can be used to overwrite *path*. This allows users
        to control where they want the data to be stored. We'll append *version* to the
        end of this value as well.
    registry : dict or None
        A record of the files that are managed by this Pooch. Keys should be the file
        names and the values should be their SHA256 hashes. Only files in the registry
        can be fetched from the local storage. Files in subdirectories of *path* **must
        use Unix-style separators** (``'/'``) even on Windows.
    urls : dict or None
        Custom URLs for downloading individual files in the registry. A dictionary with
        the file names as keys and the custom URLs as values. Not all files in
        *registry* need an entry in *urls*. If a file has an entry in *urls*, the
        *base_url* will be ignored when downloading it in favor of ``urls[fname]``.
    Returns
    -------
    pooch : :class:`~aletheia_data.AletheiaPooch`
        The :class:`~aletheia_data.AletheiaPooch` initialized with the given arguments.
    Examples
    --------
    Create a :class:`~aletheia_data.AletheiaPooch` for a release (v0.1):

     >>> from aletheia_data import create
     >>> p = create(path="myproject",
     ...              base_url="ftp://ftp.cgd.ucar.edu/archive/aletheia-data/tutorial-data/",
     ...              version="v0.1",
     ...              registry={'rasm.nc': '28498798c1934277268ef806112c001a8281b59c18228a17797df38defad8dfb'})
     >>> print(p.path.parts)  # The path is a pathlib.Path
     ('/', 'Users', 'abanihi', '.aletheia', 'data', 'v0.1')
     >>> print(p.base_url)
     ftp://ftp.cgd.ucar.edu/archive/aletheia-data/tutorial-data/
     >>> print(p.registry)
     {'rasm.nc': '28498798c1934277268ef806112c001a8281b59c18228a17797df38defad8dfb'}
    """

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
