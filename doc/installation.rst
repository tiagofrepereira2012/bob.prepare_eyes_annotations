=============
 Installation
=============

.. note::

  To follow these instructions locally you will need a local copy of this package.
  You can obtain a copy by:

  .. code-block:: sh

    $ wget https://pypi.python.org/packages/source/b/bob.example.faceverify/bob.example.faceverify-<version>.zip
    $ unzip bob.example.faceverify-<version>.zip
    $ cd bob.example.faceverify-<version>

  where ``<version>`` is the latest version of the package that you can find under https://pypi.python.org/pypi/bob.example.faceverify, or by cloning our git repository

  .. code-block:: sh

    $ git clone https://github.com/bioidiap/bob.example.faceverify.git
    $ cd bob.example.faceverify

Installation of this example uses the `buildout <http://www.buildout.org/>`_ build environment.
You don't need to understand its inner workings to use this package.
Here is a recipe to get you started:

.. code-block:: sh

  $ python bootstrap.py
  $ ./bin/buildout

These 2 commands should download and install all non-installed dependencies and get you a fully operational test and development environment.

.. note::

  The python shell used in the first line of the previous command set determines the python interpreter that will be used for all scripts developed inside this package.
  Because this package makes use of `Bob <http://www.idiap.ch/software/bob>`_, you must make sure that the ``bootstrap.py`` script is called with the **same** interpreter used to build Bob, or unexpected problems might occur.

  If Bob is installed by the administrator of your system, it is safe to consider it uses the default python interpreter.
  In this case, the above 2 command lines should work as expected.



Downloading the test database
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The images that are required to run the test are not included in this package, but they are freely downloadable from http://www.cl.cam.ac.uk/research/dtg/attarchive/facedatabase.html

Unpack the database in a directory that fits you.
The easiest solution is to create a subdirectory ``Database`` in this package.
If you decide to put the data somewhere else, please remember the image directory.

.. note ::

  If you are at Idiap, the AT&T database is located at ``/idiap/group/biometric/databases/orl``.
  To ease up the usage of the examples, you can generate a link to the database:

  .. code-block:: sh

    $ ln -s /idiap/group/biometric/databases/orl Database


Verify your installation
~~~~~~~~~~~~~~~~~~~~~~~~
To verify your installation, you might want to run the unit tests that are provided with this package.
For this, the AT&T database is required to be either in the ``Database`` subdirectory of this package (see above), or that the ``ATNT_DATABASE_DIRECTORY`` environment variable points to your database directory.
At Idiap, you might want to use:

.. code-block:: sh

  $ export ATNT_DATABASE_DIRECTORY=/idiap/group/biometric/databases/orl
  $ bin/nosetests -v

