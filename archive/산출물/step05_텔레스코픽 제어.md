
```
lerobot-teleoperate --robot.type=so101_follower --robot.port=/dev/tty.usbmodem5AE60573201 --robot.id=hdel_iot_01_follower_arm --teleop.type=so101_leader --teleop.port=/dev/tty.usbmodem5AE60537131 --teleop.id=hdel_iot_01_leader_arm
```

```
(lerobot) ➜  lerobot git:(main) lerobot-teleoperate --robot.type=so101_follower --robot.port=/dev/tty.usbmodem5AE60573201 --robot.id=hdel_iot_01_follower_arm --teleop.type=so101_leader --teleop.port=/dev/tty.usbmodem5AE60537131 --teleop.id=hdel_iot_01_leader_arm
INFO 2026-03-14 12:15:24 eoperate.py:211 {'display_compressed_images': False,
 'display_data': False,
 'display_ip': None,
 'display_port': None,
 'fps': 60,
 'robot': {'calibration_dir': None,
           'cameras': {},
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
INFO 2026-03-14 12:15:24 so_leader.py:78 hdel_iot_01_leader_arm SOLeader connected.
INFO 2026-03-14 12:15:24 follower.py:105 hdel_iot_01_follower_arm SOFollower connected.
Teleop loop time: 16.67ms (60 Hz)
^CINFO 2026-03-14 12:15:39 o_leader.py:155 hdel_iot_01_leader_arm SOLeader disconnected.
(lerobot) ➜  lerobot git:(main)
```