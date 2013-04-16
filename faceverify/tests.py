#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Author: Manuel Günther <manuel.guenther@idiap.ch>
# Date:   Tue Apr 16 15:56:33 CEST 2013
#
# Copyright (C) 2011-2012 Idiap Research Institute, Martigny, Switzerland
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""A few checks at the faceverify examples.
"""

import os, sys
import unittest

import bob
import numpy

import xbob.db.atnt

import pkg_resources
import faceverify


regenerate_references = False


class FaceVerifyExampleTest(unittest.TestCase):
  """Performs various tests on the BANCA database."""

  def resource(self, f):
    return pkg_resources.resource_filename('faceverify', '../testdata/%s'%f)

  def test01_eigenface(self):
    # test the eigenface algorithm
    from faceverify.eigenface import load_images, train, extract_feature

    # open database
    atnt_db = xbob.db.atnt.Database()
    # test if all training images are loaded
    images = load_images(atnt_db, group = 'world')
    self.assertEqual(len(images), 200)

    # test that the training works (for speed reasons, we limit the number of training files)
    pca = train(images)
    if regenerate_references:
      pca.save(bob.io.HDF5File(self.resource('pca_projector.hdf5'), 'w'))

    # load PCA reference and check that it is still similar
    pca_ref = bob.machine.LinearMachine(bob.io.HDF5File(self.resource('pca_projector.hdf5')))
#TODO: enable for bob version 1.2.0
#    self.assertTrue(pca_ref.is_similar_to(pca))

    # check the the projection is the same
    model = extract_feature(images[1], pca)
    probe = extract_feature(images[2], pca)

    if regenerate_references:
      bob.io.save(model, self.resource('pca_model.hdf5'))
      bob.io.save(probe, self.resource('pca_probe.hdf5'))

    # load model and probe reference
    model_ref = bob.io.load(self.resource('pca_model.hdf5'))
    probe_ref = bob.io.load(self.resource('pca_probe.hdf5'))
    self.assertTrue(numpy.allclose(model_ref, model))
    self.assertTrue(numpy.allclose(probe_ref, probe))

    # compute score
    score = bob.math.euclidean_distance(model, probe)
    self.assertAlmostEqual(score, 3498.308154114)


  def test02_gabor_phase(self):
    # test the gabor phase algorithm
    from faceverify.gabor_phase import load_images, extract_feature

    # open database
    atnt_db = xbob.db.atnt.Database()
    # test if all training images are loaded
    images = load_images(atnt_db, group = 'world')
    self.assertEqual(len(images), 200)

    # extract features; for test purposes we wil use smaller features with inter-node-distance 8
    graph = bob.machine.GaborGraphMachine((0,0), (111,91), (8,8))

    # check the the projection is the same
    model = extract_feature(images[1], graph)
    probe = extract_feature(images[2], graph)

    if regenerate_references:
      bob.io.save(model, self.resource('gabor_model.hdf5'))
      bob.io.save(probe, self.resource('gabor_probe.hdf5'))

    # load model and probe reference
    model_ref = bob.io.load(self.resource('gabor_model.hdf5'))
    probe_ref = bob.io.load(self.resource('gabor_probe.hdf5'))
    self.assertTrue(numpy.allclose(model_ref, model))
    self.assertTrue(numpy.allclose(probe_ref, probe))

    # compute score
    similarity_function = bob.machine.GaborJetSimilarity(bob.machine.gabor_jet_similarity_type.PHASE_DIFF)
    score = graph.similarity(model, probe, similarity_function)
    self.assertAlmostEqual(score, 0.110043015)

  def test03_dct_ubm(self):
    # test the UBM/GMM algorithm
    from faceverify.dct_ubm import load_images, extract_feature, train, enroll, stats, NUMBER_OF_GAUSSIANS

    # open database
    atnt_db = xbob.db.atnt.Database()
    # test if all training images are loaded
    images = load_images(atnt_db, group = 'world')
    keys = sorted(images.keys())
    self.assertEqual(len(images), 200)

    extract_feature(images[1])

    # extract features for several images
    features = {i : extract_feature(images[i]) for i in keys[:13]}

    if regenerate_references:
      bob.io.save(features[1], self.resource('dct_feature.hdf5'))

    feature_ref = bob.io.load(self.resource('dct_feature.hdf5'))
    self.assertTrue(numpy.allclose(feature_ref, features[1]))

    # train the UBM with several features, and a limited numebr of Gaussians
    NUMBER_OF_GAUSSIANS = 2
    ubm = train({i : features[i] for i in keys[:10]})
    if regenerate_references:
      ubm.save(bob.io.HDF5File(self.resource('dct_ubm.hdf5'), 'w'))

    # load PCA reference and check that it is still similar
    ubm_ref = bob.machine.GMMMachine(bob.io.HDF5File(self.resource('dct_ubm.hdf5')))
#TODO: enable for bob version 1.2.0
#    self.assertTrue(ubm_ref.is_similar_to(ubm))


    # enroll a model with two features
    enroller = bob.trainer.MAP_GMMTrainer()
    enroller.max_iterations = 1
    enroller.set_prior_gmm(ubm)
    model = enroll({i : features[i] for i in keys[10:12]}, ubm, enroller)
    if regenerate_references:
      model.save(bob.io.HDF5File(self.resource('dct_model.hdf5'), 'w'))

    model_ref = bob.machine.GMMMachine(bob.io.HDF5File(self.resource('dct_model.hdf5')))
#TODO: enable for bob version 1.2.0
#    self.assertTrue(model_ref.is_similar_to(model))

    # compute probe statistics
    probe = stats(features[keys[12]], ubm)
    if regenerate_references:
      probe.save(bob.io.HDF5File(self.resource('dct_probe.hdf5'), 'w'))

    probe_ref = bob.machine.GMMStats(bob.io.HDF5File(self.resource('dct_probe.hdf5')))
#TODO: enable for bob version 1.2.0
#    self.assertTrue(probe_ref.is_similar_to(probe))

    # compute score
    score = bob.machine.linear_scoring([model], ubm, [probe])[0,0]
    self.assertAlmostEqual(score, 43049.56532399742)

