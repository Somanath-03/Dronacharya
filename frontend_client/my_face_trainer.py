import cv2
import numpy as np
import os
from PIL import Image

face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
recognizer = cv2.face.LBPHFaceRecognizer_create()

Face_ID = -1
pev_person_name = ""
y_ID = []
x_train = []

Face_Images = os.path.join(os.getcwd(), "Face_Images_copy")

for root, dirs, files in os.walk(Face_Images):
    for file in files:
        if file.endswith("jpeg") or file.endswith("jpg") or file.endswith("png"):
            path = os.path.join(root, file)
            person_name = os.path.basename(root)

            if pev_person_name!= person_name:
                Face_ID += 1
                pev_person_name = person_name


            try:
                img = Image.open(path).convert('L')
                img_array = np.array(img, 'uint8')
                faces = face_cascade.detectMultiScale(img_array, 1.1, 4)

                for (x, y, w, h) in faces:
                    roi = cv2.resize(img_array[y:y+h, x:x+w], (100, 100)) # resize the face to 100x100 pixels
                    x_train.append(roi)
                    y_ID.append(Face_ID)

            except Exception as e:
                print(e)

# Check if all elements in x_train have the same shape
if len(x_train) > 0:
    shape = x_train[0].shape
    if not all(x.shape == shape for x in x_train):
        raise ValueError("Not all elements in x_train have the same shape")

x_train = np.array(x_train)
y_ID = np.array(y_ID)

x_train = x_train.reshape((x_train.shape[0], x_train.shape[1], x_train.shape[2], 1))
x_train = x_train.astype('float32')
x_train /= 255

recognizer.train(x_train, y_ID)
recognizer.save("my-face-trainner3.yml")