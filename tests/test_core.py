from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

import aletheia_data
from aletheia_data import config

registry = {
    'NARR_19930313_0000.nc': '65a23aba0e32dc3dfa56e58fab68ad9028646e57547b246a42a8c16ed9152df4',
    'NOAA_NCDC_ERSST_v3b_SST.nc': '4b87b558e4d2f7ad10555aef84903eaa31572976ee6864cde801d179384ff8cc',
    'air_temperature.nc': 'f6994a1a0509bae59ab7df9395a34c6bb46daeae57d7a89e3d06b593f0becc90',
    'aviso_madt_2015.tar.gz': '3b34c1c2de87aa62221e36c2274b09438b48824f1a5dd4d73a23fd7f11dd3107',
    'co2.nc': '5fa2a230ac8a0637ffa676928530fd77e6392f7833d653b9446491c0104f694e',
    'moc.nc': '7dbd73a7ba29c029e13701d45c3992898f39efa33437e11b7355cd9014f6ba68',
    'rasm.nc': '28498798c1934277268ef806112c001a8281b59c18228a17797df38defad8dfb',
    'sst_indices.csv': '513c0cda976d457d9bc32a61070c07e0d782b8be82b1d4ae8d64e8235c0b6704',
    'thetao_Omon_historical_GISS-E2-1-G_r1i1p1f1_gn_185001-185512.nc': '56998d9ebbd567fd8c41a920639b7bca7191ebfdb215d3237e39591a0d2407c7',
    'woa2013v2-O2-thermocline-ann.nc': 'c9a607c8d8308d6b425ef30d5d4cfb518949c9f6ac59cc58dcd712fa5f7fb081',
}

# @pytest.mark.parametrize(
#     'path, progressbar, blocksize',
#     [
#         ('/archive/aletheia-data/test.sh', False, 100),
#         ('/archive/aletheia-data/tutorial-data/woa2013v2-O2-thermocline-ann.nc', True, 2000),
#     ],
# )
# def test_ftpdownloader(path, progressbar, blocksize):
#     downloader = FTPDownloader(
#         host='ftp.cgd.ucar.edu', progressbar=progressbar, blocksize=blocksize
#     )
#     with TemporaryDirectory() as local_store:
#         name = Path(path).name
#         downloader(path=path, dst_dir=local_store)
#         assert (Path(local_store) / name).is_file()


def test_aletheia_pooch():
    p = aletheia_data.create(
        path=config.conf['cache_dir'],
        base_url='ftp://ftp.cgd.ucar.edu/archive/aletheia-data/tutorial-data/',
        registry=registry,
    )
    assert p.is_available('rasm.nc')
    path = p.fetch('rasm.nc')
    assert Path(path).exists()
