import cv2
import os
from ultralytics import YOLO
# from api.crud import create_mounting, find_subscription_by_id
# from db import database, schemas
# from sqlalchemy.orm import Session
from decimal import Decimal
# from fastapi import HTTPException
# from pywebpush import webpush, WebPushException
# import logging
import json


record = {
        'camera_id': '1',
        'detection_accuracy': Decimal(0.00),
        # 'mount_yn': 0,  # Default value
        # 'is_deleted': 0,  # Default value
        'detection_scene': b''
    }
# Import YOLO model (using customiZed weights)
model = YOLO('best.pt')

# Class names
class_names = ["mounting"]

# Open a video file
video_path = ''
cap = cv2.VideoCapture(video_path)

# Get the frame rate of the original video
fps = cap.get(cv2.CAP_PROP_FPS)

# Video setting to save
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
# Initialization
frame_idx = 0
detect_frame_idx = -1
out = None
detect_frame_count = 0  # Tracking the number of frames detected
filename = None
cnt_conf = 0
height_max = 0
height_min = 1000
mount = False

# The folder where the video will be saved
output_dir = 'detected_video'
os.makedirs(output_dir, exist_ok=True)  # Create folder if you don't have it
def get_unique_filename(base_filename, ext='mp4'):
    cnt = 1
    while True:
        filename = os.path.join(output_dir, f"{base_filename}_{cnt}.{ext}")
        if not os.path.exists(filename):
            return filename
        cnt += 1

