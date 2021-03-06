import cv2
import numpy as np

# Create window for image display
CASCADE_FN = "haarcascade_frontalface_default.xml"

# The scale used for face recognition.
# It is important as the face recognition algorithm works better on small images
# Also helps with removing faces that are too far away
RESIZE_SCALE = 3
RECTANGE_COLOUR = (255, 0, 0)
THICKNESS = 2

def getFaces(image):
  cascade = cv2.CascadeClassifier(CASCADE_FN)
  img_copy = cv2.resize(image, (image.shape[1]/RESIZE_SCALE,
                                image.shape[0]/RESIZE_SCALE))
  gray = cv2.cvtColor(img_copy, cv2.COLOR_BGR2GRAY)
  gray = cv2.equalizeHist(gray)
  rects = cascade.detectMultiScale(gray)
  resized_rects = []
  for r in rects:
    new_r = map((lambda x: RESIZE_SCALE * x), r)
    resized_rects += [new_r]
  return resized_rects

def drawFaces(image, faces):
  for f in faces:
    x = f[0]
    w = f[1]
    y = f[2]
    h = f[3]
    cv2.rectangle(np.asarray(image), (x,y), (x + w, y + h), RECTANGE_COLOUR,
                  thickness=THICKNESS)

def getAndDrawFaces(image, display=False):
  faces = getFaces(image)
  if display:
    drawFaces(image, faces)
