#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# @author: Manuel Guenther <Manuel.Guenther@idiap.ch>
# @date: Wed May  1 11:33:00 CEST 2013
#
# Copyright (C) 2011-2013 Idiap Research Institute, Martigny, Switzerland
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import bob
import xbob.db.atnt
import os, sys
import numpy
from matplotlib import pyplot

# setup the logging system
import logging
formatter = logging.Formatter("%(name)s@%(asctime)s -- %(levelname)s: %(message)s")
logger = logging.getLogger("bob")
for handler in logger.handlers:
  handler.setFormatter(formatter)
logger.setLevel(logging.INFO)


# This is the base directory where by default the AT&T images are found. You can
# overwrite this  directory on the command line
global ATNT_IMAGE_DIRECTORY
ATNT_IMAGE_DIRECTORY = os.environ['ATNT_DATABASE_DIRECTORY'] if 'ATNT_DATABASE_DIRECTORY' in os.environ else "Database"

# The default file name extension of the AT&T images
ATNT_IMAGE_EXTENSION = ".pgm"


def load_images(db, group = None, purpose = None, client_id = None):
  """Reads the images for the given group and the given client id from the given database"""
  # get the file names from the database
  files = db.objects(groups = group, purposes = purpose, model_ids = client_id)
  # iterate through the list of file names
  images = {}
  for k in files:
    # load image and linearize it into a vector
    images[k.id] = bob.io.load(k.make_path(ATNT_IMAGE_DIRECTORY, ATNT_IMAGE_EXTENSION)).astype(numpy.float64)
  return images


# Parameters of the DCT extraction
DCT_BLOCK_SIZE = 12
DCT_BLOCK_OVERLAP = 11
NUMBER_OF_DCT_COMPONENTS = 45

# create a DCT block extractor model
dct_extractor = bob.ip.DCTFeatures(DCT_BLOCK_SIZE, DCT_BLOCK_SIZE, DCT_BLOCK_OVERLAP, DCT_BLOCK_OVERLAP, NUMBER_OF_DCT_COMPONENTS)

def extract_feature(image):
  """Extracts the DCT features for the given image"""

  # extract DCT blocks
  return dct_extractor(image)



# Parameters of the UBM/GMM module training
NUMBER_OF_GAUSSIANS = 100

def train(training_features, number_of_gaussians = NUMBER_OF_GAUSSIANS):
  """Trains the UBM/GMM module with the given set of training DCT features"""

  # create array set used for training
  training_set = numpy.vstack([v for v in training_features.values()])

  input_size = training_set.shape[1]
  # create the KMeans and UBM machine
  kmeans = bob.machine.KMeansMachine(number_of_gaussians, input_size)
  ubm = bob.machine.GMMMachine(number_of_gaussians, input_size)

  # create the KMeansTrainer
  kmeans_trainer = bob.trainer.KMeansTrainer()

  # train using the KMeansTrainer
  kmeans_trainer.train(kmeans, training_set)

  [variances, weights] = kmeans.get_variances_and_weights_for_each_cluster(training_set)
  means = kmeans.means

  # initialize the GMM
  ubm.means = means
  ubm.variances = variances
  ubm.weights = weights

  # train the GMM
  trainer = bob.trainer.ML_GMMTrainer()
  trainer.train(ubm, training_set)

  return ubm


def enroll(model_features, ubm, gmm_trainer):
  """Enrolls the GMM model for the given model features (which should stem from the same identity)"""
  # create array set used for enrolling
  enroll_set = numpy.vstack(model_features.values())
  # create a GMM from the UBM
  gmm = bob.machine.GMMMachine(ubm)

  # train the GMM
  gmm_trainer.train(gmm, enroll_set)

  # return the resulting gmm
  return gmm


def stats(probe_feature, ubm):
  """Computes the UBM Statistics for the given feature vector"""
  # compute the UBM stats for the given probe feature
  probe_feature = numpy.vstack([probe_feature])

  # Accumulate statistics
  gmm_stats = bob.machine.GMMStats(ubm.dim_c, ubm.dim_d)
  gmm_stats.init()
  ubm.acc_statistics(probe_feature, gmm_stats)

  return gmm_stats


