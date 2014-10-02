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

from __future__ import print_function

# import required bob modules
import bob.db.atnt
import bob.io.base
import bob.io.image
import bob.learn.linear
import bob.measure

import os, sys
import numpy, scipy.spatial
import matplotlib
matplotlib.use('pdf')
# enable LaTeX interpreter
matplotlib.rc('text', usetex=True)
matplotlib.rc('font', family='serif')
matplotlib.rc('lines', linewidth = 4)
from matplotlib import pyplot

from .utils import atnt_database_directory


def load_images(db, group = None, purpose = None, database_directory = None, image_extension = '.pgm'):
  """Reads the images for the given group and the given purpose from the given database"""
  # get the file names from the database
  files = db.objects(groups = group, purposes = purpose)
  # iterate through the list of file names
  images = {}
  for k in files:
    # load image
    images[k.id] = bob.io.base.load(k.make_path(database_directory, image_extension)).astype(numpy.float64)
  return images


# The number of eigenfaces that should be kept
KEPT_EIGENFACES = 5

def train(training_images):
  """Trains the PCA module with the given list of training images"""
  # perform training using a PCA trainer
  pca_trainer = bob.learn.linear.PCATrainer()

  # create array set used for training
  # iterate through the training examples and linearize the images
  training_set = numpy.vstack([image.flatten() for image in training_images.values()])

  # training the PCA returns a machine that can be used for projection
  pca_machine, eigen_values = pca_trainer.train(training_set)

  # limit the number of kept eigenfaces
  pca_machine.resize(pca_machine.shape[0], KEPT_EIGENFACES)

  return pca_machine


def extract_feature(image, pca_machine):
  """Projects the given list of images to the PCA subspace and returns the results"""
  # project and return the data after linearizing them
  return pca_machine(image.flatten())


DISTANCE_FUNCTION = scipy.spatial.distance.euclidean

def main():
  """This function will perform an eigenface test on the AT&T database"""

  # use the bob.db interface to retrieve information about the Database
  atnt_db = bob.db.atnt.Database()

  # Check the existence of the AT&T database and download it if not
  # Also check if the AT&T database directory is overwritten by the command line
  image_directory = atnt_database_directory(sys.argv[1] if len(sys.argv) > 1 else None)


  #####################################################################
  ### Training

  # load all training images
  training_images = load_images(atnt_db, group = 'world', database_directory = image_directory)

  print("Training PCA machine")
  pca_machine = train(training_images)

  #####################################################################
  ### extract eigenface features of model and probe images

  # load model and probe images
  model_images = load_images(atnt_db, group = 'dev', purpose = 'enrol', database_directory = image_directory)
  probe_images = load_images(atnt_db, group = 'dev', purpose = 'probe', database_directory = image_directory)

  print("Extracting models")
  model_features = {}
  for key, image in model_images.items():
    model_features[key] = extract_feature(image, pca_machine)

  # enroll models from 5 features by simply storing all features
  model_ids = [client.id for client in atnt_db.clients(groups = 'dev')]
  models = dict((model_id, []) for model_id in model_ids) # note: py26 compat.
  # iterate over model features
  for file_id, image in model_features.items():
    model_id = atnt_db.get_client_id_from_file_id(file_id)
    # "enroll" model by collecting all model features of this client
    models[model_id].append(model_features[file_id])

  print("Extracting probes")
  probe_features = {}
  for key, image in probe_images.items():
    probe_features[key] = extract_feature(image, pca_machine)


  #####################################################################
  ### compute scores, we here choose a simple Euclidean distance measure
  positive_scores = []
  negative_scores = []

  print("Computing scores")

  # iterate through models and probes and compute scores
  for model_id, model in models.items():
    for probe_key, probe_feature in probe_features.items():
      # compute scores for all model features
      scores = [- DISTANCE_FUNCTION(model_feature, probe_feature) for model_feature in model]
      # the final score is the average distance
      # :: Note for the testers :: Try out other strategies!
      score = numpy.sum(scores)

      # check if this is a positive score
      if model_id == atnt_db.get_client_id_from_file_id(probe_key):
        positive_scores.append(score)
      else:
        negative_scores.append(score)

  print("Evaluation")
  # convert list of scores to numpy arrays
  positives = numpy.array(positive_scores)
  negatives = numpy.array(negative_scores)

  # compute equal error rate
  threshold = bob.measure.eer_threshold(negatives, positives)
  FAR, FRR = bob.measure.farfrr(negatives, positives, threshold)

  print("Result: FAR", FAR, "and FRR", FRR, "at threshold", threshold)

  # plot ROC curve
  bob.measure.plot.roc(negatives, positives, CAR=True)
  pyplot.xlabel("False Acceptance Rate (\%)")
  pyplot.ylabel("Correct Acceptance Rate (\%)")
  pyplot.title("ROC Curve for Eigenface based AT\&T Verification Experiment")
  pyplot.grid()
  pyplot.axis([0.1, 100, 0, 100]) #xmin, xmax, ymin, ymax

  # save plot to file
  pyplot.savefig("eigenface.pdf")
  print("Saved figure 'eigenface.pdf'")

  # show ROC curve.
  # enable it if you like. This will open a window and display the ROC curve
#  pyplot.show()

