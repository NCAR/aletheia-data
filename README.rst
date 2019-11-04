.. image:: https://img.shields.io/circleci/project/github/NCAR/aletheia-data/master.svg?style=for-the-badge&logo=circleci
    :target: https://circleci.com/gh/NCAR/aletheia-data/tree/master

.. image:: https://img.shields.io/codecov/c/github/NCAR/aletheia-data.svg?style=for-the-badge
    :target: https://codecov.io/gh/NCAR/aletheia-data


.. image:: https://img.shields.io/pypi/v/aletheia-data.svg?style=for-the-badge
    :target: https://pypi.org/project/aletheia-data
    :alt: Python Package Index



==============
aletheia-data
==============


Utility package for accessing data files over HTTP and FTP
from a server and storing them in a local directory. `aletheia-data` is built on top of `Pooch`_.

`Pooch`_ provides the following functionality:

- Download a file only if it’s not in the local storage.
- Check the SHA256 hash to make sure the file is not corrupted or needs updating.
- If the hash is different from the registry, Pooch will download a new version of the file.
- If the hash still doesn’t match, Pooch will raise an exception warning of possible data corruption.


By default, `pooch` has support for downloading files over HTTP only. `aletheia-data` extends `pooch` by adding
support for downloading files over FTP.

See pooch's documentation_ for more information.

.. _documentation: https://www.fatiando.org/pooch/latest/index.html
.. _pooch: https://github.com/fatiando/pooch


Installation
------------

aletheia-data can be installed from PyPI with pip:

.. code-block:: bash

    pip install aletheia-data


Usage
------

.. code-block:: python

    Create an `AletheiaPooch` for a release (v0.1):

    >>> from aletheia_data import create
    >>> p = create(path="/Users/abanihi/.aletheia/data",
    ...              base_url="ftp://ftp.cgd.ucar.edu/archive/aletheia-data/tutorial-data/",
    ...              version="v0.1",
    ...              registry={'rasm.nc': '28498798c1934277268ef806112c001a8281b59c18228a17797df38defad8dfb'})
    >>> print(p.path.parts)  # The path is a pathlib.Path
    ('/', 'Users', 'abanihi', '.aletheia', 'data', 'v0.1')
    >>> print(p.base_url)
    ftp://ftp.cgd.ucar.edu/archive/aletheia-data/tutorial-data/
    >>> print(p.registry)
    {'rasm.nc': '28498798c1934277268ef806112c001a8281b59c18228a17797df38defad8dfb'}

    Fetch the file from remote server and persist a copy in the local storage:

    >>> path = p.fetch("rasm.nc")
    Downloading data file 'rasm.nc' from remote data store
    'ftp://ftp.cgd.ucar.edu/archive/aletheia-data/tutorial-data/rasm.nc'
    to '/Users/abanihi/.aletheia/data/v0.1'.
    100%|█████████████████████████████████████| 17.2M/17.2M [00:00<00:00, 23.2GB/s]

    >>> print(path)
    '/Users/abanihi/.aletheia/data/v0.1/rasm.nc'

    Open the file with xarray

    >>> import xarray as xr
    >>> ds = xr.open(path)
    >>> ds
    <xarray.Dataset>
    Dimensions:  (time: 36, x: 275, y: 205)
    Coordinates:
    * time     (time) object 1980-09-16 12:00:00 ... 1983-08-17 00:00:00
        xc       (y, x) float64 ...
        yc       (y, x) float64 ...
    Dimensions without coordinates: x, y
    Data variables:
        Tair     (time, y, x) float64 ...
    Attributes:
        title:                     /workspace/jhamman/processed/R1002RBRxaaa01a/l...
        institution:               U.W.
        source:                    RACM R1002RBRxaaa01a
        output_frequency:          daily
        output_mode:               averaged
        convention:                CF-1.4
        references:                Based on the initial model of Liang et al., 19...
        comment:                   Output from the Variable Infiltration Capacity...
        nco_openmp_thread_number:  1
        NCO:                       "4.6.0"
        history:                   Tue Dec 27 14:15:22 2016: ncatted -a dimension...
