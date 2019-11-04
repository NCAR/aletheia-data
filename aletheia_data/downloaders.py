"""
Download hooks for Pooch.fetch
"""
import sys

import requests
from requests_ftp.ftp import FTPSession
from tqdm import tqdm

from .utils import infer_protocol_options


class Downloader:
    def __init__(self, progressbar=True, chunk_size=1024, **kwargs):
        self.kwargs = kwargs
        self.progressbar = progressbar
        self.chunk_size = chunk_size

    def __call__(self, url, output_file, pooch):
        """
        Download the given URL over HTTP to the given output file.

        Uses :func:`requests.get`.

        Parameters
        ----------
        url : str
            The URL to the file you want to download.
        output_file : str or file-like object
            Path (and file name) to which the file will be downloaded.
        pooch : :class:`~pooch.Pooch`
            The instance of :class:`~pooch.Pooch` that is calling this method.

        """
        kwargs = self.kwargs.copy()
        kwargs.setdefault('stream', True)
        ispath = not hasattr(output_file, 'write')
        if ispath:
            output_file = open(output_file, 'w+b')
        try:

            options = infer_protocol_options(url)
            # For FTP, we use the requests_ftp library
            if options['protocol'] == 'ftp':
                requests_ = FTPSession()
            else:
                requests_ = requests
            response = requests_.get(url, **kwargs)
            response.raise_for_status()
            content = response.iter_content(chunk_size=self.chunk_size)
            if self.progressbar:
                total = int(response.headers.get('content-length', 0))
                # Need to use ascii characters on Windows because there isn't always
                # full unicode support (see https://github.com/tqdm/tqdm/issues/454)
                use_ascii = bool(sys.platform == 'win32')
                progress = tqdm(
                    total=total, ncols=79, ascii=use_ascii, unit='B', unit_scale=True, leave=True
                )
            for chunk in content:
                if chunk:
                    output_file.write(chunk)
                    output_file.flush()
                    if self.progressbar:
                        # Use the chunk size here because chunk may be much larger if
                        # the data are decompressed by requests after reading (happens
                        # with text files).
                        progress.update(self.chunk_size)
            # Make sure the progress bar gets filled even if the actual number is
            # chunks is smaller than expected. This happens when streaming text files
            # that are compressed by the server when sending (gzip). Binary files don't
            # experience this.
            if self.progressbar:
                progress.reset()
                progress.update(total)
                progress.close()
        finally:
            if ispath:
                output_file.close()
