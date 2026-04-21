---
created: 2026-02-04 07:50
tags:
aliases: []
---

---

현재 연결되어있는 usb 장비를 확인하기 위해 명령어를 실행 후, 제거하면 확인됨, 다시 꽂기
```
lerobot-find-port
```


```
Remove the USB cable from your MotorsBus and press Enter when done.

The port of this MotorsBus is '/dev/tty.usbmodem5AE60573201'
Reconnect the USB cable.
```




Follower 확인

```
lerobot-setup-motors --robot.type=so101_follower --robot.port=/dev/tty.usbmodem5AE60573201
```

모터에 선을 1개씩만 연결하면서 해야함
```
(lerobot) ➜  lerobot git:(main) ✗ lerobot-setup-motors --robot.type=so101_follower --robot.port=/dev/tty.usbmodem5AE60573201
Connect the controller board to the 'gripper' motor only and press enter.
'gripper' motor id set to 6
Connect the controller board to the 'wrist_roll' motor only and press enter.
'wrist_roll' motor id set to 5
Connect the controller board to the 'wrist_flex' motor only and press enter.
'wrist_flex' motor id set to 4
Connect the controller board to the 'elbow_flex' motor only and press enter.
'elbow_flex' motor id set to 3
Connect the controller board to the 'shoulder_lift' motor only and press enter.
'shoulder_lift' motor id set to 2
Connect the controller board to the 'shoulder_pan' motor only and press enter.
'shoulder_pan' motor id set to 1
(lerobot) ➜  lerobot git:(main) ✗
```

 캘리브레이션
``` 
lerobot-calibrate --robot.type=so101_follower --robot.port=/dev/tty.usbmodem5AE60573201 --robot.id=hdel_iot_01_follower_arm
```


```
(lerobot) ➜  lerobot git:(main) ✗ lerobot-calibrate --robot.type=so101_follower --robot.port=/dev/tty.usbmodem5AE60573201 --robot.id=hdel_iot_01_follower_arm
INFO 2026-01-31 17:36:59 calibrate.py:76 {'robot': {'calibration_dir': None,
           'cameras': {},
           'disable_torque_on_disconnect': True,
           'id': 'hdel_iot_01_follower_arm',
           'max_relative_target': None,
           'port': '/dev/tty.usbmodem5AE60573201',
           'use_degrees': False},
 'teleop': None}
INFO 2026-01-31 17:36:59 follower.py:106 hdel_iot_01_follower_arm SOFollower connected.
INFO 2026-01-31 17:36:59 follower.py:123
Running calibration of hdel_iot_01_follower_arm SOFollower
Move hdel_iot_01_follower_arm SOFollower to the middle of its range of motion and press ENTER....
Move all joints except 'wrist_roll' sequentially through their entire ranges of motion.
Recording positions. Press ENTER to stop...

-------------------------------------------
NAME            |    MIN |    POS |    MAX
shoulder_pan    |    672 |    677 |   3168
shoulder_lift   |      0 |   2441 |   4095
elbow_flex      |      0 |   2055 |   4095
wrist_flex      |    549 |   1397 |   2834
gripper         |    795 |    813 |   2383

```

보정을 하면 파일이 생성됨
/Users/deois/.cache/huggingface/lerobot/calibration/robots/so_follower

