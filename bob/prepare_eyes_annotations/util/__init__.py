import os
import numpy

def split_files(files,rank,number_process):
  """This is the call function that you have to overwrite in the derived class.

    This method will split a list into different process
  """
  file_indexes = numpy.array(range(len(files)))
  files = numpy.array(files)

  #Selecting the indexes for each rank
  mod = file_indexes % number_process
  selected_indexes = list(numpy.where(mod==rank)[0])

  files = list(files[selected_indexes])
  if(type(files[0]) == str):
    for i in range(len(files)):
      files[i] = files[i].rstrip("\n")

  return files



def create_dir(directory_name):
  directory = os.path.dirname(directory_name)
  if directory and not os.path.exists(directory): os.makedirs(directory)


def opencv_detect(image):
  """
  Detects a face using OpenCV's cascade detector
  Returns a list of arrays containing (x, y, width, height) for each detected
  face.
  """
  from cv2 import CascadeClassifier
  cc = CascadeClassifier('./bob/prepare_eyes_annotations/util/data/haarcascade_frontalface_alt.xml')

  faces = cc.detectMultiScale( image, 1.3, #scaleFactor (at each time the image is re-scaled)
                               4, #minNeighbors (around candidate to be retained)
                               0, #flags (normally, should be set to zero)
                               (20,20), #(minSize, maxSize) (of detected objects on that scale)
                             )
  if(len(faces) == 0):
    faces = [[0,0,image.shape[0],image.shape[1]]]

  return faces


def get_image_files(input_dir, extension=".jpg"):
  """
  Given a directory, return a list with all files (recursivelly)
  """
  files = os.listdir(input_dir)
  list_files = []
  for f in files:
    element = os.path.join(input_dir,f)
    if(os.path.isdir(element)):
      another_files = get_image_files(element, extension)
      for a in another_files:
        list_files.append(a)
    else:
      if(element.endswith(extension)):
        list_files.append(element)

  return list_files

