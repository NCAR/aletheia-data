from ftplib import FTP
from pathlib import Path

import attr

from .config import conf


@attr.s
class FTPDownloader(object):
    ftp = attr.ib(default=None)
    host = attr.ib(default=None)
    current_dir = attr.ib(default=None)

    def connect(self, host='ftp.cgd.ucar.edu'):
        """Connect and login into the ftp server.

        Parameters
        ----------
        host : str
          Address of the FTP server

        Examples
        --------

        >>> from aletheia_data import FTPDownloader
        >>> c = FTPDownloader()
        >>> c.connect()

        After connecting, the `ftp` and `host` attributes are updated:

        >>> c.ftp
        <ftplib.FTP at 0x1087f9d68>
        >>> c.host
        'ftp.cgd.ucar.edu'

        """
        ftp = FTP()
        ftp.connect(host)
        ftp.login()
        self.host = host
        self.ftp = ftp

    def download(self, filename, src_dir='archive/aletheia-data/', dst_dir=None):
        """Download file from specified directory on the FTP.

        Parameters
        ----------

        filename : str
             Name of the file to download

        src_dir : str
             Path to directory where files are located

        dst_dir : str
             Path to a local destionation directory


         Examples
        --------

        >>> from aletheia_data import FTPDownloader
        >>> c = FTPDownloader()
        >>> c.connect()
        >>> c.download(filename="test.sh", src_dir="archive/aletheia-data/")


        """
        if src_dir == self.current_dir:
            pass
        else:
            self.current_dir = src_dir
            self.ftp.cwd(src_dir)

        if dst_dir is None:
            dst_dir = conf['cache_dir']

        filelist = self.ftp.nlst()
        if filename in filelist:
            Path(dst_dir).mkdir(parents=True, exist_ok=True)
            local_filename = Path(dst_dir) / filename
            if local_filename.is_file():
                print(f'{local_filename} exists already')

            else:
                with open(local_filename, 'wb') as f:
                    cmd = f'RETR {filename}'
                    print(
                        f"--> Downloading 'file={filename}' from '{self.host}/{src_dir}' to {dst_dir}"
                    )
                    self.ftp.retrbinary(cmd, f.write)

        else:
            print(f"--> Couldn't find 'file={filename}'! Skipping.")
