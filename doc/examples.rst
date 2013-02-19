=====================
 Running the examples
=====================

To run the examples, just call the scripts from within the ``bin`` directory, e.g.:

.. code-block:: sh

  $ ./bin/eigenface.py

If you installed the image database in another folder than ``Database``, please give this directory as parameter to the script, e.g.:

.. code-block:: sh

  $ ./bin/eigenface.py <AT&T_DATABASE_DIR>

There are three example scripts:

.. code-block:: sh

  $ ./bin/eigenface.py
  $ ./bin/gabor_phase.py
  $ ./bin/dct_ubm.py

that perform more or less complicated face verification experiments.
Each experiment creates an ROC curve that contains the final verification result of the test.
The generated files will be ``eigenface.png``, ``gabor_phase.png``, and ``dct_ubm.png``.

Since the complexity of the algorithms increase, the expected execution time of them differ a lot.
While the eigenface example should be finished in a couple of seconds, the Gabor phase example could take some minutes, and the UBM/GMM model needs in the order of half an hour to compute.

.. note::

  The example code that is presented here differ slightly from the code in the source files.
  Here, only the concepts of the functions should be clarified, while the source files contain code that is better arranged and computes faster.


The eigenface example
~~~~~~~~~~~~~~~~~~~~~
The eigenface example follows the work-flow that is presented in the original paper *Eigenfaces for Recognition* [TP91]_ by Turk and Pentland.
First, it creates an object to query the database:

.. code-block:: python

  >>> atnt_db = bob.db.atnt.Database()

For training the projection matrix, the training images need to be read:

.. code-block:: python

  >>> training_image_files = atnt_db.files(groups = 'train', ...)
  >>> for filename in training_image_files.values():
  ...   training_image = bob.io.load(filename)

Since the images are already aligned to the eye positions, they can simply be linearized (converted into one long vector) and put into a 2D array
with one sample in each row:

.. code-block:: python

  >>> training_set = numpy.vstack([image.flatten() for image in training_images.values()])

which is used to train a ``bob.machine.LinearMachine``:

.. code-block:: python

  >>> pca_trainer = bob.trainer.SVDPCATrainer()
  >>> pca_machine, eigen_values = pca_trainer.train(training_set)

For some distance functions, the eigenvalues are needed, but in our example we just ignore them.

After training, the model and probe images are loaded, linearized, and projected into the eigenspace using the trained ``pca_machine``:

.. code-block:: python

  >>> model_image_files = atnt_db.files(groups = 'test', purpose = 'enrol', ...)
  >>> for filename in model_image_files.values():
  ...   model_image = bob.io.load(filename)
  ...   model_feature = pca_machine(model_image.flatten())

  >>> probe_image_files = atnt_db.files(groups = 'test', purpose = 'probe', ...)
  >>> for filename in probe_image_files.values():
  ...   probe_image = bob.io.load(filename)
  ...   probe_feature = pca_machine(probe_image.flatten())

To compute the verification result, each model feature is compared to each probe feature by computing the Euclidean distance:

.. code-block:: python

  >>> for model_feature in model_features:
  ...  for probe_feature in probe_features:
  ...    score = bob.math.euclidean_distance(model_feature, probe_feature)

The results are divided into a list of positive scores (model and probe are from the same identity) and a a list of negative scores (identities of model and probe differ).
Using these lists, the ROC curve is plotted:

.. code-block:: python

  >>> bob.measure.plot.roc(negatives, positives)

.. image:: eigenface.png
  :scale: 70 %

and the performance is computed:

.. code-block:: python

  >>> threshold = bob.measure.eer_threshold(negatives, positives)
  >>> FAR, FRR = bob.measure.farfrr(negatives, positives, threshold)

The expected result is: FAR 83.6% and FRR 83.6% at distance threshold 2048.9

.. note::

  Computing eigenfaces with such a low amount of training data is usually not an excellent idea.
  Hence, the performance in this example is extremely poor.