```
(lerobot) ➜  so_follower pwd
/Users/deois/.cache/huggingface/lerobot/calibration/robots/so_follower
(lerobot) ➜  so_follower ls -al
total 8
drwxr-xr-x@ 3 deois  staff   96  2  1 09:41 .
drwxr-xr-x@ 3 deois  staff   96  1 31 17:15 ..
-rw-r--r--@ 1 deois  staff  911  2  1 07:23 hdel_iot_01_follower_arm.json
(lerobot) ➜  so_follower

(lerobot) ➜  so_follower cat hdel_iot_01_follower_arm.json
{
    "shoulder_pan": {
        "id": 1,
        "drive_mode": 0,
        "homing_offset": -1408,
        "range_min": 476,
        "range_max": 2701
    },
    "shoulder_lift": {
        "id": 2,
        "drive_mode": 0,
        "homing_offset": 719,
        "range_min": 0,
        "range_max": 4095
    },
    "elbow_flex": {
        "id": 3,
        "drive_mode": 0,
        "homing_offset": -890,
        "range_min": 0,
        "range_max": 4095
    },
    "wrist_flex": {
        "id": 4,
        "drive_mode": 0,
        "homing_offset": 1676,
        "range_min": 635,
        "range_max": 2954
    },
    "wrist_roll": {
        "id": 5,
        "drive_mode": 0,
        "homing_offset": 1219,
        "range_min": 0,
        "range_max": 4095
    },
    "gripper": {
        "id": 6,
        "drive_mode": 0,
        "homing_offset": 1391,
        "range_min": 2032,
        "range_max": 3486
    }
}%
(lerobot) ➜  so_follower
```



---
캘리브레이션 다시 진행

```
(lerobot) ➜  ~ lerobot-calibrate --robot.type=so101_follower --robot.port=/dev/tty.usbmodem5AE60573201 --robot.id=hdel_iot_01_follower_arm
objc[18844]: Class AVFFrameReceiver is implemented in both /Users/deois/miniforge3/envs/lerobot/lib/python3.12/site-packages/cv2/.dylibs/libavdevice.61.3.100.dylib (0x1064383a8) and /Users/deois/miniforge3/envs/lerobot/lib/python3.12/site-packages/av/.dylibs/libavdevice.61.3.100.dylib (0x11c8903a8). This may cause spurious casting failures and mysterious crashes. One of the duplicates must be removed or renamed.
objc[18844]: Class AVFAudioReceiver is implemented in both /Users/deois/miniforge3/envs/lerobot/lib/python3.12/site-packages/cv2/.dylibs/libavdevice.61.3.100.dylib (0x1064383f8) and /Users/deois/miniforge3/envs/lerobot/lib/python3.12/site-packages/av/.dylibs/libavdevice.61.3.100.dylib (0x11c8903f8). This may cause spurious casting failures and mysterious crashes. One of the duplicates must be removed or renamed.
INFO 2026-03-14 10:39:02 calibrate.py:82 {'robot': {'calibration_dir': None,
           'cameras': {},
           'disable_torque_on_disconnect': True,
           'id': 'hdel_iot_01_follower_arm',
           'max_relative_target': None,
           'port': '/dev/tty.usbmodem5AE60573201',
           'use_degrees': True},
 'teleop': None}
INFO 2026-03-14 10:39:02 follower.py:105 hdel_iot_01_follower_arm SOFollower connected.
Press ENTER to use provided calibration file associated with the id hdel_iot_01_follower_arm, or type 'c' and press ENTER to run calibration:  c
INFO 2026-03-14 10:39:09 follower.py:122
Running calibration of hdel_iot_01_follower_arm SOFollower
Move hdel_iot_01_follower_arm SOFollower to the middle of its range of motion and press ENTER....
Move all joints except 'wrist_roll' sequentially through their entire ranges of motion.
Recording positions. Press ENTER to stop...

-------------------------------------------
-------------------------------------------
NAME            |    MIN |    POS |    MAX
shoulder_pan    |    744 |   2004 |   2756
shoulder_lift   |    916 |   2820 |   3361
elbow_flex      |    756 |   2163 |   2934
wrist_flex      |    946 |   1213 |   3176
gripper         |   2027 |   2115 |   3458
Calibration saved to /Users/deois/.cache/huggingface/lerobot/calibration/robots/so_follower/hdel_iot_01_follower_arm.json
INFO 2026-03-14 10:40:34 follower.py:229 hdel_iot_01_follower_arm SOFollower disconnected.
(lerobot) ➜  ~
```