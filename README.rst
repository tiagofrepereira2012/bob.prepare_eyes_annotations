Face verification using Bob
===========================

This example demonstrates how to use Bob to build different face verification
systems. It includes examples with three different complexities:

* A simple eigenface based example
* An example using Gabor jets and a Gabor-phase based similarity function
* An example building an UBM/GMM model on top of DCT blocks.

To use this example, you will require Bob and the AT&T database. If you do not
have a Bob version yet, you can get it from `here <http://www.idiap.ch/software/bob/>`_.

If you already have installed Bob, please make sure that you have at least
the version 1.0.5, otherwise the example won't work.

The AT&T image database is quite small, but sufficient to show how the face
verification methods work. Still, the results may not be meaningful. One good
thing about the AT&T database is that it is freely available. You can download
it from `here <http://www.cl.cam.ac.uk/research/dtg/attarchive/facedatabase.html>`_.


Finally, to download this package, please open a shell, go to a directory of
your choice and call::

  $ pip install bob.example.faceverify

To generate the Documentation, please further go into the "doc" directory and
call::

  $ make html
  $ firefox html/index.html

(or use any other browser of your choice). After you did this, please read the
documentation and try to execute the examples.