Gabor jet comparisons
~~~~~~~~~~~~~~~~~~~~~
A better face verification example uses Gabor jet features [WFKM97]_ .
In this example we do not define a face graph, but instead we use the Gabor jets at all positions in the image.
To do that, we define:

.. code-block:: python

  >>> graph_machine = bob.machine.GaborGraphMachine((0,0), (111,91), (1,1))

that will create Gabor graphs with node positions from (0,0) to (111,91) with step size (1,1), i.e., a tight Gabor grid graph covering the whole image.

.. note::

  The resolution of the images in the AT&T database is 92x112.
  Of course, there are ways to automatically get the size of the images, but for brevity we hard-coded the resolution of the images.

.. note::

  The Gabor graph extraction does not require a training stage.
  Therefore, in opposition to the eigenface example, the training images are not used in this example.

Now, the Gabor graph features can be extracted from the model and probe images:

.. code-block:: python

  >>> model_image_files = atnt_db.files(groups = 'test', purpose = 'enrol', ...)
  >>> for filename in model_image_files.values():
  ...   model_image = bob.io.load(filename)
  ...   # ... some steps to create the Gabor jet image ...
  ...   graph_machine(jet_image, model_feature)

  >>> probe_image_files = atnt_db.files(groups = 'test', purpose = 'probe', ...)
  >>> for filename in probe_image_files.values():
  ...   probe_image = bob.io.load(filename)
  ...   # ... some steps to create the Gabor jet image ...
  ...   graph_machine(jet_image, probe_feature)

To compare the Gabor graphs, several methods can be applied.
Here, we chose to compute the similarity of two graphs as the average of corresponding Gabor jet similarities.
Again, many choices for the Gabor jet comparison exist, here we take the novel Gabor phase based similarity function [GHW12]_:

.. code-block:: python

  >>> for model_feature in model_features:
  ...  for probe_feature in probe_features:
  ...    score = graph_machine.similarity(model_feature, probe_feature, bob.machine.DisparityCorrectedPhaseDifference())

The evaluation is identical to the evaluation in the eigenface example.
Since this method is much better for suited for small image databases, the resulting verification rates are much better.
The expected ROC curve is:

.. image:: gabor_phase.png
  :scale: 70 %

while the expected verification result is: FAR 22% and FRR 22% at distance threshold 0.1799


The UBM/GMM modeling of DCT Blocks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The last example shows a quite complicated, but very successful algorithm.
The first step is the feature extraction of the training image features and the collection of them in a 2D array.
In this experiment we will use *Discrete Cosine Transform* (DCT) block features [MM09]_:

.. code-block:: python

  >>> training_image_files = atnt_db.files(groups = 'train', ...)
  >>> training_set_list = []
  >>> for filename in training_image_files.values():
  ...   training_image = bob.io.load(filename)
  ...   # ... prepare image blocks ...
  ...   bob.ip.block(training_image, training_image_blocks, ...)
  ...   # ... create DCT extractor ...
  ...   training_dct_blocks = dct_extractor(training_image_blocks)
  ...   training_set_list.append(training_dct_blocks)
  >>> training_set = numpy.vstack(training_set_list)

With these training features, a *universal background model* (UBM) is computed [RQD00]_.
It is a *Gaussian Mixture Model* (GMM) that holds information about the overall distribution of DCT features in facial images.
The UBM model is trained using a bob.trainer.KMeansTrainer to estimate the means of the Gaussians:

.. code-block:: python

  >>> kmeans_machine = bob.machine.KMeansMachine(...)
  >>> kmeans_trainer = bob.trainer.KMeansTrainer()
  >>> kmeans_trainer.train(kmeans, training_set)

Afterward, the UBM is initialized with the results of the k-means training:

.. code-block:: python

  >>> ubm = bob.machine.GMMMachine(...)
  >>> ubm.means = kmeans_machine.means
  >>> [variances, weights] = kmeans_machine.get_variances_and_weights_for_each_cluster(training_set)
  >>> ubm.variances = variances
  >>> ubm.weights = weights

