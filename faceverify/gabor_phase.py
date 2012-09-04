import bob
import xbob.db.atnt
import os, sys
import numpy
from matplotlib import pyplot

# This is the base directory where by default the AT&T images are found. You can
# overwrite this  directory on the command line
global ATNT_IMAGE_DIRECTORY
ATNT_IMAGE_DIRECTORY = "Database"

# The default file name extension of the AT&T images
ATNT_IMAGE_EXTENSION = ".pgm"


def load_images(db, group = None, purpose = None):
  """Reads the images for the given group and the given purpose from the given database"""
  # get the file names from the database
  file_names = db.files(groups = group, purposes = purpose, directory = ATNT_IMAGE_DIRECTORY, extension = ATNT_IMAGE_EXTENSION)
  # iterate through the list of file names
  images = {}
  for key, image_name in file_names.iteritems():
    # load image and linearize it into a vector
    images[key] = bob.io.load(image_name).astype(numpy.float64)
  return images


# define Gabor wavelet transform class globally since it is reused for all images
gabor_wavelet_transform = bob.ip.GaborWaveletTransform()
# create empty Gabor jet image including Gabor phases in the required size
jet_image = gabor_wavelet_transform.empty_jet_image(numpy.ndarray((112,92)), True)

def extract_feature(image, graph_machine):
  """Extracts the Gabor graphs from the given image"""

  # create extraction result in the desired size
  shape = [graph_machine.number_of_nodes]
  # add the shape of one Gabor jet
  shape.extend(jet_image[0,0].shape)
  gabor_graph = numpy.ndarray(shape, dtype = numpy.float64)

  # perform Gabor wavelet transform on the image
  gabor_wavelet_transform.compute_jets(image, jet_image)

  # extract the Gabor graphs from the feature image
  graph_machine(jet_image, gabor_graph)

  # return the extracted graph
  return gabor_graph


def main():
  """This function will perform Gabor graph comparison test on the AT&T database"""

  # use the bob.db interface to retrieve information about the Database
  atnt_db = xbob.db.atnt.Database()

  # check if the AT&T database directory is overwritten by the command line
  global ATNT_IMAGE_DIRECTORY
  if len(sys.argv) > 1:
    ATNT_IMAGE_DIRECTORY = sys.argv[1]

  # check if the database directory exists
  if not os.path.isdir(ATNT_IMAGE_DIRECTORY):
    print "The database directory '" + ATNT_IMAGE_DIRECTORY + "' does not exists!"
    return

  #####################################################################
  ### Training

  # for Gabor graphs, no training is required.

  print "Creating Gabor graph machine"
  # create a machine that will produce tight Gabor graphs with inter-node distance (1,1)
  graph_machine = bob.machine.GaborGraphMachine((0,0), (111,91), (1,1))

  #####################################################################
  ### extract Gabor graph features for all model and probe images
  # load all model and probe images
  model_images = load_images(atnt_db, group = 'dev', purpose = 'enrol')
  probe_images = load_images(atnt_db, group = 'dev', purpose = 'probe')

  print "Extracting models"
  model_features = {}
  for key, image in model_images.iteritems():
    model_features[key] = extract_feature(image, graph_machine)
  print "Extracting probes"
  probe_features = {}
  for key, image in probe_images.iteritems():
    probe_features[key] = extract_feature(image, graph_machine)


  #####################################################################
  ### compute scores, we here choose a simple Euclidean distance measure
  positive_scores = []
  negative_scores = []

  print "Computing scores"
  # define a certain Gabor jet similarity function that should be used
  similarity_function = bob.machine.DisparityCorrectedPhaseDifference()

  # iterate through models and probes and compute scores
  for model_key, model_feature in model_features.iteritems():
    for probe_key, probe_feature in probe_features.iteritems():
      # compute score using the desired Gabor jet similarity function
      score = graph_machine.similarity(model_feature, probe_feature, similarity_function)

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
  pyplot.title("ROC Curve for Gabor phase based AT&T Verification Experiment")
  pyplot.grid()
  pyplot.axis([0, 100, 0, 100]) #xmin, xmax, ymin, ymax

  # save plot to file
  pyplot.savefig("gabor_phase.png")

  # show ROC curve.
  # enable it if you like. This will open a window and display the ROC curve
#  pyplot.show()

