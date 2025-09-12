#!/usr/bin/env python3

import rospy
from sensor_msgs.msg import LaserScan, CompressedImage
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
import numpy as np
from geometry_msgs.msg import Twist
from time import *
import math
from math import pi

rospy.init_node("line_following_with_obstacle_avoidance")

# 라인 팔로잉 관련 변수
LINEAR_SPEED = 0.45
ANGULAR_SPEED = 0.5

DIST = 1.2

# LiDAR 관련 변수
ROBOT_WIDTH = 0.3
MIN_PASSABLE_WIDTH = 0.5

result3 = []
ranges = []
path_msg = String()
path_msg.data = "D"
LKAS_RESTART_FLAG = True
LKAS_RESTART = None

camera_move = Twist()
lidar_move = Twist()
laba_move = Twist()
stop_move = Twist()
hope_move = Twist()

avoidance_done = False

mode = "LKAS"

laba_count = 0
yaw_z = None

laba_time = None

laba_initial = True
# imu_offset = None

path_flag = True


bridge = CvBridge()
cmd_vel = rospy.Publisher('/cmd_vel', Twist, queue_size=10)

def path_callback(msg):
    global path_msg
    path_msg = msg

# def imu_callback(msg):
#     global imu_offset, yaw_z

#     x = msg.orientation.x
#     y = msg.orientation.y
#     z = msg.orientation.z
#     w = msg.orientation.w
    
#     t3 = +2.0 * (w * z + x * y)
#     t4 = +1.0 - 2.0 * (y * y + z * z)
#     yaw_z = math.atan2(t3, t4)/pi*180

#     if imu_offset is None:
#         imu_offset = yaw_z

def camera_callback(data):
    """CompressedImage 데이터로 라인 팔로잉"""
    try:
        # CompressedImage 데이터를 OpenCV 이미지로 변환
        np_arr = np.frombuffer(data.data, np.uint8)
        cv_image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        line_following(cv_image)
    except Exception as e:
        rospy.logerr(f"Error processing compressed image: {e}")

def lidar_callback(msg):
    global laba_time,laba_count, LKAS_RESTART_FLAG, LKAS_RESTART
    global result3
    global lidar_move, camera_move, laba_move, stop_move, hope_move
    global ranges, path_msg, path_flag
    global laba_initial, avoidance_done
    global mode#, imu_offset, yaw_z

    ranges = msg.ranges[::-1]
    
    f_r = [min(x, DIST) for x in ranges]

    result = smooth_list(f_r)
    result2 = smooth_list(result)
    result3 = smooth_list(result2)

    laba_avoidance()

    result4 = to_go(result3)

    lidar_move.linear.x = 0.2

    if(abs(-result4/100) <= 0.1):
        lidar_move.angular.z = -result4/50*3
    else:
        lidar_move.angular.z = -result4/50*2

    if(sum(result3)/len(result3) >= DIST - 0.03) and mode != "LIDAR_AVOID":
        mode = "LKAS"
    else:
        if laba_initial:
            laba_time = rospy.Time.now().to_sec()
            laba_initial = False
        print(rospy.Time.now().to_sec() - laba_time)
        if rospy.Time.now().to_sec() - laba_time >= 12:
            avoidance_done = True

        if avoidance_done == True and rospy.Time.now().to_sec() - laba_time >= 35:
            mode = "LIDAR_LAVA"
        else:
            mode = "LIDAR_AVOID"

        # if 12 >= rospy.Time.now().to_sec() - laba_time >= 9:
        #     mode = "RECOVERY"

    # if mode == "RECOVERY":
    #     recovery_move = Twist()
    #     if((yaw_z)%360 - 180 - imu_offset > 2.5): # imu need check
    #         recovery_move.angular.z = -0.3
    #         recovery_move.linear.x = 0.1
    #     elif((yaw_z)%360 - 180 - imu_offset < 2.5):
    #         recovery_move.angular.z = 0.3
    #         recovery_move.linear.x = 0.1
    #     else:
    #         recovery_move.angular.z = 0
    #         recovery_move.linear.x = 0.15

    # if(185 >= abs(yaw_z - imu_offset) >=175) and path_msg.data == "D":
    #     mode = "STOP"
    #     stop_move.linear.x = 0
    #     stop_move.angular.z = 0

    #mode = "STOP"

    # if mode == "STOP" or mode == "HOPE":
    #     mode = "HOPE"
    #     if path_msg.data == "A":
    #         ang = (imu_offset + 26) #28degree
    #         print(abs(yaw_z - ang))
    #         if(abs(yaw_z - ang) <= 4):
    #             path_flag = False
            
    #         if path_flag:
    #             str = 0.29
    #         else:
    #             str = 0
    #     if path_msg.data == "B":
    #         ang = (imu_offset + 10) #13degree
    #         print(abs(yaw_z - ang))
    #         if(abs(yaw_z - ang) <= 4):
    #             path_flag = False
            
    #         if path_flag:
    #             str = 0.28
    #         else:
    #             str = 0
                
    #     if path_msg.data == "C":
    #         str = 0
    #     hope_move.linear.x = 0.1
    #     hope_move.angular.z = str

        #  min(result3) < 0.3:
        #     mode = "LIDAR_AVOID"
        #     if LKAS_RESTART_FLAG:
        #         LKAS_RESTART = rospy.Time.now().to_sec()
        #         LKAS_RESTART_FLAG = False
        # if LKAS_RESTART is not None and (rospy.Time.now().to_sec() - LKAS_RESTART >= 15):
        #     mode = "LKASif"

        

    if mode == "LKAS":
        cmd_vel.publish(camera_move)
    elif mode == "LIDAR_AVOID":
        cmd_vel.publish(lidar_move)
    elif mode == "LIDAR_LAVA":
        cmd_vel.publish(laba_move)
    # elif mode == "RECOVERY":
    #     cmd_vel.publish(recovery_move)
    # elif mode == "STOP":
    #     cmd_vel.publish(stop_move)
    # elif mode == "HOPE":
    #     cmd_vel.publish(hope_move)

    print(mode)
    
