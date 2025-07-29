'''
Program to Detect the Face and Recognise the Person based on the data from face-trainner.yml
  
cam shape -- height - 480, width - 640, c- 3 i.e 3d shape --(480,640,3)
some places its (width,height)
numpy[arry_height , array_width]
 
(100, 640, 3) is black box dimensions
 
black box overlay after face detected -- 256- width , 158- height , 3- c

sitl command
sim_vehicle.py -v copter --console --map -w --out 127.0.0.1:14551 --out 127.0.0.1:14552

xterm files - css nd js
https://cdn.jsdelivr.net/npm/xterm@4.19.0/css/xterm.css
https://cdn.jsdelivr.net/npm/xterm@4.19.0/lib/xterm.js


'''

import cv2 #For Image processing 
from pymavlink import mavutil
from flask_socketio import SocketIO    
from flask import Flask, render_template
import base64,time,threading,subprocess


def term():
    global process
    # Start a new bash subprocess
    process = subprocess.Popen(['bash'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

    # Continuously read output from the terminal
    while True:
        output = process.stdout.readline()
        if output:
            socketio.emit('term_out', {'data': output.strip()})
  

                

def param_data():
    """Data from the drone via mavlink comes with the heartbeat this function
    processes data and send it to the frontend in json and from there js will use it 
    for its purpose"""

    while True:
        response_vfr = connection.recv_match(type="VFR_HUD", blocking=True)
        response_gps = connection.recv_match(type="GPS_RAW_INT",blocking = True)
        response_nav = connection.recv_match(type="NAV_CONTROLLER_OUTPUT",blocking = True)
        response_terrain = connection.recv_match(type="TERRAIN_REPORT",blocking = True)
        # response_wav = connection.recv_match(type="MISSION_ITEM",blocking = False)
        # print(response_wav,response_wav.x,response_wav.y)
        if response_vfr:
            data = {'altitude': response_terrain.current_height,
                    'airspeed':response_vfr.airspeed,
                    'heading':response_nav.nav_bearing,
                    'lat':float(response_gps.lat)/1E7,
                    'long':float(response_gps.lon)/1E7,
                    'target_dist' : response_nav.wp_dist

                    }
            # if response_wav:
            #     data['target_lat'] = response_wav[6]
            #     data['target_lon'] = response_wav[7]
        else:
            data = {'error': 0}
        # data = {'altitude': round(100 + 10 * time.time() % 50, 2)}
        socketio.emit('drone_data',{'param':data})
        time.sleep(2)



#video streamming and conversion to send to frontend   
def video_stream():
    while True:
        ret, frame = cap.read() # Break video into frames
        if not ret:
            print("camera not connected")
            exit(0)
        else:
            #preprocess code data
            frame = detect_face(frame)
            ret,buffer = cv2.imencode('.jpeg',frame)
            frame = buffer.tobytes()
            frame= base64.b64encode(frame).decode('utf-8')
            socketio.emit('video_frame', {'frame': frame})
            time.sleep(0.03)


# haarcascade face detector
def detect_face(frame):
    # frame size = 640,480
    frame = cv2.resize(frame, (640, 480))

    #convert Video frame to Greyscale
    gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) 

    #center circle marking 
    cv2.circle(img=frame,center=(640//2,480//2),radius=7,color=(0,255,0))
    cv2.circle(img=frame,center=(640//2,480//2),radius=2,color=(0,255,0))

    #multi face dectector
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.5, minNeighbors=5) #Recog. faces
    for (x, y, w, h) in faces:
        cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
    return frame
    
''' cv2.imshow('Preview',frame) #Display the Video
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break'''

 
 
print("starting")

# Global Values for the system

app = Flask('__name__')
socketio = SocketIO(app)

#haarcascade face classifier 
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
 
#Get video feed from the Camera
cap = cv2.VideoCapture(0) 
print(cap)

#connection object to drone via mavlink
print("Connecting to drone...")
connection = mavutil.mavlink_connection('udpin:127.0.0.1:14551')
connection.wait_heartbeat()
print("Heartbeat from system (system %u component %u)" % (connection.target_system, connection.target_component))


@app.route('/')
def camera():
    return render_template('dashboard.html')

@socketio.on('connect')
def drone_stats():
    print("Client connected!")

    # Start drone data thread
    threading.Thread(target=param_data, daemon=True).start()
    # Start video thread
    threading.Thread(target=video_stream, daemon=True).start()
    # command thread
    threading.Thread(target=term, daemon=True).start()


@socketio.on('term_in')
def handle_command(command):
    if process:
        process.stdin.write(command + '\n')
        process.stdin.flush()

@socketio.on('file')
def script_save(message):
    out = subprocess.run(message,shell=True, text=True, capture_output=True)
    socketio.emit('term_out',out.stdout)



if __name__ == '__main__':
    try:
        socketio.run(app)

    finally:
        # When everything done, release the capture
        cap.release()
        cv2.destroyAllWindows()

