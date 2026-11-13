# 동결 유지 (신규 시뮬 작업 없음) — 2026-11-13 (금, 시연 D+13)

## 한 일
- 드라이버 결과 문서화: STAGE=완료/유지, `episodes_rs232` 100ep · 최종 성공률 0.6 (목표 0.50). 재수집·재학습·재측정 없음(드라이버 담당).
- 로드맵 잔여 `[ ]` 확인. **오늘 시뮬로 수행할 항목 없음**, 코드·MJCF 변경 없음.
  - 169 Orin 배포 / 나머지 보류·이관·외부 의존: 규칙상 건너뜀.
  - 985 pptx 활동현장 이미지: 스틸 준비 완료(11-02). 남은 일은 `site_image:` 입력(PARA 읽기전용, 사용자 직접). `[ ]` 유지.
  - 991 리허설: 사람이 하는 25분 계측. 시뮬 대상 아님. `[ ]` 유지.

## 검증
동결 무결성 재검증(비파괴):

| 항목 | 값 |
|---|---|
| `data/episodes_rs232/meta/info.json` | total_episodes=100 / total_frames=16093 |
| 모델 락 `act_rs232_sim/epoch_0041/model.safetensors` | 335,947,896 B · Sep 18 02:42 |
| 마커 | target=`data/episodes_rs232`(`.next` 없음) · trained_on=`episodes_rs232:1789546321` · measured=`episodes_rs232:1789666953` · pending 마커 없음 |
| `rollout_summary_rs232.json` | success_rate 0.6 · full_rate 0.5 · median_lift 9.66mm · measured_at 2026-09-18T23:02 |
| sim sanity `sim/assets/rs232_unplug_scene.xml` | nq=7 nu=6 ncam=3 · MuJoCo 3.8.0 · Renderer 240×320 **15.03 / 14.75 / 14.87 ms/frame** |

렌더 외 수치는 11-12 와 동일.

**렌더**: 14ms대 기준선 이틀째 유지(11-12 14.72~14.80ms). 측정 시점 부하 평균 4.02~4.18(1분), 11-12(3.9~4.0)와 비슷.

측정 조건: warmup 5 뒤 50프레임 × 3세트, 정지 상태(mj_step 없음), camera 0. 11-12와 같은 방식, 1회 실행.

스크린샷 없음. 시각 산출물이 바뀌지 않았다. 이 문서는 동결 상태 확인이고 성공률을 다시 추정한 것이 아니다.

## 다음 단계와의 연결
- 시뮬로 실행 가능한 `[ ]` 0개 상태가 이어진다. 다음 사이클은 **사용자 결정**이다: 11월 로드맵을 신설한 뒤 `logs/cop_dataset_target.next`로 전환하거나, 마커를 지워 재수집한다.
- 시연(10-31) 실시 여부와 991 리허설 결과는 저장소에 기록이 없다. 사용자 확인 후 체크한다.
