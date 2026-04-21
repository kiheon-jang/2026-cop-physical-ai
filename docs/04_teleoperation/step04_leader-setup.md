---
created: 2026-02-04 07:50
tags: 
aliases: []
---
https://huggingface.co/docs/lerobot/so101





현재 연결되어있는 usb 장비를 확인하기 위해 명령어를 실행 후, 제거하면 확인됨, 다시 꽂기


```
lerobot-find-port


Remove the USB cable from your MotorsBus and press Enter when done.

The port of this MotorsBus is '/dev/tty.usbmodem5AE60537131'
Reconnect the USB cable.
(lerobot) ➜  lerobot git:(main) ✗




```


Leader 모터 셋업 : 이순서대로 셋업이 필요함

| Leader-Arm Axis     | Motor | Gear Ratio |
|---------------------|-------|------------|
| Base / Shoulder Pan | 1     | 1 / 191    |
| Shoulder Lift       | 2     | 1 / 345    |
| Elbow Flex          | 3     | 1 / 191    |
| Wrist Flex          | 4     | 1 / 147    |
| Wrist Roll          | 5     | 1 / 147    |
| Gripper             | 6     | 1 / 147    |

```
lerobot-setup-motors --teleop.type=so101_leader --teleop.port=/dev/tty.usbmodem5AE60537131
```


```
(lerobot) ➜  ~ lerobot-setup-motors --teleop.type=so101_leader --teleop.port=/dev/tty.usbmodem5AE60537131
objc[12109]: Class AVFFrameReceiver is implemented in both /Users/deois/miniforge3/envs/lerobot/lib/python3.10/site-packages/av/.dylibs/libavdevice.61.3.100.dylib (0x10f5bc3a8) and /Users/deois/miniforge3/envs/lerobot/lib/python3.10/site-packages/cv2/.dylibs/libavdevice.61.3.100.dylib (0x1150f03a8). This may cause spurious casting failures and mysterious crashes. One of the duplicates must be removed or renamed.
objc[12109]: Class AVFAudioReceiver is implemented in both /Users/deois/miniforge3/envs/lerobot/lib/python3.10/site-packages/av/.dylibs/libavdevice.61.3.100.dylib (0x10f5bc3f8) and /Users/deois/miniforge3/envs/lerobot/lib/python3.10/site-packages/cv2/.dylibs/libavdevice.61.3.100.dylib (0x1150f03f8). This may cause spurious casting failures and mysterious crashes. One of the duplicates must be removed or renamed.
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
(lerobot) ➜  ~
```


```
lerobot-calibrate --teleop.type=so101_leader --teleop.port=/dev/tty.usbmodem5AE60537131 --teleop.id=hdel_iot_01_leader_arm
```


```
(lerobot) ➜  ~ lerobot-calibrate --robot.type=so101_follower --robot.port=/dev/tty.usbmodem5AE60537131 --robot.id=hdel_iot_01_leader_arm
objc[12474]: Class AVFFrameReceiver is implemented in both /Users/deois/miniforge3/envs/lerobot/lib/python3.10/site-packages/cv2/.dylibs/libavdevice.61.3.100.dylib (0x10215c3a8) and /Users/deois/miniforge3/envs/lerobot/lib/python3.10/site-packages/av/.dylibs/libavdevice.61.3.100.dylib (0x11cab43a8). This may cause spurious casting failures and mysterious crashes. One of the duplicates must be removed or renamed.
objc[12474]: Class AVFAudioReceiver is implemented in both /Users/deois/miniforge3/envs/lerobot/lib/python3.10/site-packages/cv2/.dylibs/libavdevice.61.3.100.dylib (0x10215c3f8) and /Users/deois/miniforge3/envs/lerobot/lib/python3.10/site-packages/av/.dylibs/libavdevice.61.3.100.dylib (0x11cab43f8). This may cause spurious casting failures and mysterious crashes. One of the duplicates must be removed or renamed.
INFO 2026-02-23 21:02:43 calibrate.py:76 {'robot': {'calibration_dir': None,
           'cameras': {},
           'disable_torque_on_disconnect': True,
           'id': 'hdel_iot_01_leader_arm',
           'max_relative_target': None,
           'port': '/dev/tty.usbmodem5AE60537131',
           'use_degrees': False},
 'teleop': None}
INFO 2026-02-23 21:02:43 follower.py:106 hdel_iot_01_leader_arm SOFollower connected.
INFO 2026-02-23 21:02:43 follower.py:123
Running calibration of hdel_iot_01_leader_arm SOFollower
Move hdel_iot_01_leader_arm SOFollower to the middle of its range of motion and press ENTER....
Move all joints except 'wrist_roll' sequentially through their entire ranges of motion.
Recording positions. Press ENTER to stop...

-------------------------------------------
-------------------------------------------
NAME            |    MIN |    POS |    MAX
shoulder_pan    |    775 |   2070 |   3162
shoulder_lift   |    677 |    965 |   2967
elbow_flex      |    883 |   3084 |   3084
wrist_flex      |    822 |   2326 |   3137
gripper         |    120 |   2045 |   3918
Calibration saved to /Users/deois/.cache/huggingface/lerobot/calibration/robots/so_follower/hdel_iot_01_leader_arm.json
INFO 2026-02-23 21:04:06 follower.py:230 hdel_iot_01_leader_arm SOFollower disconnected.
(lerobot) ➜  ~
```