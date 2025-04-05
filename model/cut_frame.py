# save video as photos
import cv2
import os

# video file path
video_path = ''

# directory path to store the image
output_dir = ''

# create directory
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# read a video file
cap = cv2.VideoCapture(video_path)

# initialize frame number
frame_count = 0

while True:
    ret, frame = cap.read()  # read frame
    if not ret:
        break  # end the video
    
    # save as an image file (ex: frame_0001.png)
    frame_filename = os.path.join(output_dir, f'frame_{frame_count:04d}.png')
    cv2.imwrite(frame_filename, frame)
    
    frame_count += 1

# resource release
cap.release()

print(f"총 {frame_count}개의 프레임이 저장되었습니다.")
