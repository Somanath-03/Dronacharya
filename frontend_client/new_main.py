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
import os
from huggingface_hub import InferenceClient


process = None  # initialized global process reference


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

    last_emit = 0
    cache = {}
    last_lat = None
    last_lon = None
    while True:
        msg = connection.recv_match(blocking=False)
        if msg:
            mtype = msg.get_type()
            cache[mtype] = msg
        now = time.time()
        if now - last_emit >= 0.2:
            vfr = cache.get('VFR_HUD')
            att = cache.get('ATTITUDE')
            gps = cache.get('GPS_RAW_INT')
            gpos = cache.get('GLOBAL_POSITION_INT')
            nav = cache.get('NAV_CONTROLLER_OUTPUT')
            terr = cache.get('TERRAIN_REPORT')
            sys_s = cache.get('SYS_STATUS')
            batt = cache.get('BATTERY_STATUS')
            rpm = cache.get('RPM')
            esc_1_4 = cache.get('ESC_TELEMETRY_1_TO_4')  # provides arrays for first 4 ESCs
            esc_5_8 = cache.get('ESC_TELEMETRY_5_TO_8')  # provides arrays for next 4 (in case of octo)
            servo_raw = cache.get('SERVO_OUTPUT_RAW')    # fallback raw PWM outputs
            hb = cache.get('HEARTBEAT')
            if vfr or att or gps or gpos:
                groundspeed = getattr(vfr,'groundspeed',None)
                climb = getattr(vfr,'climb',None)
                voltage = (sys_s.voltage_battery / 1000.0) if (sys_s and sys_s.voltage_battery != 65535) else None
                battery_remaining = sys_s.battery_remaining if (sys_s and sys_s.battery_remaining != 255) else None
                mode = mavutil.mode_string_v10(hb) if hb else None
                pack_voltage = None
                current_a = None
                if batt:
                    try:
                        cells = [v for v in batt.voltages if v != 65535]
                        if cells:
                            pack_voltage = sum(cells)/1000.0
                        if getattr(batt,'current_battery',-1) != -1:
                            current_a = batt.current_battery/100.0
                    except Exception:
                        pass
                rpm1 = getattr(rpm,'rpm1',None) if rpm else None
                rpm2 = getattr(rpm,'rpm2',None) if rpm else None
                rpm3 = None
                rpm4 = None
                # Override / augment with ESC telemetry if available (gives up to 4 values)
                if esc_1_4:
                    try:
                        esc_rpms = list(getattr(esc_1_4, 'rpm', []))
                        if len(esc_rpms) >= 1: rpm1 = esc_rpms[0]
                        if len(esc_rpms) >= 2: rpm2 = esc_rpms[1]
                        if len(esc_rpms) >= 3: rpm3 = esc_rpms[2]
                        if len(esc_rpms) >= 4: rpm4 = esc_rpms[3]
                    except Exception:
                        pass
                # extend for 5-8 if needed later (not emitted yet in data)
                if esc_5_8 and (rpm3 is None or rpm4 is None):
                    try:
                        esc_rpms_b = list(getattr(esc_5_8, 'rpm', []))
                        # only fill empty slots
                        if rpm3 is None and len(esc_rpms_b) >= 1: rpm3 = esc_rpms_b[0]
                        if rpm4 is None and len(esc_rpms_b) >= 2: rpm4 = esc_rpms_b[1]
                    except Exception:
                        pass
                # Fallback: derive pseudo RPM from PWM (range 1000-2000) scaled to 0-10000
                if servo_raw and (rpm1 is None or rpm1 == 0):
                    try:
                        pwm1 = getattr(servo_raw,'servo1_raw',None)
                        pwm2 = getattr(servo_raw,'servo2_raw',None)
                        pwm3 = getattr(servo_raw,'servo3_raw',None)
                        pwm4 = getattr(servo_raw,'servo4_raw',None)
                        def pwm_to_rpm(p):
                            if p is None: return None
                            # constrain plausible PWM
                            if p < 900 or p > 2200: return None
                            return int((p-1000)/1000 * 10000)  # 1000->0, 2000->10000
                        if rpm1 in (None,0): rpm1 = pwm_to_rpm(pwm1)
                        if rpm2 in (None,0): rpm2 = pwm_to_rpm(pwm2)
                        if rpm3 in (None,0): rpm3 = pwm_to_rpm(pwm3)
                        if rpm4 in (None,0): rpm4 = pwm_to_rpm(pwm4)
                    except Exception:
                        pass
                # location resolution priority
                lat = (gps.lat/1e7) if gps else ((gpos.lat/1e7) if gpos else last_lat)
                lon = (gps.lon/1e7) if gps else ((gpos.lon/1e7) if gpos else last_lon)
                if lat is not None: last_lat = lat
                if lon is not None: last_lon = lon
                data = {
                    'altitude_agl': getattr(terr,'current_height',None),
                    'altitude_msl': getattr(vfr,'alt',None) or (gpos.relative_alt/1000.0 if gpos else None),
                    'airspeed': getattr(vfr,'airspeed',None),
                    'groundspeed': groundspeed,
                    'climb_rate': climb,
                    'heading': getattr(nav,'nav_bearing',None),
                    'lat': lat,
                    'long': lon,
                    'target_dist': getattr(nav,'wp_dist',None),
                    'voltage': pack_voltage if pack_voltage is not None else voltage,
                    'current_a': current_a,
                    'battery_pct': battery_remaining,
                    'mode': mode,
                    'rpm1': rpm1,
                    'rpm2': rpm2,
                    'rpm3': rpm3,
                    'rpm4': rpm4,
                    'roll_deg': (att.roll*57.2958) if att else None,
                    'pitch_deg': (att.pitch*57.2958) if att else None,
                    'yaw_deg': (att.yaw*57.2958) if att else None
                }
            else:
                data = {'error': 0}
            socketio.emit('drone_data', {'param': data})
            last_emit = now
        time.sleep(0.02)



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

