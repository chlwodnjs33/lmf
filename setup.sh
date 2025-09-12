#!/bin/sh

cd /media/wego/DISK_IMG
unzip -d ~/wego_ws/src/ limo_application-master.zip
unzip -d ~/wego_ws/src/ limo_examples-master.zip
unzip -d ~/wego_ws/src/ yolov3-pytorch-ros-master.zip
unzip -d ~/ limo_start_shortcut.zip

cp CMakeCache.txt ~/wego_ws/build

cd ~/limo_start_shortcut && ./setup.bash

cd ~/wego_ws && catkin_make
