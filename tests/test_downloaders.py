from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from aletheia_data import FTPDownloader, config


@pytest.mark.parametrize(
    'path, progressbar, blocksize',
    [
        ('/archive/aletheia-data/test.sh', False, 100),
        ('/archive/aletheia-data/tutorial-data/woa2013v2-O2-thermocline-ann.nc', True, 2000),
    ],
)
def test_ftpdownloader(path, progressbar, blocksize):
    downloader = FTPDownloader(
        host='ftp.cgd.ucar.edu', progressbar=progressbar, blocksize=blocksize
    )
    with TemporaryDirectory() as local_store:
        name = Path(path).name
        downloader(path=path, dst_dir=local_store)
        assert (Path(local_store) / name).is_file()
