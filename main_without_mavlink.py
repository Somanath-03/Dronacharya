'''
Program to Detect the Face and Recognise the Person based on the data from face-trainner.yml
  
cam shape -- height - 480, width - 640, c- 3 i.e 3d shape --(480,640,3)
some places its (width,height)
numpy[arry_height , array_width]
 
(100, 640, 3) is black box dimensions
 
black box overlay after face detected -- 256- width , 158- height , 3- c
 
 
# Semicircle parameters
center_x = 60  
center_y = 60  
radius = 35
start_angle = 150
end_angle = 390
thickness = 3  # Thickness of the semicircle in pixels
color = 255 # color in rgb 0-255
'''
 
import cv2 #For Image processing 
import numpy as np #For converting Images to Numerical array 
from PIL import Image,ImageDraw,ImageFont #Pillow lib for handling images
from flask import Flask, render_template, Response, stream_with_context, request

 
 
def drawing_meter(center_x, center_y, radius, start_angle, end_angle,thickness,color,writer=0,name="Unknown"):
    center_y =center_y-15
    # Generate angles and calculate coordinates
    theta = np.linspace(np.radians(start_angle), np.radians(end_angle), num=100)
    x = center_x + radius * np.cos(theta)
    y = center_y + radius * np.sin(theta)
 
    # Fill points in the array (consider edge cases for x and y)
    for i in range(len(x)):
        int_x = int(round(x[i]))
        int_y = int(round(y[i]))
 
    # Iterate within a range for thickness
        for dx in range(-thickness//2, thickness//2 + 1):
            for dy in range(-thickness//2, thickness//2 + 1):
                new_x = int_x + dx
                new_y = int_y + dy
                if 0 <= new_x < 1000 and 0 <= new_y < 1000:
                    bottom_np[new_y, new_x] = color  # Set to white
 
    end_angle = str(end_angle)
 
    if writer == 1:
        cv2.putText(bottom_np,end_angle,(center_x-30,center_y+5),fontFace=1,fontScale=2,color=(255,255,255),thickness=2)
        cv2.putText(bottom_np,name,(center_x-40,center_y+40),fontFace=1,fontScale=1.25,color=(255,255,255),thickness=2)
 
 
def identi_box(name,x,y,w,h,frame):
        face_image = frame[y:y + h, x:x + w]
 
        # Resize the face image to a smaller size for display
        resized_face = cv2.resize(face_image, (128, 128))
 
        # Convert face image to PIL format for text overlay
        face_pil_image = Image.fromarray(resized_face)
 
        # Create a new image to hold the face and text
        combined_image = Image.new('RGB', ((face_pil_image.width * 2)+60, face_pil_image.height))
 
        # Paste the face image onto the combined image
        combined_image.paste(face_pil_image, (0, 0))
 
        # Draw information text below the face
        draw = ImageDraw.Draw(combined_image)
        font = ImageFont.truetype("arial.ttf", 25)
        draw.text((face_pil_image.width + 10, 15), f"Face Detected\n{name.title()}", font=font, fill=(0, 255, 0))
 
        # Convert the combined image back to OpenCV format
        combined_frame = cv2.cvtColor(np.array(combined_image), cv2.COLOR_RGB2BGR)
        frame[:128,324:] = combined_frame
        return frame
 
def initiate_tracking(bbox):
    """
    Initializes the CSRT tracker based on the detected face's bounding box.
    Replace with your preferred tracking approach if needed.
    """
    global tracker,tracking
    tracker = cv2.TrackerCSRT_create()
    tracker.init(frame, bbox)
    tracking = True
    
    
def video_stream():
    while True:
        global frame
        ret, frame = cap.read() # Break video into frames
        if not ret:
            print("camera not connected")
            exit(0)
        else:
            frame = camera_overlay(frame)

            ret,buffer = cv2.imencode('.jpeg',frame)
            frame = buffer.tobytes()
            yield (b' --frame\r\n' b'Content-type: imgae/jpeg\r\n\r\n' + frame +b'\r\n')
 

def camera_overlay(frame):

    frame = cv2.resize(frame, (640, 480))
    gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) #convert Video frame to Greyscale
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.5, minNeighbors=5) #Recog. faces
    for (x, y, w, h) in faces:
        cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
        cv2.circle(img=frame,center=(640//2,480//2),radius=7,color=(0,255,0))
        cv2.circle(img=frame,center=(640//2,480//2),radius=2,color=(0,255,0))
        roi_gray = gray[y:y+h, x:x+w] #Convert Face to greyscale 
        id_, conf = recognizer.predict(roi_gray) #recognize the Face
    
        if conf>=80:
            name = labels[id_] #Get the name from the List using ID number 
    
            frame = identi_box(name,x,y,w,h,frame)
            cv2.circle(img=frame,center=(x+(w//2),y+(h//2)),radius=7,color=(0,0,255))
            cv2.circle(img=frame,center=(x+(w//2),y+(h//2)),radius=2,color=(0,0,255))
    
            # Initiate tracking after specified time
            global tracking,start_time
            if not tracking:
                start_time = cv2.getTickCount() if start_time is None else start_time
                elapsed_time = (cv2.getTickCount() - start_time) / cv2.getTickFrequency()
                if elapsed_time > track_after_seconds:
                    initiate_tracking((x, y, w, h))
    
                # Update tracker and potentially control servo (implementation needed)
            if tracking:
                success, bbox = tracker.update(frame)
                if success:
                    (x, y, w, h) = bbox
                    print(f"tracking person {name} and cordintes{bbox}")
                    cv2.line(frame,(640//2,480//2),(x+(w//2),y+(h//2)),(255,0,0),3)
                    centre = (x+(w//2),y+(h//2))

    
                    if centre != (640//2,480//2):
                        print(f"move {(640//2)-centre[0]}px horizontally and {(480//2)-centre[1]}px vertrically")
        else:
            # Face recognition failed or no face detected
            identi_box("unknown",x,y,w,h,frame)
            tracking = False
            start_time = None

     
    
    
    
        # Create a NumPy array for the overlay and concatinate with frame array 
    global bottom_np
    bottom_np = np.zeros((100,frame.shape[1], 3), dtype=np.uint8)
    
    global z,i
    if z == 0:
        i+=1
    elif z == 1:
        i-=1
    
    if i == 99:
        z = 1
    elif i == 1:
        z = 0

    
    drawing_meter(60,60,35,150,390,3,70)    # speed_bk left most meter
    drawing_meter(60,60,35,150,angle[i],3,255,1,"Airspeed")   # speed writer left most meter
    
    drawing_meter(150,60,35,150,390,3,70)    # rpm_bk 2 - left most meter
    drawing_meter(150,60,35,150,angle[i],3,255,1,"Groundspeed")   # rpm writer 2 - left most meter   
    
    drawing_meter(640-60,60,35,150,390,3,70)    # speed_bk right most meter
    drawing_meter(640-60,60,35,150,angle[i],3,255,1,"Throttle")   # speed writer right most meter
    
    drawing_meter(640-150,60,35,150,390,3,70)    # rpm_bk 2 - right most meter
    drawing_meter(640-150,60,35,150,angle[i],3,255,1,"Altitude")   # rpm writer 2 - right most meter 
    
    overlay_data = np.concatenate([frame[:380],bottom_np])
    #cv.putText(overlay_data,"hello world",(20,440),fontFace=1,fontScale=2,color=(255,255,255),thickness=3)
    
    # put overlay on the frame to give the transperency effect
    frame = cv2.addWeighted(overlay_data,1,frame,1,0)
    # Display the frame
    
    return frame
    
''' cv2.imshow('Preview',frame) #Display the Video
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break'''
 
 
print("starting")
 
labels = ["bhanu", "somu"] 
start_angle = 150
end_angle = 390

i,z = 0,0
angle = [round(z) for z in np.linspace(start_angle, end_angle, num=100)]
 
# Object tracking parameters
track_after_seconds = 3  # Time (in seconds) to wait before initiating tracking
tracking = False  # Flag to indicate if tracking is active
start_time = None

app = Flask('__name__')
 
 
face_cascade = cv2.CascadeClassifier('./haarcascade_frontalface_default.xml')
recognizer = cv2.face.LBPHFaceRecognizer_create()
with open("./my-face-trainner3.yml", "r") as f:
    print("successfully found the file")
recognizer.read("./my-face-trainner3.yml")

 
cap = cv2.VideoCapture(0) #Get video feed from the Camera
 

 
@app.route('/camera')
def camera():
    return render_template('camera.html')

@app.route('/video_feed')
def video_feed():
    return Response(video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port='5000',debug=False)
    finally:
        # When everything done, release the capture
        cap.release()
        cv2.destroyAllWindows()
