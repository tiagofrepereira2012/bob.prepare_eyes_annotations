#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Tiago de Freitas Pereira <tiago.pereira@idiap.ch>
# Tue 07 Oct 17:00:00 2014 CEST

"""
Script that detects the face, FROM IMAGES, using openCV face detector and detects the eyes using FLandmark (bob.ip.FLandmark)
"""
import bob
import bob.ip.flandmark
import argparse

from bob.prepare_eyes_annotations.util import *


def main():

  ##########
  # General configuration
  ##########
  parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('input_dir', metavar='DIR', type=str, default="", help="Input image dir (root dir).")
  parser.add_argument('output_dir', metavar='DIR', default="", help="Output dir. The structure of the input dir will be copied.")

  parser.add_argument('-e',dest='extension', default=".jpg", help="File extension in order to filter")

  parser.add_argument('-c','--count',dest='count', action='store_true', help="Count the number of available files in order to use the grid")

  # For SGE grid processing @ Idiap
  parser.add_argument('--grid', dest='grid', action='store_true', default=False, help=argparse.SUPPRESS)
  args = parser.parse_args()

  input_dir  = args.input_dir
  output_dir = args.output_dir
  extension  = args.extension

  image_files = get_image_files(input_dir, extension)

  if(args.count):
    print("Total of files to be processed: {0}".format(len(image_files)))
    exit()

  #Some default parameters
  default_left_eye  = (100,100)
  default_right_eye = (200,100)

  #Default header
  header               = "L R"
  annotation_extension = ".txt"

  if args.grid:
    rank           = int(os.environ['SGE_TASK_ID']) - 1
    number_process = int(os.environ['SGE_TASK_LAST'])
    image_files    = split_files(image_files, rank, number_process)


  for i in image_files:
    img = bob.io.load(i)   
    gray = bob.ip.rgb_to_gray(img)

    #detecting face
    (x, y, width, height) = opencv_detect(gray)[0]

    #detecting landmarks
    flm = bob.ip.flandmark.Flandmark()
    keypoints = flm.locate(gray, y, x, height, width)
    if(keypoints!=None):
      left_eye = (  (keypoints[5][1] + keypoints[1][1]) / 2, (keypoints[5][0] + keypoints[1][0]) / 2)
      right_eye = ((keypoints[2][1] + keypoints[6][1]) / 2, (keypoints[2][0] + keypoints[6][0]) / 2)
    else:
      left_eye  = default_left_eye
      right_eye = default_right_eye

    #generate the content compatible with the annotator
    output_file = i.replace(input_dir, output_dir).replace(extension,annotation_extension)
    create_dir(output_file)
     
    content = header + "\n"
    content += "0 {0} {1} {2} {3}".format(left_eye[0],left_eye[1],right_eye[0],right_eye[1])
    open(output_file, 'w+').write(content)


if __name__ == '__main__':
  main()
