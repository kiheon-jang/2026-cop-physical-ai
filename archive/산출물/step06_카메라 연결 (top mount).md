

https://huggingface.co/docs/lerobot/cameras#setup-cameras

카메라 찾기

```
lerobot-find-cameras opencv
```


실행 시키면 현재 달려있는 카메라가 표시되고 스냅샷이 카메라당 한장씩 찍힘

./output/captured_images


```
(lerobot) ➜  ~ lerobot-find-cameras opencv
OpenCV: out device of bound (0-2): 3
OpenCV: camera failed to properly initialize!
[ WARN:0@3.185] global cap_ffmpeg_impl.hpp:1217 open VIDEOIO/FFMPEG: Failed list devices for backend avfoundation
OpenCV: out device of bound (0-2): 4
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 5
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 6
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 7
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 8
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 9
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 10
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 11
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 12
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 13
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 14
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 15
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 16
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 17
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 18
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 19
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 20
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 21
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 22
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 23
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 24
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 25
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 26
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 27
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 28
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 29
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 30
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 31
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 32
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 33
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 34
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 35
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 36
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 37
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 38
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 39
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 40
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 41
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 42
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 43
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 44
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 45
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 46
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 47
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 48
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 49
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 50
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 51
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 52
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 53
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 54
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 55
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 56
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 57
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 58
OpenCV: camera failed to properly initialize!
OpenCV: out device of bound (0-2): 59
OpenCV: camera failed to properly initialize!

--- Detected Cameras ---
Camera #0:
  Name: OpenCV Camera @ 0
  Type: OpenCV
  Id: 0
  Backend api: AVFOUNDATION
  Default stream profile:
    Format: 16.0
    Fourcc:
    Width: 1920
    Height: 1080
    Fps: 10.0
--------------------
Camera #1:
  Name: OpenCV Camera @ 1
  Type: OpenCV
  Id: 1
  Backend api: AVFOUNDATION
  Default stream profile:
    Format: 16.0
    Fourcc:
    Width: 1920
    Height: 1080
    Fps: 15.0
--------------------
Camera #2:
  Name: OpenCV Camera @ 2
  Type: OpenCV
  Id: 2
  Backend api: AVFOUNDATION
  Default stream profile:
    Format: 16.0
    Fourcc:
    Width: 1920
    Height: 1080
    Fps: 1.0
--------------------
ERROR:lerobot.scripts.lerobot_find_cameras:Failed to connect or configure OpenCV camera 1: OpenCVCamera(1) read failed (status=False).

Finalizing image saving...
Image capture finished. Images saved to outputs/captured_images
```


0 번이 설치한 카메라였음 
![[attachments/opencv_0.png]]

---
https://huggingface.co/docs/lerobot/il_robots

텔레스코픽에 인자 추가 

```
lerobot-teleoperate --robot.type=so101_follower --robot.port=/dev/tty.usbmodem5AE60573201 --robot.id=hdel_iot_01_follower_arm --teleop.type=so101_leader --teleop.port=/dev/tty.usbmodem5AE60537131 --teleop.id=hdel_iot_01_leader_arm --robot.cameras="{ front: {type: opencv, index_or_path: 0, width: 1920, height: 1080, fps: 30}}" --display_data=true
```


```
(lerobot) ➜  captured_images lerobot-teleoperate --robot.type=so101_follower --robot.port=/dev/tty.usbmodem5AE60573201 --robot.id=hdel_iot_01_follower_arm --teleop.type=so101_leader --teleop.port=/dev/tty.usbmodem5AE60537131 --teleop.id=hdel_iot_01_leader_arm --robot.cameras="{ front: {type: opencv, index_or_path: 0, width: 1920, height: 1080, fps: 30}}" --display_data=true
objc[36649]: Class AVFFrameReceiver is implemented in both /Users/deois/miniforge3/envs/lerobot/lib/python3.10/site-packages/cv2/.dylibs/libavdevice.61.3.100.dylib (0x1040b43a8) and /Users/deois/miniforge3/envs/lerobot/lib/python3.10/site-packages/av/.dylibs/libavdevice.61.3.100.dylib (0x1415cc3a8). This may cause spurious casting failures and mysterious crashes. One of the duplicates must be removed or renamed.
objc[36649]: Class AVFAudioReceiver is implemented in both /Users/deois/miniforge3/envs/lerobot/lib/python3.10/site-packages/cv2/.dylibs/libavdevice.61.3.100.dylib (0x1040b43f8) and /Users/deois/miniforge3/envs/lerobot/lib/python3.10/site-packages/av/.dylibs/libavdevice.61.3.100.dylib (0x1415cc3f8). This may cause spurious casting failures and mysterious crashes. One of the duplicates must be removed or renamed.
INFO 2026-03-01 07:56:59 eoperate.py:201 {'display_compressed_images': False,
 'display_data': True,
 'display_ip': None,
 'display_port': None,
 'fps': 60,
 'robot': {'calibration_dir': None,
           'cameras': {'front': {'color_mode': <ColorMode.RGB: 'rgb'>,
                                 'fourcc': None,
                                 'fps': 30,
                                 'height': 1080,
                                 'index_or_path': 0,
                                 'rotation': <Cv2Rotation.NO_ROTATION: 0>,
                                 'warmup_s': 1,
                                 'width': 1920}},
           'disable_torque_on_disconnect': True,
           'id': 'hdel_iot_01_follower_arm',
           'max_relative_target': None,
           'port': '/dev/tty.usbmodem5AE60573201',
           'use_degrees': False},
 'teleop': {'calibration_dir': None,
            'id': 'hdel_iot_01_leader_arm',
            'port': '/dev/tty.usbmodem5AE60537131',
            'use_degrees': False},
 'teleop_time_s': None}
[2026-02-28T22:56:59Z INFO  re_grpc_server] Listening for gRPC connections on 0.0.0.0:9876. Connect by running `rerun --connect rerun+http://127.0.0.1:9876/proxy`
INFO 2026-03-01 07:56:59 so_leader.py:79 hdel_iot_01_leader_arm SOLeader connected.
INFO 2026-03-01 07:57:01 a_opencv.py:180 OpenCVCamera(0) connected.
INFO 2026-03-01 07:57:01 follower.py:106 hdel_iot_01_follower_arm SOFollower connected.
Teleop loop time: 32.04ms (31 Hz)
^CINFO 2026-03-01 07:57:31 o_leader.py:156 hdel_iot_01_leader_arm SOLeader disconnected.
INFO 2026-03-01 07:57:31 a_opencv.py:541 OpenCVCamera(0) disconnected.
(lerobot) ➜  captured_images
```


---
카메라 연결해서 보니깐 팔에 간섭때문에 시야가 안나오는거 같음
그리고 해상도가 너무 떨어짐, 알리에서 사면 안될거 같음 로지텍으로 하다 더사야할듯

![[attachments/Step06_카메라연결.mp4]]
![[attachments/opencv_0 1.png]]