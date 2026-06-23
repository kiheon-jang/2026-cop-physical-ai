# 시뮬 grasp closed-loop 해법 확보 + 크론 핸드오프 — 2026-06-23

> Phase 1 W4. 6-22 grasp 근본원인을 재규명·정정하고, closed-loop 해법으로 sim grasp를 **0% → 88%/75%** 로 살림.
> 무인 크론이 이어받을 수 있게 데이터 수집기를 closed-loop expert로 교체(진행중).

## 1. 근본원인 재규명 (6-22 결론 정정)

6-22 문서의 "공차/서보 토크가 벽" 결론은 **부정확**. 다각 실측으로 반증:
- **토크 아님**: 팔 forcerange ±6Nm(실측 4배)에서도 open-loop grasp 0/8.
- **개구폭 아님**: 스톡 그리퍼 손끝 개구 ~94mm. 50mm 큐브는 ~53%만 점유(여유 충분). 6-22의 "53.7mm 초정밀공차"는 오측.
- **접촉모델 아님**: condim 3/4/6 + 마찰 상향 전부 0/8.
- **진짜 원인 = 단일 회전조의 닫힘 호(arc) 스윕 + open-loop expert.** 가동조가 경첩 회전이라 닫을 때 손끝이 호를 그려 자유 큐브를 30~60mm 쳐냄. 고정궤적 open-loop는 한 번 밀리면 복구 불가.
- **실물 대조**: 실물 SO-ARM101은 텔레오퍼레이션(사람 closed-loop)으로 3~5cm 물체를 바닥에서 잘 잡음 → 하드웨어/객체크기 문제 아님, **제어방식(open vs closed-loop) 차이**.

하드웨어 확인: 레포 BOM + 옵시디언 빌드기록상 **표준 SO-ARM101 단일 회전조 그리퍼**(평행조 아님). Follower 서보 = 12V STS3215-C018(≈2.94Nm 스톨). 시뮬 기본 1.5Nm는 12V보다 낮음.

## 2. closed-loop 해법 (확보)

`scripts/_grasp_closedloop.py` — visual servoing + graded close + re-grasp:
- 평패드 씬(scene_grasp_pads.xml = so101_grasp_calib.xml, 양 조 평패드 마찰2.0) 필수(끝선 접촉 → 면압).
- 매 step 큐브 ground-truth xpos 추종(TCP 재중심), 점진 닫힘(grip_q≈0.13까지만), 위+베이스쪽 곡선 들기, 실패 시 재시도.
- **실측: 30mm 큐브 8위치 88%(FORCE6) / 75%(FORCE3=12V 팔로워 실스펙) / 0%(open-loop).**
- 50mm는 TCP/grasp z 별도 보정 필요(미적용).

## 3. 4갈래 탐색 결론 (데이터 확보 경로)

| 갈래 | 결론 |
|---|---|
| ① closed-loop sim | 30mm 88% 실증. 자동 sim 데이터 생성기로 채택 |
| ② 공개 데이터셋 | SO-101 pick-place 실물 데모 ~130ep 공개(svla_so101 50/xinjiehu 60/ud-smart 20, Apache2.0). 부트스트랩용 |
| ③ 실물 우선 | LeRobot 합의=contact-rich 실물 우선. pick-place 정공법이나 6월 실물수집 미예정 |
| ④ 자동 sim 생성 | 방법A=closed-loop(cron화 가능). RL(B) 3~5일 |

**핵심 판단**: sim의 결정적 가치는 pick-place가 아니라 **Phase 3+ RS232 sub-mm 정밀삽입**(실물로 수천번 위험·비현실 → sim RL 필수). pick-place는 실물이 빠르나 6월엔 실물수집 없으니 **6월 = sim 트랙(closed-loop 자동수집) 메인.**

## 4. 크론 핸드오프 (진행중 → 무인 야간 태스크)

`samples/training/sim_data_collector.py` 를 closed-loop expert로 교체 중:
- 씬=scene_grasp_pads.xml, 큐브 30mm, **forcerange 3.0(12V faithful)**, closed-loop 정책.
- **성공 시연만 저장**(lift≥40mm 필터) — 기존엔 실패도 저장하던 게 버그.
- CLI(--root/--episodes) 유지, headless 렌더, LeRobot 포맷.

→ 완료 후 크론 야간 루프: **closed-loop 자동수집 → ACT 재학습(nohup) → `render_act_rollout.py` rollout 측정.** open-loop PICK_PLACE_POSES 폐기.

## 5. 크론 밖 (사람 트랙, 6월 미예정)
- 실물 텔레오퍼레이션 72ep 수집(③) — 사람 필요라 크론 불가. Phase 2(7월) 일정.
- Orin Nano 배포(SSH 확보 시) — 미해결.

관련 메모리: grasp-rootcause-correction / grasp-sim-strategy / model-selection. 정정 상세는 2026-06-22_grasp-task-root-cause.md 상단.
