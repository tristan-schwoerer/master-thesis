# Copyright 2023 Intel Corporation. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# DESCRIPTION #
# ----------- #
# Use this launch file to launch 2 devices.
# The Parameters available for definition in the command line for each camera are described in rs_launch.configurable_parameters
# For each device, the parameter name was changed to include an index.
# For example: to set camera_name for device1 set parameter camera_name1.
# command line example:
# ros2 launch realsense2_camera rs_multi_camera_launch.py camera_name1:=D400 device_type2:=l5. device_type1:=d4..

"""Launch realsense2_camera node."""
import rs_ours_launch
import copy
from launch import LaunchDescription
import launch_ros.actions
from launch.actions import IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, ThisLaunchFileDir
from launch.actions import TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).parent.absolute()))

local_parameters = [{'name': 'camera_name1', 'default': 'camera1', 'description': 'left_camera', 'usb_port_id': '2-3.4', 'serial_no': '_834412071134'},
                    {'name': 'camera_name2', 'default': 'camera2', 'description': 'right_camera',
                        'usb_port_id': '2-3.1', 'serial_no': '_034422074840'},
                    ]


def set_configurable_parameters(local_params):
    return dict([(param['original_name'], LaunchConfiguration(param['name'])) for param in local_params])


def duplicate_params(general_params, posix):
    local_params = copy.deepcopy(general_params)
    for param in local_params:
        param['original_name'] = param['name']
        param['name'] += posix
    return local_params


def generate_launch_description():
    params1 = duplicate_params(rs_ours_launch.configurable_parameters, '1')
    params2 = duplicate_params(rs_ours_launch.configurable_parameters, '2')
    return LaunchDescription(
        rs_ours_launch.declare_configurable_parameters(local_parameters) +
        rs_ours_launch.declare_configurable_parameters(params1) +
        rs_ours_launch.declare_configurable_parameters(params2) +
        [
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    [ThisLaunchFileDir(), '/rs_ours_launch.py']),
                launch_arguments=set_configurable_parameters(params1).items(),
            ),
            TimerAction(period=5.0,
                        actions=[IncludeLaunchDescription(
                            PythonLaunchDescriptionSource(
                                [ThisLaunchFileDir(), '/rs_ours_launch.py']),
                            launch_arguments=set_configurable_parameters(params2).items())]),

            # dummy static transformation from camera1 to camera2
            launch_ros.actions.Node(
                package="tf2_ros",
                executable="static_transform_publisher",
                arguments=["0", "-.055", "0", "0.4386448745",
                           "0", "0", "camera_link", "camera2_link"]
            ),
            launch_ros.actions.Node(
                package="tf2_ros",
                executable="static_transform_publisher",
                arguments=["0", ".055", "0", "-0.4386448745",
                           "0", "0", "camera_link", "camera1_link"]
            ),
        ])
