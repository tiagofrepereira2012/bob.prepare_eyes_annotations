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
from nose.plugins.skip import SkipTest

import bob.io.base
import bob.io.base.test_utils
import bob.learn.linear
import bob.ip.gabor
import bob.learn.misc

import numpy

import bob.db.atnt

import bob.example.faceverify


regenerate_references = False


class FaceVerifyExampleTest(unittest.TestCase):
  """Performs various tests for the face verification examples."""

  def setUp(self):
    # downloads the database into a temporary directory
    self.m_temp_dir = None
    if os.path.exists('Database'):
      self.m_database_dir = 'Database'
    elif 'ATNT_DATABASE_DIRECTORY' in os.environ:
      self.m_database_dir = os.environ['ATNT_DATABASE_DIRECTORY']
    elif os.path.exists('/idiap/group/biometric/databases/orl'):
      self.m_database_dir = '/idiap/group/biometric/databases/orl'
    else:
      import tempfile
      self.m_temp_dir = tempfile.mkdtemp(prefix='bob_atnt_db_')
      from bob.example.faceverify.utils import atnt_database_directory
      self.m_database_dir = atnt_database_directory(self.m_temp_dir)

  def tearDown(self):
    if self.m_temp_dir:
      import shutil
      shutil.rmtree(self.m_temp_dir)

  def resource(self, f):
    return bob.io.base.test_utils.datafile(f, 'bob.example.faceverify')


  def test00_database(self):
    # test that the database exists
    subdirs = ['s%d'%s for s in range(1,41)]
    files = ['%d.pgm'%s for s in range(1,11)]
    self.assertTrue(set(subdirs).issubset(os.listdir(self.m_database_dir)))
    for d in subdirs:
      self.assertTrue(set(files).issubset(os.listdir(os.path.join(self.m_database_dir,d))))


  def test01_eigenface(self):
    # test the eigenface algorithm
    try:
      from bob.example.faceverify.eigenface import load_images, train, extract_feature, DISTANCE_FUNCTION
    except ImportError as e:
      raise SkipTest("Skipping the tests since importing from bob.example.faceverify.eigenface raised exception '%s'"%e)

    # open database
    atnt_db = bob.db.atnt.Database()
    # test if all training images are loaded
    images = load_images(atnt_db, group = 'world', database_directory = self.m_database_dir)
    self.assertEqual(len(images), 200)

    # test that the training works (for speed reasons, we limit the number of training files)
    pca = train(images)
    if regenerate_references:
      pca.save(bob.io.base.HDF5File(self.resource('pca_projector.hdf5'), 'w'))

    # load PCA reference and check that it is still similar
    pca_ref = bob.learn.linear.Machine(bob.io.base.HDF5File(self.resource('pca_projector.hdf5')))
    self.assertTrue(pca_ref.is_similar_to(pca))

    # check the the projection is the same
    model = extract_feature(images[1], pca)
    probe = extract_feature(images[2], pca)

    if regenerate_references:
      bob.io.base.save(model, self.resource('pca_model.hdf5'))
      bob.io.base.save(probe, self.resource('pca_probe.hdf5'))

    # load model and probe reference
    model_ref = bob.io.base.load(self.resource('pca_model.hdf5'))
    probe_ref = bob.io.base.load(self.resource('pca_probe.hdf5'))
    self.assertTrue(numpy.allclose(model_ref, model))
    self.assertTrue(numpy.allclose(probe_ref, probe))

    # compute score
    score = DISTANCE_FUNCTION(model, probe)
    self.assertAlmostEqual(score, 3498.308154114)


  def test02_gabor_graph(self):
    # test the gabor phase algorithm
    try:
      from bob.example.faceverify.gabor_graph import load_images, extract_feature, SIMILARITY_FUNCTION
    except ImportError as e:
      raise SkipTest("Skipping the tests since importing from bob.example.faceverify.gabor_graph raised exception '%s'"%e)

    # open database
    atnt_db = bob.db.atnt.Database()
    # test if all training images are loaded
    images = load_images(atnt_db, group = 'world', database_directory = self.m_database_dir)
    self.assertEqual(len(images), 200)

    # extract features; for test purposes we wil use smaller features with inter-node-distance 8
    graph_machine = bob.ip.gabor.Graph((0,0), (111,91), (8,8))

    # check the the projection is the same
    model = extract_feature(images[1], graph_machine)
    probe = extract_feature(images[2], graph_machine)

    if regenerate_references:
      bob.ip.gabor.save_jets(model, bob.io.base.HDF5File(self.resource('gabor_model.hdf5'), 'w'))
      bob.ip.gabor.save_jets(probe, bob.io.base.HDF5File(self.resource('gabor_probe.hdf5'), 'w'))

    # load model and probe reference
    model_ref = bob.ip.gabor.load_jets(bob.io.base.HDF5File(self.resource('gabor_model.hdf5')))
    probe_ref = bob.ip.gabor.load_jets(bob.io.base.HDF5File(self.resource('gabor_probe.hdf5')))
    for i in range(len(model_ref)):
      self.assertTrue(numpy.allclose(model_ref[i].jet, model[i].jet))
      self.assertTrue(numpy.allclose(probe_ref[i].jet, probe[i].jet))

    # compute score
    score = numpy.mean([SIMILARITY_FUNCTION.similarity(model[i], probe[i]) for i in range(len(model))])
    self.assertAlmostEqual(score, 0.414937662799)


  def test03_dct_ubm(self):
    # test the UBM/GMM algorithm
    try:
      from bob.example.faceverify.dct_ubm import load_images, extract_feature, train, enroll, stats, NUMBER_OF_GAUSSIANS
    except ImportError as e:
      raise SkipTest("Skipping the tests since importing from bob.example.faceverify.dct_ubm raised exception '%s'"%e)

    # open database
    atnt_db = bob.db.atnt.Database()
    # test if all training images are loaded
    images = load_images(atnt_db, group = 'world', database_directory = self.m_database_dir)
    keys = sorted(images.keys())
    self.assertEqual(len(images), 200)

    # test that the original DCT extraction works
    dct_feature = extract_feature(images[1])
    if regenerate_references:
      bob.io.base.save(dct_feature, self.resource('dct_feature.hdf5'))

    feature_ref = bob.io.base.load(self.resource('dct_feature.hdf5'))
    self.assertTrue(numpy.allclose(feature_ref, dct_feature))

    # extract features for several images
