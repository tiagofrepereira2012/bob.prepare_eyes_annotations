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

# This is the base directory where by default the AT&T images are found. You can
# overwrite this  directory on the command line
global ATNT_IMAGE_DIRECTORY
ATNT_IMAGE_DIRECTORY = os.environ['ATNT_DATABASE_DIRECTORY'] if 'ATNT_DATABASE_DIRECTORY' in os.environ else "Database"

# The default file name extension of the AT&T images
ATNT_IMAGE_EXTENSION = ".pgm"


def load_images(db, group = None, purpose = None):
  """Reads the images for the given group and the given purpose from the given database"""
  # get the file names from the database
  files = db.objects(groups = group, purposes = purpose)
  # iterate through the list of file names
  images = {}
  for k in files:
    # load image and linearize it into a vector
    images[k.id] = bob.io.load(k.make_path(ATNT_IMAGE_DIRECTORY, ATNT_IMAGE_EXTENSION)).astype(numpy.float64)
  return images


# The number of eigenfaces that should be kept
KEPT_EIGENFACES = 5

def train(training_images):
  """Trains the PCA module with the given list of training images"""
  # perform training using a SVD PCA trainer
  pca_trainer = bob.trainer.SVDPCATrainer()

  # create array set used for training
  # iterate through the training examples and linearize the images
  training_set = numpy.vstack([image.flatten() for image in training_images.values()])

  # training the SVD PCA returns a machine that can be used for projection
  pca_machine, eigen_values = pca_trainer.train(training_set)

  # limit the number of kept eigenfaces
  pca_machine.resize(pca_machine.shape[0], KEPT_EIGENFACES)

  return pca_machine


def extract_feature(image, pca_machine):
  """Projects the given list of images to the PCA subspace and returns the results"""
  # create projection result in the desired size
  projected_feature = numpy.ndarray((KEPT_EIGENFACES,), dtype = numpy.float64)

  # project the data after linearizing them
  pca_machine(image.flatten(), projected_feature)

  # return the projected data
  return projected_feature


def main():
  """This function will perform an eigenface test on the AT&T database"""

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
  ### Training

  # load all training images
  training_images = load_images(atnt_db, group = 'world')

  print "Training PCA machine"
  pca_machine = train(training_images)

  #####################################################################
  ### extract eigenface features of model and probe images

  # load model and probe images
  model_images = load_images(atnt_db, group = 'dev', purpose = 'enrol')
  probe_images = load_images(atnt_db, group = 'dev', purpose = 'probe')

  print "Extracting models"
  model_features = {}
  for key, image in model_images.iteritems():
    model_features[key] = extract_feature(image, pca_machine)
  print "Extracting probes"
  probe_features = {}
  for key, image in probe_images.iteritems():
    probe_features[key] = extract_feature(image, pca_machine)


  #####################################################################
  ### compute scores, we here choose a simple Euclidean distance measure
  positive_scores = []
  negative_scores = []

  print "Computing scores"
  distance_function = bob.math.euclidean_distance

  # iterate through models and probes and compute scores
  for model_key, model_feature in model_features.iteritems():
    for probe_key, probe_feature in probe_features.iteritems():
      # compute score
      score = distance_function(model_feature, probe_feature)

      # check if this is a positive score
      if atnt_db.get_client_id_from_file_id(model_key) == atnt_db.get_client_id_from_file_id(probe_key):
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
  pyplot.title("ROC Curve for Eigenface based AT&T Verification Experiment")
  pyplot.grid()
  pyplot.axis([0, 100, 0, 100]) #xmin, xmax, ymin, ymax

  # save plot to file
  pyplot.savefig("eigenface.png")
  print "Saved figure 'eigenface.png'"

  # show ROC curve.
  # enable it if you like. This will open a window and display the ROC curve
#  pyplot.show()

