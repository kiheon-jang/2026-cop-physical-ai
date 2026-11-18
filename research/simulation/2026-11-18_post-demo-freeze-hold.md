# 동결 유지 (신규 시뮬 작업 없음) — 2026-11-18 (수, 시연 D+18)

## 한 일
- 드라이버 결과 문서화: STAGE=완료/유지, `episodes_rs232` 100ep · 최종 성공률 0.6 (목표 0.50). 재수집·재학습·재측정 없음(드라이버 담당).
- 로드맵 잔여 `[ ]` 확인. **오늘 시뮬로 수행할 항목 없음**, 코드·MJCF 변경 없음.
  - 169 Orin 배포 / 나머지 보류·이관·외부 의존: 규칙상 건너뜀.
  - 985 pptx 활동현장 이미지: `site_image:` 사용자 입력 대기. `[ ]` 유지.
  - 991 리허설: 사람이 하는 작업. 시뮬 대상 아님. `[ ]` 유지.

## 검증
동결 무결성 재검증(비파괴):

| 항목 | 값 |
|---|---|
| `data/episodes_rs232/meta/info.json` | total_episodes=100 / total_frames=16093 |
| 모델 락 `act_rs232_sim/epoch_0041/model.safetensors` | 335,947,896 B · Sep 18 02:42 |
| 마커 | target=`data/episodes_rs232`(`.next` 없음) · trained_on=`episodes_rs232:1789546321` · measured=`episodes_rs232:1789666953` · pending 없음 |
| `rollout_summary_rs232.json` | success_rate 0.6 · full_rate 0.5 · median_lift 9.66mm · measured_at 2026-09-18T23:02 |
| sim sanity `sim/assets/rs232_unplug_scene.xml` | nq=7 nu=6 ncam=3 · MuJoCo 3.8.0 · Renderer 240×320 **14.73 / 16.09 / 16.36 ms/frame** |

렌더 외 수치는 11-17 과 동일. 렌더 1세트는 기준선(14.4~15.0ms), 2·3세트는 16.1~16.4ms 로 기준선 위(11-06 1차 16.2~17.8ms 와 비슷한 범위). 23:00 부하 평균 4.97/4.50/4.46. 1회 측정이라 회귀 판단 안 함 — 23:30 sim-test 재측정으로 확인.

측정 조건: warmup 5 뒤 50프레임 × 3세트, 정지 상태, camera 0. 11-13~11-17과 같은 방식. 측정 스크립트 `logs/simtest_20261118_freeze_check.py` 실행 후 삭제.

스크린샷 없음(시각 산출물 불변). 동결 상태 확인이며 성공률 재추정 아님.

## 다음 단계와의 연결
- 시뮬 실행 가능 `[ ]` 0개 상태 지속. 다음 사이클은 **사용자 결정**: 11월 로드맵 신설 후 `logs/cop_dataset_target.next` 전환, 또는 마커 삭제로 재수집.
- 시연(10-31) 실시 여부·991 리허설 결과는 저장소에 기록 없음. 사용자 확인 후 체크.