#    features = {i : extract_feature(images[i]) for i in keys[:13]}
    features = {}
    for i in keys[:13]: features[i] = extract_feature(images[i])


    # train the UBM with several features, and a limited number of Gaussians
#    ubm = train({i : features[i] for i in keys[:10]})
    trainset = {}
    for i in keys[:10]: trainset[i] = features[i]
    ubm = train(trainset, number_of_gaussians = 2)
    if regenerate_references:
      ubm.save(bob.io.base.HDF5File(self.resource('dct_ubm.hdf5'), 'w'))

    # load PCA reference and check that it is still similar
    ubm_ref = bob.learn.misc.GMMMachine(bob.io.base.HDF5File(self.resource('dct_ubm.hdf5')))
    self.assertTrue(ubm_ref.is_similar_to(ubm))


    # enroll a model with two features
    enroller = bob.learn.misc.MAP_GMMTrainer()
    enroller.max_iterations = 1
    enroller.set_prior_gmm(ubm)
#    model = enroll({i : features[i] for i in keys[10:12]}, ubm, enroller)
    enrollset = {}
    for i in keys[10:12]: enrollset[i] = features[i]
    model = enroll(enrollset, ubm, enroller)
    if regenerate_references:
      model.save(bob.io.base.HDF5File(self.resource('dct_model.hdf5'), 'w'))

    model_ref = bob.learn.misc.GMMMachine(bob.io.base.HDF5File(self.resource('dct_model.hdf5')))
    self.assertTrue(model_ref.is_similar_to(model))

    # compute probe statistics
    probe = stats(features[keys[12]], ubm)
    if regenerate_references:
      probe.save(bob.io.base.HDF5File(self.resource('dct_probe.hdf5'), 'w'))

    probe_ref = bob.learn.misc.GMMStats(bob.io.base.HDF5File(self.resource('dct_probe.hdf5')))
    self.assertTrue(probe_ref.is_similar_to(probe))

    # compute score
    score = bob.learn.misc.linear_scoring([model], ubm, [probe])[0,0]
    self.assertAlmostEqual(score, 6975.2165874138391)

