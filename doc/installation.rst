=============
 Installation
=============

.. note::

  To follow these instructions locally you will need a local copy of this package.
  Start by cloning this project with something like:

  .. code-block:: sh

    $ pip install bob.example.faceverify

Installation of the toolkit uses the `buildout <http://www.buildout.org/>`_ build environment.
You don't need to understand its inner workings to use this package.
Here is a recipe to get you started (shell commands are marked with a ``$`` signal):

.. code-block:: sh

  $ python bootstrap.py
  $ ./bin/buildout

These 2 commands should download and install all non-installed dependencies and get you a fully operational test and development environment.

.. note::

  The python shell used in the first line of the previous command set determines the python interpreter that will be used for all scripts developed inside this package.
  Because this package makes use of `Bob <http://www.idiap.ch/software/bob>`_, you must make sure that the ``bootstrap.py`` script is called with the **same** interpreter used to build Bob, or unexpected problems might occur.

  If Bob is installed by the administrator of your system, it is safe to consider it uses the default python interpreter.
  In this case, the above 2 command lines should work as expected.


Use this example with Bob not installed globally
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If your Bob version is not installed globally, you have to edit the *buildout.cfg* file.
Please search for the ``egg-directories`` region and set the value according to your local Bob install directory.
If you are at Idiap, you can simply choose the pre-set directories.


Use Bob at Idiap
~~~~~~~~~~~~~~~~
To get the example running nicely at Idiap, as noted above, ``bootstrap.py`` has to be executed with the correct python version.
For Idiap, this is (currently):

.. code-block:: sh

  $ /idiap/group/torch5spro/nightlies/externals/v3/ubuntu-10.04-x86_64/bin/python bootstrap.py
  $ ./bin/buildout


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

