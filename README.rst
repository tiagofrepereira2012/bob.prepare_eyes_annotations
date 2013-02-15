Face verification using Bob
===========================

.. note::
  If you are reading this page through our GitHub portal and not through PyPI, note the development tip of the package may not be stable or become unstable in a matter of moments.

  Go to http://pypi.python.org/pypi/bob.example.faceverify to download the latest stable version of this package.

This example demonstrates how to use Bob to build different face verification systems.
It includes examples with three different complexities:

* A simple eigenface based example
* An example using Gabor jets and a Gabor-phase based similarity function
* An example building an UBM/GMM model on top of DCT blocks.

To use this example, you will require Bob and the AT&T database.
If you do not have a Bob version yet, you can get it from http://www.idiap.ch/software/bob.

The AT&T image database is quite small, but sufficient to show how the face verification methods work.
Still, the results may not be meaningful.
One good thing about the AT&T database is that it is freely available.
You can download it from http://www.cl.cam.ac.uk/research/dtg/attarchive/facedatabase.html.


Finally, to download this package, please open a shell, go to a directory of your choice and call::

  $ pip install bob.example.faceverify

To generate the Documentation, please further go into the "doc" directory and call::

  $ make html
  $ firefox html/index.html

(or use any other browser of your choice).
After you did this, please read the documentation and try to execute the examples.
