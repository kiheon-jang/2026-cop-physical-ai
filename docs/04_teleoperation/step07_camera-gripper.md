- 카메라를 2개를 같이 사용하는게 맞을거 같아.

```
lerobot-teleoperate \
  --robot.type=so101_follower \
  --robot.port=/dev/tty.usbmodem5AE60573201 \
  --robot.id=hdel_iot_01_follower_arm \
  --robot.cameras='{
    "gripper":{"type":"opencv","index_or_path":0,"width":640,"height":480,"fps":30},
    "top":{"type":"opencv","index_or_path":1,"width":640,"height":480,"fps":30}
  }' \
  --teleop.type=so101_leader \
  --teleop.port=/dev/tty.usbmodem5AE60537131 \
  --teleop.id=hdel_iot_01_leader_arm \
  --display_data=true
```

로그

```
(lerobot) ➜  lerobot git:(main) lerobot-teleoperate \
  --robot.type=so101_follower \
  --robot.port=/dev/tty.usbmodem5AE60573201 \
  --robot.id=hdel_iot_01_follower_arm \
  --robot.cameras='{
    "gripper":{"type":"opencv","index_or_path":0,"width":640,"height":480,"fps":30},
    "top":{"type":"opencv","index_or_path":1,"width":640,"height":480,"fps":30}
  }' \
  --teleop.type=so101_leader \
  --teleop.port=/dev/tty.usbmodem5AE60537131 \
  --teleop.id=hdel_iot_01_leader_arm \
  --display_data=true
INFO 2026-03-14 12:28:45 eoperate.py:211 {'display_compressed_images': False,
 'display_data': True,
 'display_ip': None,
 'display_port': None,
 'fps': 60,
 'robot': {'calibration_dir': None,
           'cameras': {'gripper': {'backend': <Cv2Backends.ANY: 0>,
                                   'color_mode': <ColorMode.RGB: 'rgb'>,
                                   'fourcc': None,
                                   'fps': 30,
                                   'height': 480,
                                   'index_or_path': 0,
                                   'rotation': <Cv2Rotation.NO_ROTATION: 0>,
                                   'warmup_s': 1,
                                   'width': 640},
                       'top': {'backend': <Cv2Backends.ANY: 0>,
                               'color_mode': <ColorMode.RGB: 'rgb'>,
                               'fourcc': None,
                               'fps': 30,
                               'height': 480,
                               'index_or_path': 1,
                               'rotation': <Cv2Rotation.NO_ROTATION: 0>,
                               'warmup_s': 1,
                               'width': 640}},
           'disable_torque_on_disconnect': True,
           'id': 'hdel_iot_01_follower_arm',
           'max_relative_target': None,
           'port': '/dev/tty.usbmodem5AE60573201',
           'use_degrees': True},
 'teleop': {'calibration_dir': None,
            'id': 'hdel_iot_01_leader_arm',
            'port': '/dev/tty.usbmodem5AE60537131',
            'use_degrees': True},
 'teleop_time_s': None}
INFO 2026-03-14 12:28:45 so_leader.py:78 hdel_iot_01_leader_arm SOLeader connected.
INFO 2026-03-14 12:28:47 a_opencv.py:179 OpenCVCamera(0) connected.
WARNING 2026-03-14 12:28:48 a_opencv.py:460 Error reading frame in background thread for OpenCVCamera(0): OpenCVCamera(0) read failed (status=False).
INFO 2026-03-14 12:28:51 a_opencv.py:179 OpenCVCamera(1) connected.
INFO 2026-03-14 12:28:51 follower.py:105 hdel_iot_01_follower_arm SOFollower connected.
Teleop loop time: 16.67ms (60 Hz)
---------------------------
NAME              |    NORM
shoulder_pan.pos  |   35.74
(lerobot) ➜  lerobot git:(main)
```


![[attachments/Pasted image 20260314123114.png]]