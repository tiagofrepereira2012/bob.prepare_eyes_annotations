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

import bob
import xbob.db.atnt
import os, sys
import numpy, math
import matplotlib
matplotlib.use('pdf')
# enable LaTeX interpreter
matplotlib.rc('text', usetex=True)
matplotlib.rc('font', family='serif')
matplotlib.rc('lines', linewidth = 4)
from matplotlib import pyplot

from .utils import atnt_database_directory


# To preprocess the AT&T images, we use the TanTriggs algorithm
preprocessor = bob.ip.TanTriggs()

def load_images(db, group = None, purpose = None, database_directory = None, image_extension = '.pgm'):
  """Reads the images for the given group and the given purpose from the given database"""
  # get the file names from the database
  files = db.objects(groups = group, purposes = purpose)
  # iterate through the list of file names
  images = {}
  for k in files:
    # load image and linearize it into a vector
    images[k.id] = bob.io.load(k.make_path(database_directory, image_extension)).astype(numpy.float64)
    # preprocess the images
    images[k.id] = preprocessor(images[k.id])
  return images


# define Gabor wavelet transform class globally since it is reused for all images
gabor_wavelet_transform = bob.ip.GaborWaveletTransform(k_max = 0.25 * math.pi)
# create empty Gabor jet image including Gabor phases in the required size to avoid re-calculation
gabor_jet_image = gabor_wavelet_transform.empty_jet_image(numpy.ndarray((112,92)), True)

def extract_feature(image, graph_machine):
  """Extracts the Gabor graphs from the given image"""

  # perform Gabor wavelet transform on the image
  gabor_wavelet_transform.compute_jets(image, gabor_jet_image)

  # extract the Gabor graphs from the feature image
  gabor_graph = graph_machine(gabor_jet_image)

  # return the extracted graph
  return gabor_graph


# define a certain Gabor jet similarity function that should be used
SIMILARITY_FUNCTION = bob.machine.GaborJetSimilarity(bob.machine.gabor_jet_similarity_type.PHASE_DIFF_PLUS_CANBERRA, gabor_wavelet_transform)

def main():
  """This function will perform Gabor graph comparison test on the AT&T database."""

  # use the bob.db interface to retrieve information about the Database
  atnt_db = xbob.db.atnt.Database()

  # Check the existence of the AT&T database and download it if not
  # Also check if the AT&T database directory is overwritten by the command line
  image_directory = atnt_database_directory(sys.argv[1] if len(sys.argv) > 1 else None)


  #####################################################################
  ### Training

  # for Gabor graphs, no training is required.

  print("Creating Gabor graph machine")
  # create a machine that will produce tight Gabor graphs with inter-node distance (4,4)
  graph_machine = bob.machine.GaborGraphMachine((8,6), (104,86), (4,4))

  #####################################################################
  ### extract Gabor graph features for all model and probe images
  # load all model and probe images
  model_images = load_images(atnt_db, group = 'dev', purpose = 'enrol', database_directory = image_directory)
  probe_images = load_images(atnt_db, group = 'dev', purpose = 'probe', database_directory = image_directory)

  print("Extracting models")
  model_features = {}
  for key, image in model_images.iteritems():
    model_features[key] = extract_feature(image, graph_machine)

  # enroll models from 5 features by simply storing all features
  model_ids = [client.id for client in atnt_db.clients(groups = 'dev')]
  models = dict((model_id, []) for model_id in model_ids) # note: py26 compat.
  # iterate over model features
  for key, image in model_features.iteritems():
    model_id = atnt_db.get_client_id_from_file_id(key)
    # "enroll" model by collecting all model features of this client
    models[model_id].append(model_features[key])

  print("Extracting probes")
  probe_features = {}
  for key, image in probe_images.iteritems():
    probe_features[key] = extract_feature(image, graph_machine)


  #####################################################################
  ### compute scores, we here choose a simple Euclidean distance measure
  positive_scores = []
  negative_scores = []

  print("Computing scores")

  # iterate through models and probes and compute scores
  model_count = 1
  for model_id, model in models.iteritems():
    print("\rModel", model_count, "of", len(models), end='')
    sys.stdout.flush()
    model_count += 1
    for probe_key, probe_feature in probe_features.iteritems():
      # compute local scores for each model gabor jet and each probe jet
      scores = numpy.ndarray((len(model), probe_feature.shape[0]), dtype = numpy.float)
      for model_feature_index in range(len(model)):
        for gabor_jet_index in range(probe_feature.shape[0]):
          scores[model_feature_index, gabor_jet_index] = SIMILARITY_FUNCTION(model[model_feature_index][gabor_jet_index], probe_feature[gabor_jet_index])

      # the final score is computed as the average over all positions, taking the most similar model jet
      score = numpy.average(numpy.max(scores, axis = 0))

      # check if this is a positive score
      if model_id == atnt_db.get_client_id_from_file_id(probe_key):
        positive_scores.append(score)
      else:
        negative_scores.append(score)

  print("\nEvaluation")
  # convert list of scores to numpy arrays
  positives = numpy.array(positive_scores)
  negatives = numpy.array(negative_scores)

  # compute equal error rate
  threshold = bob.measure.eer_threshold(negatives, positives)
  FAR, FRR = bob.measure.farfrr(negatives, positives, threshold)

  print("Result: FAR", FAR, "and FRR", FRR, "at threshold", threshold)

  # plot ROC curve
  bob.measure.plot.roc(negatives, positives)
  pyplot.xlabel("False Rejection Rate (\%)")
  pyplot.ylabel("False Acceptance Rate (\%)")
  pyplot.title("ROC Curve for Gabor phase based AT\&T Verification Experiment")
  pyplot.grid()
  pyplot.axis([0, 100, 0, 100]) #xmin, xmax, ymin, ymax

  # save plot to file
  pyplot.savefig("gabor_graph.pdf")
  print("Saved figure 'gabor_graph.pdf'")

  # show ROC curve.
  # enable it if you like. This will open a window and display the ROC curve
#  pyplot.show()

