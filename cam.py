import cv2 as cv
import numpy as np 

'''
image[50:100, 50:100] = 255


cam shape -- height - 480, width - 640, c- 3 i.e 3d shape --(480,640,3)
some places its (width,height)
(100, 640, 3) is black box dimensions

# Semicircle parameters
center_x = 60  
center_y = 60  
radius = 35
start_angle = 150
end_angle = 390
thickness = 3  # Thickness of the semicircle in pixels
color = 255 # color in rgb 0-255
'''

cap = cv.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    exit()

start_angle = 150
end_angle = 390

i,z = 0,0
angle = [round(z) for z in np.linspace(start_angle, end_angle, num=100)]





def drawing_meter(center_x, center_y, radius, start_angle, end_angle,thickness,color,writer=0):

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
        cv.putText(bottom_np,end_angle,(center_x-30,center_y+5),fontFace=1,fontScale=2,color=(255,255,255),thickness=2)





print("starting")

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
 
    # if frame is read correctly ret is True
    if not ret:
        print("Can't receive frame. Exiting ...")
        break
    
    #converting frame to numpy array 
    frame_np = np.array(frame)


    # Create a NumPy array for the overlay and concatinate with frame array 
    global bottom_np
    bottom_np = np.zeros((100,frame.shape[1], 3), dtype=np.uint8)

    
    if z == 0:
        i+=1
    elif z == 1:
        i-=1
    
    if i == 99:
        z = 1
    elif i == 1:
        z = 0


    drawing_meter(60,60,35,150,390,3,70)    # speed_bk left most meter
    drawing_meter(60,60,35,150,angle[i],3,255,1)   # speed writer left most meter

    drawing_meter(150,60,35,150,390,3,70)    # rpm_bk 2 - left most meter
    drawing_meter(150,60,35,150,angle[i],3,255,1)   # rpm writer 2 - left most meter   

    drawing_meter(640-60,60,35,150,390,3,70)    # speed_bk right most meter
    drawing_meter(640-60,60,35,150,angle[i],3,255,1)   # speed writer right most meter

    drawing_meter(640-150,60,35,150,390,3,70)    # rpm_bk 2 - right most meter
    drawing_meter(640-150,60,35,150,angle[i],3,255,1)   # rpm writer 2 - right most meter 

    


    overlay_data = np.concatenate([frame[:380],bottom_np])
    #cv.putText(overlay_data,"hello world",(20,440),fontFace=1,fontScale=2,color=(255,255,255),thickness=3)

    # put overlay on the frame to give the transperency effect
    frame = cv.addWeighted(overlay_data,1,frame,1,0)
    # Display the frame
    cv.imshow('frame', frame)
    
    if cv.waitKey(1) == ord('q'):
        break