from ftplib import FTP, Error, error_perm
from pathlib import Path

from tqdm.auto import tqdm

from .config import conf


class FTPDownloader:
    """
    Download manager for fetching files over FTP.

    When called, downloads the given file URL into the specified local file. Uses the
    :mod:`ftplib` library to manage downloads.
    """

    def __init__(
        self,
        host,
        port=21,
        username=None,
        password=None,
        acct=None,
        timeout=None,
        progressbar=True,
        blocksize=1024,
        **kwargs,
    ):
        """

        Parameters
        ----------
        host : str
            The remote server name/ip to connect to
        port : int, optional
            Port to connect with, by default 21
        username : str, optional
            If authenticating, the user's identifier, by default None
        password : str, optional
           User's password on the server, if using authentication, by default None
        acct : str, optional
            Some servers also need an "account" string for auth, by default None
        timeout : int, optional
            default timeout for all ftp socket operations for this instance, by default None
        progressbar : bool, optional
            If True, will print a progress bar of the download to
            standard error (stderr), by default True
        blocksize : int, optional
            The maximum number of bytes to read from the
            socket at one time, by default 1024

        Raises
        ------
        ValueError
            [description]
        """
        self.host = host
        self.port = port
        self.ftp = None
        self.username = username
        self.password = password
        self.cred = username, password, acct
        self.timeout = timeout
        self.progressbar = progressbar
        self.blocksize = blocksize
        self.kwargs = kwargs
        self._connect()

    def _connect(self):
        self.ftp = FTP(timeout=self.timeout)
        self.ftp.connect(self.host, self.port)
        self.ftp.login(*self.cred)

    def __del__(self):
        if self.ftp is not None:
            self.ftp.close()

    def _strip_protocol(self, path):
        return '/' + path.lstrip('/').rstrip('/')

    def ls(self, path, detail=True):
        """List objects at path.

        This should include subdirectories and files at that location. The
        difference between a file and a directory must be clear when details
        are requested.

        Parameters
        ----------
        path: str
        detail: bool
            if True, gives a list of dictionaries, where each is the same as
            the result of ``info(path)``. If False, gives a list of paths
            (str).

        Returns
        -------
        List of strings if detail is False, or list of directory information
        dicts if detail is True.
        """
        self.dircache = {}
        path = self._strip_protocol(path)
        out = []
        if path not in self.dircache:
            try:
                try:
                    out = [
                        (fn, details)
                        for (fn, details) in self.ftp.mlsd(path)
                        if fn not in ['.', '..'] and details['type'] not in ['pdir', 'cdir']
                    ]
                except error_perm:
                    out = _mlsd2(self.ftp, path)  # Not platform independent
                for fn, details in out:
                    if path == '/':
                        path = ''  # just for forming the names, below
                    details['name'] = '/'.join([path, fn.lstrip('/')])
                    if details['type'] == 'file':
                        details['size'] = int(details['size'])
                    else:
                        details['size'] = 0
                self.dircache[path] = out
            except Error:
                try:
                    info = self.info(path)
                    if info['type'] == 'file':
                        out = [(path, info)]
                except (Error, IndexError):
                    raise FileNotFoundError
        files = self.dircache.get(path, out)
        if not detail:
            return sorted([fn for fn, details in files])
        return [details for fn, details in files]

    def info(self, path, **kwargs):
        """Give details of entry at path

        Returns a single dictionary, with exactly the same information as ``ls``
        would with ``detail=True``.

        Some file systems might not be able to measure the file's size, in
        which case, the returned dict will include ``'size': None``.

        Returns
        -------

        dict with keys: name (full path), size (in bytes), type (file,
        directory, or something else) and other FS-specific keys.

        """
        path = self._strip_protocol(path)
        files = self.ls(path.rsplit('/', 1)[0].lstrip('/'), True)
        try:
            out = [f for f in files if f['name'] == path][0]
        except IndexError:
            raise FileNotFoundError(path)
        return out

    def __call__(self, path, dst_dir=None):
        """Download file from specified directory on the FTP.

        Parameters
        ----------

        path : str
             Name of the file to download


        dst_dir : str
             Path to a local destionation directory


         Examples
        --------

        >>> from aletheia_data import FTPDownloader
        >>> downloader = FTPDownloader(host="ftp.cgd.ucar.edu")
        >>> downloader(path='/archive/aletheia-data/tutorial-data/woa2013v2-O2-thermocline-ann.nc')

        """

        if dst_dir is None:
            dst_dir = conf['cache_dir']

        path = self.info(path)
        filename = Path(path['name']).name
        size = path['size']
        Path(dst_dir).mkdir(parents=True, exist_ok=True)
        local_filename = Path(dst_dir) / filename

        if local_filename.is_file():
            print(f'{local_filename} exists already')

        else:
            with open(local_filename, 'wb') as f:
                cmd = f"RETR {path['name']}"
                # print(
                #     f"""--> Downloading "file={path['name']}" to {local_filename}"""
                # )
                with tqdm(
                    total=size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                    ncols=79,
                    leave=True,
                    disable=not self.progressbar,
                ) as pbar:

                    def callback(data):
                        pbar.update(len(data))
                        f.write(data)

                    self.ftp.retrbinary(cmd, callback, blocksize=self.blocksize)


# Original implementation:
# https://github.com/intake/filesystem_spec/blob/master/fsspec/implementations/ftp.py
def _mlsd2(ftp, path='.'):
    """
    Fall back to using `dir` instead of `mlsd` if not supported.
    This parses a Linux style `ls -l` response to `dir`, but the response may
    be platform dependent.
    Parameters
    ----------
    ftp: ftplib.FTP
    path: str
        Expects to be given path, but defaults to ".".
    """
    lines = []
    minfo = []
    _ = ftp.dir(path, lines.append)
    for line in lines:
        line = line.split()
        this = (
            line[-1],
            {
                'modify': ' '.join(line[5:8]),
                'unix.owner': line[2],
                'unix.group': line[3],
                'unix.mode': line[0],
                'size': line[4],
            },
        )
        if 'd' == this[1]['unix.mode'][0]:
            this[1]['type'] = 'dir'
        else:
            this[1]['type'] = 'file'
        minfo.append(this)
    return minfo