def main():
  """This function will perform an a DCT block extraction and a UBM/GMM modeling test on the AT&T database"""

  # use the bob.db interface to retrieve information about the Database
  atnt_db = xbob.db.atnt.Database()

  # check if the AT&T database directory is overwritten by the command line
  global ATNT_IMAGE_DIRECTORY
  if len(sys.argv) > 1:
    if sys.argv[1].lower() in ('-h', '--help'):
      print "Usage:", sys.argv[0], "[DatabaseDirectory]"
      print "  NOTE: DatabaseDirectory defaults to the './Database' or to the environment variable 'ATNT_DATABASE_DIRECTORY', if set"
      return
    ATNT_IMAGE_DIRECTORY = sys.argv[1]

  # check if the database directory exists
  if not os.path.isdir(ATNT_IMAGE_DIRECTORY):
    print "The database directory '" + ATNT_IMAGE_DIRECTORY + "' does not exists!"
    return

  #####################################################################
  ### UBM Training
  # load all training images
  training_images = load_images(atnt_db, group = 'world')

  print "Extracting training features"
  training_features = {}
  for key, image in training_images.iteritems():
    training_features[key] = extract_feature(image)

  print "Training UBM model"
  ubm = train(training_features)

  #####################################################################
  ### GMM model enrollment
  print "Enrolling GMM models"
  gmm_trainer = bob.trainer.MAP_GMMTrainer()
  gmm_trainer.max_iterations = 1
  gmm_trainer.set_prior_gmm(ubm)

  # enroll a GMM model for each model identity (i.e., each client)
  model_ids = [client.id for client in atnt_db.clients(groups = 'dev')]
  models = {}
  for model_id in model_ids:
    # load images for the current model id
    model_images = load_images(atnt_db, group = 'dev', purpose = 'enrol', client_id = model_id)
    models_for_current_id = {}
    # extract model features
    for key, image in model_images.iteritems():
      models_for_current_id[key] = extract_feature(image)
    # enroll model for the current identity from these features
    model = enroll(models_for_current_id, ubm, gmm_trainer)
    models[model_id] = model

  #####################################################################
  ### probe stats

  print "Computing probe statistics"
  probe_images = load_images(atnt_db, group = 'dev', purpose = 'probe')
  probes = {}
  for key, image in probe_images.iteritems():
    # extract probe features
    probe_feature = extract_feature(image)
    # compute GMM statistics
    probes[key] = stats(probe_feature, ubm)

  #####################################################################
  ### compute scores, we here choose a simple Euclidean distance measure
  positive_scores = []
  negative_scores = []

  print "Computing scores"
  distance_function = bob.machine.linear_scoring

  # iterate through models and probes and compute scores
  for model_id, model_gmm in models.iteritems():
    for probe_key, probe_stats in probes.iteritems():
      # compute score
      score = distance_function([model_gmm], ubm, [probe_stats])[0,0]

      # check if this is a positive score
      if model_id == atnt_db.get_client_id_from_file_id(probe_key):
        positive_scores.append(score)
      else:
        negative_scores.append(score)

  print "Evaluation"
  # convert list of scores to numpy arrays
  positives = numpy.array(positive_scores)
  negatives = numpy.array(negative_scores)

  # compute equal error rate
  threshold = bob.measure.eer_threshold(negatives, positives)
  FAR, FRR = bob.measure.farfrr(negatives, positives, threshold)

  print "Result: FAR", FAR, "and FRR", FRR, "at threshold", threshold

  # plot ROC curve
  bob.measure.plot.roc(negatives, positives)
  pyplot.xlabel("False Rejection Rate (%)")
  pyplot.ylabel("False Acceptance Rate (%)")
  pyplot.title("ROC Curve for UBM/GMM based AT&T Verification Experiment")
  pyplot.grid()
  pyplot.axis([0, 100, 0, 100]) #xmin, xmax, ymin, ymax

  # save plot to file
  pyplot.savefig("dct_ubm.png")
  print "Saved figure 'dct_ubm.png'"

  # show ROC curve.
  # enable it if you like. This will open a window and display the ROC curve
#  pyplot.show()

