#!/usr/bin/env python3
import sqlite3
from rosidl_runtime_py.utilities import get_message
from rclpy.serialization import deserialize_message

import matplotlib.pyplot as plt
from cv_bridge import CvBridge
import cv2
import os


class BagFileParser():
    def __init__(self, bag_file):
        self.conn = sqlite3.connect(bag_file)
        self.cursor = self.conn.cursor()

        # create a message type map
        topics_data = self.cursor.execute(
            "SELECT id, name, type FROM topics").fetchall()
        self.topic_type = {name_of: type_of for id_of,
                           name_of, type_of in topics_data}
        self.topic_id = {name_of: id_of for id_of,
                         name_of, type_of in topics_data}
        self.topic_msg_message = {name_of: get_message(
            type_of) for id_of, name_of, type_of in topics_data}

    def __del__(self):
        self.conn.close()

    # Return [(timestamp0, message0), (timestamp1, message1), ...]
    def get_messages(self, topic_name):

        topic_id = self.topic_id[topic_name]
        # Get from the db
        rows = self.cursor.execute(
            "SELECT timestamp, data FROM messages WHERE topic_id = {}".format(topic_id)).fetchall()
        # Deserialise all and timestamp them
        return [(timestamp, deserialize_message(data, self.topic_msg_message[topic_name])) for timestamp, data in rows]


if __name__ == "__main__":

    bag_file = '/home/tristan/repositories/master-thesis/ros2_ws/test_bag/test_bag_0.db3'

    parser = BagFileParser(bag_file)
    cvbridge = CvBridge()
    # people = parser.get_messages("/people")
    social_map_msgs = parser.get_messages("/social_map")
    path = dirname = os.path.dirname(bag_file)
    os.mkdir(os.path.join(path, "images"))
    for i, msg in enumerate(social_map_msgs):
        image = cvbridge.imgmsg_to_cv2(msg[1])
        cv2.imwrite(os.path.join(path, "images",
                    str(i).zfill(8)+".png"), image)
