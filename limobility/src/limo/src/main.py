#!/usr/bin/env python3
import rospy
from sensor_msgs.msg import LaserScan, CompressedImage
from geometry_msgs.msg import Twist
from math import *
import cv2
import numpy as np
from cv_bridge import CvBridge


class IntegratedNode:
    def __init__(self):
        rospy.init_node("integrated_node")

        # Publisher
        self.pub = rospy.Publisher("/cmd_vel", Twist, queue_size=1)

        # Subscribers
        rospy.Subscriber("/scan", LaserScan, self.lidar_cb)
        rospy.Subscriber("/camera/rgb/image_raw/compressed", CompressedImage, self.camera_cb)

        # Messages and utilities
        self.lidar_msg = None
        self.camera_msg = None
        self.cmd_msg = Twist()
        self.bridge = CvBridge()

        # Flags
        self.lidar_flag = False
        self.camera_flag = False

        # LKAS parameters
        self.steer = 0

        # Obstacle avoidance parameters
        self.dist_data = 0
        self.direction = None
        self.is_scan = False
        self.obstacle_ranges = []
        self.center_list_left = ( [] )
        self.center_list_right = ( [] )

        self.scan_degree = 45
        self.min_dist = 0.2

        # Movement parameters
        self.speed = 0
        self.angle = 0
        self.default_speed = 0.15 # 장애물이 없을때의 속도
        self.default_angle = 0.0
        self.turning_speed = 0.08 # 로봇 회전 속도
        self.backward_speed = -0.08 # 로봇 후진 속도
        self.OBSTACLE_PERCEPTION_BOUNDARY = 20 # 거리 경계값(장애물 감지 민감도)
        self.ranges_length = None  

        self.rate = rospy.Rate(10)

    def lidar_cb(self, msg):
        # 라이다 데이터 콜백 함수:
        self.msg = (
            msg
        )
        if(len(self.obstacle_ranges) > self.OBSTACLE_PERCEPTION_BOUNDARY):
            self.obstacle_exit = True
        else:
            self.obstacle_exit = False
       
        ##================장애물 탐지를 우선으로 둘 건지를 설정하는 부분================##
        self.lidar_msg = msg
        if msg.ranges and any(0 < r < 0.3 for r in msg.ranges):
            self.is_scan = True
        else:
            self.is_scan = False
        ##================장애물 탐지를 우선으로 둘 건지를 설정하는 부분================##


    def camera_cb(self, msg):
        # 카메라 데이터 콜백 함수:
        self.camera_msg = msg
        self.camera_flag = True
        rospy.loginfo(f"{self.camera_msg} : camera 값")

        # OpenCV를 통해 이미지를 표시
        try:
            cv_img = self.bridge.compressed_imgmsg_to_cv2(msg)
            cv2.imshow("Camera View", cv_img)  # OpenCV 창에 이미지 출력
            if cv2.waitKey(1) & 0xFF == ord('q'):  # 'q'를 눌러 종료
                rospy.signal_shutdown("User exited the viewer.")  # ROS 노드 종료
        except Exception as e:
            rospy.logerr(f"Error displaying camera data: {e}")

    def lkas(self):
        # 차선 유지 보조 시스템 (LKAS) 기능:
        # 카메라 데이터를 사용하여 차선을 인식하고, 조향 각도 (steer)를 계산.
       
        if not self.camera_flag:
            return

        cv_img = self.bridge.compressed_imgmsg_to_cv2(self.camera_msg)
        y, x, channel = cv_img.shape
        hsv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2HSV)

        # Filtering for white and yellow
        # 우리 환경에 맞는 hsv 값을 찾아야 함..
        white_filter = cv2.inRange(hsv_img, np.array([121, 23, 60]), np.array([159, 102, 105]))
        yellow_filter = cv2.inRange(hsv_img, np.array([0, 21, 170]), np.array([70, 255, 223]))
        and_img = cv2.bitwise_and(cv_img, cv_img, mask=cv2.bitwise_or(white_filter, yellow_filter))

        # Perspective transform
        margin_x, margin_y = 250, 300
        src_pts = np.float32([(0, y), (margin_x, margin_y), (x - margin_x, margin_y), (x, y)])
        dst_margin_x = 120
        dst_pts = np.float32([(dst_margin_x, y), (dst_margin_x, 0), (x - dst_margin_x, 0), (x - dst_margin_x, y)])

        matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
        warp_img = cv2.warpPerspective(and_img, matrix, (x, y))
        gray_img = cv2.cvtColor(warp_img, cv2.COLOR_BGR2GRAY)

        # Binary image and lane detection
        bin_img = np.zeros_like(gray_img)
        bin_img[gray_img != 0] = 1
        center_index = x // 2
        avg_indices = None

        try:
            left_histogram = np.sum(bin_img[:, :center_index], axis=0)
            right_histogram = np.sum(bin_img[:, center_index:], axis=0)
            left_base = np.argmax(left_histogram)
            right_base = np.argmax(right_histogram) + center_index
            avg_indices = ((left_base + right_base) // 2) 
        except:
            avg_indices = center_index

        if avg_indices is not None:
            error_index = center_index - avg_indices
            self.steer = error_index * pi / x
        else:
            self.steer = 0
        rospy.loginfo(f"{self.steer} : 조향 값")

    def LiDAR_scan(self):
        obstacle = []
        if self.lidar_flag == False:
            self.degrees = [
                (self.msg.angle_min + (i * self.msg.angle_increment)) * 180 / pi
                for i, data in enumerate(self.msg.ranges)
            ]
            self.ranges_length = len(self.msg.ranges)
            self.lidar_flag = True

        for i, data in enumerate(self.msg.ranges):
            if 0 < data < 0.3 and -self.scan_degree < self.degrees[i] < self.scan_degree:
                obstacle.append(i)
                self.dist_data = data

        if obstacle:
            first = obstacle[0]
            first_dst = first
            last = obstacle[-1]
            last_dst = self.ranges_length - last
            self.obstacle_ranges = self.msg.ranges[first : last + 1]
        else:
            first, first_dst, last, last_dst = 0, 0, 0, 0

        return first, first_dst, last, last_dst


    def compare_space(self, first_dst, last_dst):
        if self.obstacle_exit == True:
           
            if first_dst > last_dst and self.dist_data > self.min_dist:
                self.direction = "right"
           
            elif first_dst <= last_dst and self.dist_data > self.min_dist:
                self.direction = "left"
           
            else:
                self.direction = "back"
        else:
            self.direction = "front"

    def move_direction(self, last, first):
        # 로봇 이동 방향 설정: 장애물의 위치와 방향에 따라 속도와 조향 각도를 조정.
        if self.direction == "right":
            for i in range(first):
                self.center_list_left.append(i)
            Lcenter = self.center_list_left[floor(first / 2)]
            center_angle_left = -self.msg.angle_increment * Lcenter
            self.angle = center_angle_left
            self.speed = self.default_speed

        elif self.direction == "left":
            for i in range(len(self.msg.ranges)):
                self.center_list_right.append(last + i)
            Rcenter = self.center_list_right[
                floor(last + (self.ranges_length - last) / 2)
            ]
            center_angle_right = self.msg.angle_increment * Rcenter
            self.angle = center_angle_right / 2.5
            self.speed = self.default_speed            

        elif self.direction == "back":
            self.angle = self.default_angle
            self.speed = self.backward_speed
        else:
            self.angle = self.default_angle
            self.speed = self.default_speed

    def ctrl(self):
        # 로봇 제어: 장애물 회피가 활성화되면 이를 우선하며, 그렇지 않으면 LKAS를 사용. 속도 및 조향 각도를 `/cmd_vel` 토픽에 Publish.
        str = ""
        if self.is_scan:
            str = "obstacle"
            first, first_dst, last, last_dst = self.LiDAR_scan()
            self.compare_space(first_dst, last_dst)
            self.move_direction(last, first)
        else:
            str = "line"
            self.lkas()
            self.speed = 0.1
            self.angle = self.steer

        self.cmd_msg.linear.x = self.speed
        self.cmd_msg.angular.z = self.angle
        self.pub.publish(self.cmd_msg)
        rospy.loginfo(str + "control published 속도 : " + f"{self.speed}")  # 차선 추적 모드
        self.rate.sleep()

    def main(self):
        while not rospy.is_shutdown():
            # self.lkas()
            self.ctrl()

if __name__ == "__main__":
    node = IntegratedNode()
    node.main()
