.. vim: set fileencoding=utf-8 :
.. Manuel Guenther <manuel.guenther@idiap.ch>
.. Thu Sep  4 11:35:05 CEST 2014

.. image:: https://travis-ci.org/bioidiap/bob.example.faceverify.svg?branch=master
   :target: https://travis-ci.org/bioidiap/bob.example.faceverify
.. image:: https://coveralls.io/repos/bioidiap/bob.example.faceverify/badge.png
   :target: https://coveralls.io/r/bioidiap/bob.example.faceverify
.. image:: http://img.shields.io/github/tag/bioidiap/bob.example.faceverify.png
   :target: https://github.com/bioidiap/bob.example.faceverify
.. image:: http://img.shields.io/pypi/v/bob.example.faceverify.png
   :target: https://pypi.python.org/pypi/bob.example.faceverify
.. image:: http://img.shields.io/pypi/dm/bob.example.faceverify.png
   :target: https://pypi.python.org/pypi/bob.example.faceverify


=======================================
 Exemplary Face Verification Using Bob
=======================================

.. note::
  If you are reading this page through our GitHub portal and not through PyPI, note the development tip of the package may not be stable or become unstable in a matter of moments.

  Go to http://pypi.python.org/pypi/bob.example.faceverify to download the latest stable version of this package.

Overview
--------

This example demonstrates how to use Bob to build three different face verification systems.
It includes examples with three different complexities:

* A simple eigenface based example
* An example using Gabor jets in a grid graph
* An example building an UBM/GMM model on top of DCT blocks.

Requirements
------------

To use this example, you will require the AT&T database.

The AT&T database
.................
The AT&T image database is quite small, but sufficient to show how the face verification methods work.
Still, the results may not be meaningful.
One good thing about the AT&T database is that it is freely available.
You can download it from http://www.cl.cam.ac.uk/research/dtg/attarchive/facedatabase.html.

Download
--------

Finally, to download this package, you can extract the .zip file from the link below, or you open a shell in a directory of your choice and call::

  $ wget https://pypi.python.org/packages/source/b/bob.example.faceverify/bob.example.faceverify-<version>.zip
  $ unzip bob.example.faceverify-<version>.zip
  $ cd bob.example.faceverify-<version>

where <version> should be replaced with a (the current) version of this package, or you can clone our git repository::

  $ git clone https://github.com/bioidiap/bob.example.faceverify.git
  $ cd bob.example.faceverify

Afterwards, please call::

  $ python bootstrap.py
  $ ./bin/buildout

to generate the scripts that, amongst others, will run the face verification algorithms. Please verify your installation by running the test cases. For more details, please refer to the documentation, which you might create and open yourself by::

  $ ./bin/sphinx-build doc sphinx
  $ firefox sphinx/index.html

(or use any other browser of your choice).

If you have questions to or problems with this package, please send a request to bob-devel@googlegroups.com, or file a bug under https://github.com/bioidiap/bob.example.faceverify/issues.

