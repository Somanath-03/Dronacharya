import cv2
import numpy as np
import os
import PIL
from PIL import Image

face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
recognizer = cv2.face.LBPHFaceRecognizer_create()

Face_ID = -1
pev_person_name = ""
y_ID = []
x_train = []

Face_Images = os.path.join(os.getcwd(), "Face_Images_copy")

for root, dirs, files in os.walk(Face_Images):
    print(root,dirs,files)
    for file in files:
        if file.endswith("jpeg") or file.endswith("jpg") or file.endswith("png"):
            path = os.path.join(root, file)
            person_name = os.path.basename(root)
            print(path,person_name)

            if pev_person_name!= person_name:
                Face_ID += 1
                print(pev_person_name)
                pev_person_name = person_name


            try:
                img = Image.open(path).convert('L')
                img_array = np.array(img, 'uint8')
                faces = face_cascade.detectMultiScale(img_array, 1.1, 4)

                for (x, y, w, h) in faces:
                    print(Face_ID)
                    roi = img_array[y:y+h, x:x+w]
                    x_train.append(roi)
                    y_ID.append(Face_ID)

            except PIL.UnidentifiedImageError:
                print(f"Error: Cannot identify image file {path}")

recognizer.train(x_train, np.array(y_ID))
recognizer.save("face-trainner_2.yml")