and a bob.trainer.ML_GMMTrainer is used to compute the actual UBM model:

.. code-block:: python

  >>> trainer = bob.trainer.ML_GMMTrainer()
  >>> trainer.train(ubm, training_set)


After UBM training, the next step is the model enrollment.
Here, a separate GMM model is generated by shifting the UBM towards the mean of the model features [MM09]_.
For this purpose, we need to get the model images sorted by identity:

.. code-block:: python

  >>> model_ids = atnt_db.client_ids(groups = 'test')

Now, we load the images for each identity, extract the DCT features and enroll a model for each identity.
For that purpose, a **bob.trainer.MAP_GMMTrainer** is used:

.. code-block:: python

  >>> gmm_trainer = bob.trainer.MAP_GMMTrainer()
  >>> # ... initialize GMM trainer ...
  >>> for model_id in model_ids:
  ...   model_filenames = db.files(groups = 'test', purposes = 'enrol', client_ids = model_id, ...)
  ...   model_feature_set_list = []
  ...   for filename in model_filenames.values():
  ...     # ... load image and extract model image blocks ...
  ...     model_dct_blocks = dct_extractor(model_image_blocks)
  ...     model_feature_set_list.append(model_dct_blocks)
  ...   model_feature_set = numpy.vstack(model_feature_set_list)
  ...   model_gmm = bob.machine.GMMMachine(ubm)
  ...   gmm_trainer.train(model_gmm, model_feature_set)


Also the probe image need some processing.
First, of course, the DCT features are extracted.
Afterward, the statistics for each probe file are generated:

.. code-block:: python

  >>> probe_image_files = atnt_db.files(groups = 'test', purposes = 'probe', ...)
  >>> for filename in probe_image_files.values():
  ...   # ... load image and extract probe image blocks ...
  ...   probe_dct_blocks = dct_extractor(probe_image_blocks)
  ...   probe_gmm_stats = bob.machine.GMMStats()
  ...   gmm_stats.init()
  ...   ubm.acc_statistics(probe_dct_blocks, probe_gmm_stats)

Finally, the scores for the probe files are computed using the function **bob.machine.linear_scoring**:

.. code-block:: python

  >>> for model_gmm in models:
  ...  for probe_gmm_stats in probes:
  ...    score = bob.machine.linear_scoring([model_gmm], ubm, [probe_gmm_stats])[0,0]

Again, the evaluation of the scores is identical to the previous examples.
The expected ROC curve is:

.. image:: dct_ubm.png
  :scale: 70 %

The expected result is: FAR 5% and FRR 5% at distance threshold 7640.9

.. note::

  The resulting ROC curve is not directly comparable to the ones from the other experiments.
  This is due to the fact that here the model files are merged into **one** GMM model **per identity**, whereas before each model file (**five per identity**) generated its own scores.
  Nonetheless, the verification results of the UBM/GMM model are impressive.


.. [TP91]   Matthew Turk and Alex Pentland. Eigenfaces for recognition. Journal of Cognitive Neuroscience, 3(1):71-86, 1991.
.. [WFKM97] \L. Wiskott, J.-M. Fellous, N. Krüger and C.v.d. Malsburg. Face recognition by elastic bunch graph matching. IEEE Transactions on Pattern Analysis and Machine Intelligence, 19:775-779, 1997.
.. [GHW12]  Manuel Günther, Dennis Haufe, Rolf P. Würtz. Face recognition with disparity corrected Gabor phase differences. in preparation
.. [MM09]   Chris McCool and Sébastien Marcel. Parts-based face verification using local frequency bands. In proceedings of IEEE/IAPR international conference on biometrics. 2009.
.. [RQD00]  D.A. Reynolds, T.F. Quatieri, and R.B. Dunn. Speaker verification using adapted gaussian mixture models. Digital Signal Processing, 10(1-3):19–41, 2000.
