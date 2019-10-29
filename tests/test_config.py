from pathlib import Path

from aletheia_data import FTPDownloader, config


def test_download():
    f = FTPDownloader()
    f.connect()
    f.download(filename='test.sh')
    f.close()

    assert (Path(config.conf['cache_dir']) / 'test.sh').is_file()
