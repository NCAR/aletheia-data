.. image:: https://img.shields.io/circleci/project/github/NCAR/aletheia/master.svg?style=for-the-badge&logo=circleci
    :target: https://circleci.com/gh/NCAR/aletheia/tree/master

.. image:: https://img.shields.io/codecov/c/github/NCAR/aletheia.svg?style=for-the-badge
    :target: https://codecov.io/gh/NCAR/aletheia


.. image:: https://img.shields.io/pypi/v/aletheia.svg?style=for-the-badge
    :target: https://pypi.org/project/aletheia
    :alt: Python Package Index



==============
aletheia
==============



Utility package for accessing test/sample data files.


Installation
------------

aletheia can be installed from PyPI with pip:

.. code-block:: bash

    pip install aletheia


Usage
------

.. code-block:: python

  >>> from aletheia import FTPDownloader
  >>> f = FTPDownloader()
  >>> f.connect()
  >>> f.download(filename='test.sh')
  >>> f.close()