# Drawing bounding box
def draw_boxes(frame, boxes, confidences, class_ids):
    for box, confidence, class_id in zip(boxes, confidences, class_ids):
        x1, y1, x2, y2 = box
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        label = f"{class_names[int(class_id)]} : {confidence:.2f}"
        cv2.putText(frame, label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.putText(frame, str(result.boxes.xywh[0][3]), (int(x1), int(y1) - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    return frame

# Push notification
def send_push(message: dict, db:Session = database.SessionLocal()):
    try:
        subscribed_user = find_subscription_by_id(db)
        
        # Output subscription information using logs
        logging.debug(f"Subscribed user endpoint: {subscribed_user.endpoint}")
        logging.debug(f"Subscribed user auth: {subscribed_user.auth}")
        logging.debug(f"Subscribed user p256dh: {subscribed_user.p256dh}")
        
        # Send web push
        webpush(
            subscription_info={
                "endpoint": subscribed_user.endpoint,
                "keys": {
                    "auth": subscribed_user.auth,
                    "p256dh": subscribed_user.p256dh
                }
            },
            data=json.dumps({'title':message['title'], 'body': message['message']}),
            vapid_private_key=subscribed_user.private_key,
            vapid_claims={"sub": f"mailto:{subscribed_user.user_email}"}
        )
    except WebPushException as ex:
        print("I'm sorry, Dave, but I can't do that: {}", repr(ex))
    # Mozilla returns additional information in the body of the response.
        if ex.response and ex.response.json():
            extra = ex.response.json()
            print("Remote service replied with a {}:{}, {}",
                extra.code,
                extra.errno,
                extra.message
                )
            raise HTTPException(status_code=500, detail=f"Web push failed: {repr(ex)}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {repr(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {repr(e)}")

    return {"message": "Push notifications sent."}

# Connecting with the database
def create_mounting_from_record(record: dict, db: Session):
    mounting_create = schemas.MountingCreate(
        detection_accuracy=record['detection_accuracy'],
        camera_idx=record['camera_idx'],
        detection_scene=record['detection_scene']
    )

    message = {
    "title": "승가[MT]",
    "message": f"{mounting_create.camera_idx}번 카메라에서 승가 발생" 
    }

    send_push(message)

    create_mounting(db=db, mounting=mounting_create)



### RUN ###
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    # Object detection in frames with YOLO model
    results = model.predict(frame, conf=0.75)
    
    if results:
        result = results[0]  # Select the first result
        boxes = result.boxes.xyxy  # Bounding boxes
        confidences = result.boxes.conf  # Confidence scores
        class_ids = result.boxes.cls  # Class IDs
        # Detection of mounting (estrus)
        if boxes.shape[0] > 0:
            frame = draw_boxes(frame, boxes, confidences, class_ids)
            print("높이", result.boxes.xywh[0][3].item())
            
            # First detection frame
            if out is None:
                filename = get_unique_filename('detected_mounting')
                out = cv2.VideoWriter(filename, fourcc, fps, (int(cap.get(3)), int(cap.get(4))))
                detect_frame_count = 0  # Initialize the number of frames detected for the new video clip
            # Save first detection idx
            detect_frame_idx = frame_idx
            # Add all the accuracy
            cnt_conf += confidences.sum().item()
            # Number of frames
            detect_frame_count += 1

            # Check and update the height of all bounding boxes detected in the current frame
            height = result.boxes.xywh[0][3].item()
            if height_max < height:
                height_max = height

            if height_min > height:
                height_min = height

            out.write(frame)

        # If detection does not persist
        else:
            # When the first frame exists
            if out is not None:
                # When there are no more than 30 undetected frames
                if frame_idx - detect_frame_idx <= 30:
                    # If the height difference in the bounding box is more than 10, it is detected as mounting (estrus)
                    if height_max - height_min > 10 :
                        print("-----------------------------------------")
                        print("높이차이O")
                        print(height_max - height_min)
                        print("-----------------------------------------")
                        mount = True
                        # Initialization
                        height_max = 0
                        height_min = 1000
                    # If the height difference of the bounding box is less than 10, it is not detected by mounting (estrus)
                    else :
                        if not (height_max == 0 and height_min == 1000) :
                            print("-----------------------------------------")
                            print("높이차이X")
                            print(height_max - height_min)
                            print("-----------------------------------------")
                            # Initialization
                            height_max = 0
                            height_min = 1000

                    out.write(frame)

                # When mounting is no longer detected
                else:
                    out.release()
                    # Initialization
                    out = None
                    # Accuracy 
                    record['detection_accuracy'] = cnt_conf / detect_frame_count
                    # Accuracy Initialization
                    cnt_conf = 0
                    
                    # Do not save if detected frames are below 5
                    if detect_frame_count <= 5 and filename:
                        os.remove(filename)
                        filename = None
                    # Do not save if there is no height change
                    elif mount == False :
                        os.remove(filename)
                        filename = None
                    
                    height_max = 0
                    height_min = 1000
                    mount = False

                    if filename is not None:
                        # Read mp4 file binary
                        with open(filename, 'rb') as file:
                            binary_data = file.read()  # Read the entire data of a video file as binary
                        record['detection_scene'] = binary_data

                    # Insert into DB
                    with database.SessionLocal() as db:
                        create_mounting_from_record(record, db)

    else:
        # Safe processing when results are empty
        if out is not None:
            if frame_idx - detect_frame_idx <= 30:
                out.write(frame)
            else:
                out.release()
                out = None
                record['detection_accuracy'] = cnt_conf / detect_frame_count
                cnt_conf = 0
                
                # Do not save if detected frames are below 5
                if detect_frame_count <= 5 and filename:
                    os.remove(filename)
                    filename = None
                # Do not save if there is no height change
                elif mount == False :
                    os.remove(filename)
                    filename = None

                height_max = 0
                height_min = 1000
                mount = False

                if filename is not None:
                    pass
                    # Read mp4 file binary
                    with open(filename, 'rb') as file:
                        binary_data = file.read()  # Read the entire data of a video file as binary
                    record['detection_scene'] = binary_data


                # Insert into DB
                with database.SessionLocal() as db:
                    create_mounting_from_record(record, db)
    
    # Frame idx
    frame_idx += 1

# Remaining Video Handler Shutdown
if out is not None:
    out.release()
    out = None
    record['detection_accuracy'] = cnt_conf / detect_frame_count
    cnt_conf = 0
    
    # Do not save if detected frames are below 5
    if detect_frame_count <= 5 and filename:
        os.remove(filename)
        filename = None
    # Do not save if there is no height change
    elif mount == False :
        os.remove(filename)
        filename = None
    
    height_max = 0
    height_min = 1000
    mount = False
    
    if filename is not None:
        pass
        # Read mp4 file binary
        with open(filename, 'rb') as file:
            binary_data = file.read()  # Read the entire data of a video file as binary
        record['detection_scene'] = binary_data

    
    with database.SessionLocal() as db:
        create_mounting_from_record(record, db)

cap.release()