def laba_avoidance():
    global ranges
    global laba_move
    

    close_angles = [i for i, d in enumerate(ranges) if d and d < 0.5]
    if close_angles:
        avg_angle = sum(close_angles) / len(close_angles)
        if avg_angle < len(ranges) // 2:  # Obstacle on the right
            laba_move.angular.z = -0.4  # Turn left
            laba_move.linear.x = 0.1
        elif avg_angle > len(ranges) // 2:  # Obstacle on the left
            laba_move.angular.z = 0.4  # Turn right
            laba_move.linear.x = 0.1
        
def to_go(lst):
    global laba_time

    # 좌측과 우측의 1 제거
    left = 0
    while left < len(lst) and lst[left] == DIST:
        left += 1
    right = len(lst) - 1
    while right >= 0 and lst[right] == DIST:
        right -= 1
   
    # 리스트의 중간 부분 추출
    trimmed = lst[left:right + 1]
   
    # 연속된 1의 가장 긴 구간의 시작과 끝 인덱스 계산
    max_length = 0
    current_start = None
    longest_start = None
    longest_end = None
   
    for i, num in enumerate(trimmed):
        if num == DIST:
            if current_start is None:
                current_start = i
        else:
            if current_start is not None:
                length = i - current_start
                if length > max_length:
                    max_length = length
                    longest_start = current_start
                    longest_end = i - 1
                current_start = None
   
    # 마지막 1 구간 처리
    if current_start is not None:
        length = len(trimmed) - current_start
        if length > max_length:
            longest_start = current_start
            longest_end = len(trimmed) - 1

    
   
    # 반환할 인덱스를 원래 리스트 기준으로 변환
    if longest_start is not None and longest_end is not None:
        tmp = (longest_start + left, longest_end + left)
    else:
        tmp = [190]

    return sum(tmp)/len(tmp)-180



def smooth_list(l):
    # l2 = l[:]
    
    # for i in range(len(l)):
    #     current = l[i]
    #     left = l[i - 1] if i > 0 else 0  
    #     right = l[i + 1] if i < len(l) - 1 else 0 
        
    #     if current == 0:
    #         if left != 0:
    #             l2[i] = left
    #         elif right != 0:
    #             l2[i] = right
    # # print(l2)    
    # return l2
    while 0 in l:  # 리스트에 0이 포함되어 있는 동안 반복
        l = [
            l[i - 1] if l[i] == 0 and i > 0 and l[i - 1] != 0 else
            l[i + 1] if l[i] == 0 and i < len(l) - 1 and l[i + 1] != 0 else
            l[i]
            for i in range(len(l))
        ]
    return l

def line_following(cv_image):
    global camera_move
    """카메라를 활용한 라인 팔로잉"""
    # 이미지 전처리
    gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    # ROI 설정 (하단 1/3)
    height, width = binary.shape
    roi = binary[int(height*2/3):, :]

    # 중심선 계산
    contours, _ = cv2.findContours(roi, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        M = cv2.moments(largest_contour)
        if M["m00"] > 0:
            cx = int(M["m10"] / M["m00"])
            error = cx - width // 2

            # 라인 중심에 맞추기 위한 회전
            camera_move.linear.x = LINEAR_SPEED
            camera_move.angular.z = -float(error) / 100
            # cmd_vel.publish(move)


rospy.Subscriber("/scan", LaserScan, lidar_callback)
rospy.Subscriber("/camera/rgb/image_raw/compressed", CompressedImage, camera_callback)
# rospy.Subscriber('/imu', Imu, imu_callback)
# rospy.Subscriber("/path_", String, path_callback)
rospy.spin()
