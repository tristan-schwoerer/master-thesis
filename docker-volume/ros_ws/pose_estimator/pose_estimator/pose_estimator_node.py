import rclpy
import threading
import numpy as np
import cv2
from rclpy.node import Node

from sensor_msgs.msg import Image
from geometry_msgs.msg import Point
from visualization_msgs.msg import Marker

from cv_bridge import CvBridge

import jetson.inference
import jetson.utils
from jetson_inference import poseNet
from jetson_utils import videoOutput, logUsage

import csv # DC remove later

from .person_keypoints import *


class PoseEstimator(Node):
    '''
    Class for pose estimation of a person using Nvidia jetson implementation
    of PoseNet and passing messages using ROS2.
    The Class uses Intel Realsense messages on the ROS2 network as input for rgb and depth images
    '''

    def __init__(self):
        super().__init__('pose_estimator')

        # DC For data collection 
        self.peopleCount = 0
        self.imageCount = -1
        self.written = False

        # for working with images in ROS2
        self.bridge=CvBridge()
        self.rgb=None
        self.cudaimage=None
        self.depth=None
        self.poses=None
        self.publisher_ = self.create_publisher(Marker, 'keypoints', 10)
        self.rgb_subscription = self.create_subscription(
            Image,
            '/camera/color/image_raw',
            self.rgb_callback,
            10)
        
        self.depth_subscription = self.create_subscription(
            Image,
            '/camera/aligned_depth_to_color/image_raw',
            self.depth_callback,
            10)
        self.rgb_subscription
        self.depth_subscription  # prevent unused variable warning

        # Setup variables for PoseNet
        self.network = "resnet18-body"
        self.overlay = "links,keypoints,boxes"
        self.threshold = 0.3
        self.output_location = "images" # only needed for saving images

        # Initialising PoseNet and its output
        self.net = poseNet(self.network, ['pose_estimator_node.py'], self.threshold)
        self.output = videoOutput(self.output_location, argv=['pose_estimator_node.py'])

    def rgb_callback(self, msg):
        try:
            self.rgb = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
            cudaimage = cv2.cvtColor(self.rgb, cv2.COLOR_BGRA2RGBA).astype(np.float32) #converting the image to a cuda compatible image
            self.cudaimage = jetson.utils.cudaFromNumpy(cudaimage)
        except:
            pass

    def depth_callback(self, msg):
        try:
            depth=self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
            self.depth = np.array(depth, dtype=np.float32)*0.001
        except:
            pass


    def saveImage(self,img):
            self.imageCount += 1
            print("detected {:d} objects in image".format(len(self.poses)))
            for pose in self.poses:
                print(pose)
                print(pose.Keypoints)

                # print('Links', pose.Links)

            self.output.Render(img)
            self.output.SetStatus("{:s} | Network {:.0f} FPS".format(self.network, self.net.GetNetworkFPS()))
            self.net.PrintProfilerTimes()


    def publishKeypointsMarker(self,kpPerson:person_keypoint):
        for pose in self.poses:
            marker=Marker()
            marker.header.frame_id = "/camera_link"
            marker.header.stamp = self.get_clock().now().to_msg()

            # set shape, Arrow: 0; Cube: 1 ; Sphere: 2 ; Cylinder: 3
            marker.type = 8
            marker.id = 0

            # Set the scale of the marker
            marker.scale.x = .05
            marker.scale.y = .05
            marker.scale.z = .05

            # Set the color
            marker.color.r = 0.0
            marker.color.g = 1.0
            marker.color.b = 0.0
            marker.color.a = 1.0

            for kp in kpPerson.keypoints:
                point=Point()
                point.x=kp.x
                point.y=kp.y
                point.z=kp.z
                marker.points.append(point)
            self.publisher_.publish(marker)
    def getPersons(self):
        '''
        Calculates the location of the person as X and Y coordinates along with the orientation of the person
        '''
        persons = []
        for pose in self.poses:
            kpPerson=person_keypoint(pose.Keypoints, self.depth)
            self.publishKeypointsMarker(kpPerson=kpPerson)
            persons.append(kpPerson)
            
        return persons
    
    def writing(self, personlist):
        '''
        DC Function for writing csv file with person variables for captured images
        '''
        with open('SanityCheck.csv', mode = 'a') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)            
            
            if not self.written:
                writer.writerow(['ImageID', 'PersonX', 'PersonY', 'Orientation'])
                self.written = True
            for person in personlist:
                writer.writerow([str(self.imageCount), str(person.x), str(person.y), str(person.orientation)])


    def detectPoses(self):
        '''
        Perform pose estimation (with overlay)
        '''
        self.poses = self.net.Process(self.cudaimage, overlay=self.overlay)

        #TODO comment out when running node
        # print the pose results
        self.saveImage(self.cudaimage)
        persons=self.getPersons()

        self.peopleCount += len(persons) 
        self.writing(persons) 
          

def main(args=None):
    
    rclpy.init(args=args)
    pose_estimator = PoseEstimator()  # Start ROS2 node
    thread = threading.Thread(target=rclpy.spin, args=(pose_estimator, ), daemon=True)
    thread.start()

    rate = pose_estimator.create_rate(10)
    # initiate pose estimator object

    try:
        while rclpy.ok():
            rate.sleep()
            if(pose_estimator.cudaimage != None): # Make sure an image has been captured
                pose_estimator.detectPoses()
                
            if pose_estimator.peopleCount == 1000: # DC for data collection run only until a certain amount of people have been detected
                break
            # rclpy.spin_once(pose_estimator)
    except KeyboardInterrupt:
        pass

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    pose_estimator.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()