app = Flask(__name__)
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

# model_name = "Syouf/MAVLink16bit"
# generator = pipeline("text-generation", model=model_name)

client = InferenceClient(
    provider="fireworks-ai",
    api_key=os.environ["HF_TOKEN"],
)



@app.route('/')
def camera():
    return render_template('dashboard.html')

# Route for AI Script window
@app.route('/ai_script')
def ai_script():
    return render_template('ai_script.html')


@socketio.on('connect')
def drone_stats():
    print("Client connected!")
    # Start drone data thread
    threading.Thread(target=param_data, daemon=True).start()
    # Start video thread
    threading.Thread(target=video_stream, daemon=True).start()
    # command thread
    threading.Thread(target=term, daemon=True).start()

# Socket event for AI Script window
@socketio.on('ai_script')
def handle_ai_script(data):
    text = data.get('text', '')
    print(f"AI Script received: {text}")
    # Placeholder for AI script processing
    completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3-0324",
            messages=[
                {
                    "role": "user",
                    "content": f"{text}"
                }
            ],
        )

    print(completion.choices[0].message)
    result = f"Received: {text}\n Script: {completion.choices[0].message.content}"
    socketio.emit('ai_script_response', {'result': result})


@socketio.on('term_in')
def handle_command(command):
    global process
    if process and process.poll() is None:
        try:
            process.stdin.write(command + '\n')
            process.stdin.flush()
        except Exception as e:
            socketio.emit('term_out', {'data': f'Error writing to process: {e}'})
    else:
        socketio.emit('term_out', {'data': 'Process not running'})

@socketio.on('file')
def script_save(message):
    out = subprocess.run(message,shell=True, text=True, capture_output=True)
    socketio.emit('term_out',out.stdout)



if __name__ == '__main__':
    try:
        socketio.run(app, debug=True)
    finally:
        cap.release()
        cv2.destroyAllWindows()

