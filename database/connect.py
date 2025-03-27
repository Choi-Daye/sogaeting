import cv2
import os
from ultralytics import YOLO
from api.crud import create_mounting, find_subscription_by_id
from db import database, schemas
from sqlalchemy.orm import Session
from decimal import Decimal
from fastapi import HTTPException
from pywebpush import webpush, WebPushException
import logging
import json


record = {
        'camera_idx': '1',
        'detection_accuracy': Decimal(0.00),
        'detection_scene': b''
    }

# import customizing yolo model
model = YOLO('best.pt')

# class name
class_names = ["mounting"]

# open video
video_path = 'video/cow.mp4'
cap = cv2.VideoCapture(video_path)

# get the frame rate of the original video
fps = cap.get(cv2.CAP_PROP_FPS)

# video to save
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
# initialization
frame_idx = 0
detect_frame_idx = -1
out = None
detect_frame_count = 0  # number of frames detected
filename = None
cnt_conf = 0

# folder for video to save
output_dir = 'detected_video'
os.makedirs(output_dir, exist_ok=True)  # create folder
def get_unique_filename(base_filename, ext='mp4'):
    cnt = 1
    while True:
        filename = os.path.join(output_dir, f"{base_filename}_{cnt}.{ext}")
        if not os.path.exists(filename):
            return filename
        cnt += 1

# draw bounding box
def draw_boxes(frame, boxes, confidences, class_ids):
    for box, confidence, class_id in zip(boxes, confidences, class_ids):
        x1, y1, x2, y2 = box
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        label = f"{class_names[int(class_id)]}: {confidence:.2f}"
        cv2.putText(frame, label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    return frame

# push
def send_push(message: dict, db:Session = database.SessionLocal()):
    try:
        subscribed_user = find_subscription_by_id(db)
        
        # output subscription information to log
        logging.debug(f"Subscribed user endpoint: {subscribed_user.endpoint}")
        logging.debug(f"Subscribed user auth: {subscribed_user.auth}")
        logging.debug(f"Subscribed user p256dh: {subscribed_user.p256dh}")
        
        # send web push
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
    # returns additional information in the body of the response
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

# connect to DataBase
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


### run ###
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    # object detection in frames
    results = model.predict(frame, conf=0.75)
    
    if results:
        result = results[0]  # select the first result
        boxes = result.boxes.xyxy  # Bounding boxes
        confidences = result.boxes.conf  # confidence scores
        class_ids = result.boxes.cls  # class IDs
        # detection of estrus
        if boxes.shape[0] > 0:
            frame = draw_boxes(frame, boxes, confidences, class_ids)
            # first detection frame
            if out is None:
                filename = get_unique_filename('detected_mounting')
                out = cv2.VideoWriter(filename, fourcc, fps, (int(cap.get(3)), int(cap.get(4))))
                detect_frame_count = 0  # Initialize the number of frames detected
            # save first detection idx
            detect_frame_idx = frame_idx
            # add all the accuracy
            cnt_conf += confidences.sum().item()
            # number of frames
            detect_frame_count += 1
            out.write(frame)
        else:
            # detection does not persist
            if out is not None:
                # no more than 30 undetected frames
                if frame_idx - detect_frame_idx <= 30:
                    out.write(frame)
                # more than 30 undetected frames
                else:
                    out.release()
                    # initialization detected franes
                    out = None
                    # save accuracy
                    record['detection_accuracy'] = cnt_conf / detect_frame_count
                    # initialization accuracy
                    cnt_conf = 0
                    
                    # do not save if detected frames are below 5
                    if detect_frame_count <= 5 and filename:
                        os.remove(filename)
                        filename = None
                    
                    if filename is not None:
                        # read mp4 file binary
                        with open(filename, 'rb') as file:
                            binary_data = file.read()  
                        record['detection_scene'] = binary_data

                    # insert into DB
                    with database.SessionLocal() as db:
                        create_mounting_from_record(record, db)

    else:
        # safe processing when results are empty
        if out is not None:
            if frame_idx - detect_frame_idx <= 30:
                out.write(frame)
            else:
                out.release()
                out = None
                record['detection_accuracy'] = cnt_conf / detect_frame_count
                cnt_conf = 0
                
                # do not save if detected frames are below 5
                if detect_frame_count <= 5 and filename:
                    os.remove(filename)
                    filename = None
                
                if filename is not None:
                    # read mp4 file binary
                    with open(filename, 'rb') as file:
                        binary_data = file.read()  
                    record['detection_scene'] = binary_data


                # insert into DB
                with database.SessionLocal() as db:
                    create_mounting_from_record(record, db)
    
    # frame idx
    frame_idx += 1

# remaining video handler shutdown
if out is not None:
    out.release()
    out = None
    record['detection_accuracy'] = cnt_conf / detect_frame_count
    cnt_conf = 0
    
    # do not save if detected frames are below 5
    if detect_frame_count <= 5 and filename:
        os.remove(filename)
    
    if filename is not None:
        pass
        # read mp4 file binary
        with open(filename, 'rb') as file:
            binary_data = file.read()  
        record['detection_scene'] = binary_data

    # insert into DB
    with database.SessionLocal() as db:
        create_mounting_from_record(record, db)

cap.release()
