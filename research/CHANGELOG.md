# 리서치 갱신 이력 (CHANGELOG.md)

> 리서치 파일의 생성, 검수 통과, 갱신, 삭제 이력을 추적합니다.

---

## 형식

```
### YYYY-MM-DD
- ✅ [확정] <파일명> — drafts/ → latest-tech/ 이동
- 🔄 [갱신] <파일명> — 내용 최신화
- 🗑️ [삭제] <파일명> — 이유
- 📋 [초안] <파일명> — drafts/ 생성
```

---

## 이력

### 2026-05-01
- 🛠 [의사결정] 시뮬레이터 최종 확정: **MuJoCo 3.x** (Phase 0~2 메인) + Isaac Lab (Phase 3+, 차년도 별도 GPU 서버)
  - 사유: Mac Mini M5 (Apple Silicon)에서 Isaac Lab 미지원
- 🤖 [구조] 자동화 플랫폼: OpenClaw → Hermes Agent (로컬 Mac Mini, 2026-04-29 마이그레이션 후 시뮬 트랙으로 재구성)
- 🔄 [구조] 크론 4개 prompt 전체 재작성 (요일별 주제 순환 폐기 → PHASE_ROADMAP.md 기반 단계별 점진 구축)
  - 신규 ID: 9ad85007cf27, 85d322d3b37c, fb6d7cb26650, 0b1d4a7b2bf7
  - 폐기 ID: dc257031, b2e623a4, dcbf84a5, ed5aff22, 20ee15d4
- 📁 [구조] 신규 폴더: research/simulation/, agent/research-log/, agent/report-evidence/, ~/Obsidian/00_AI_Wiki/CoP_PhysicalAI/
- 📋 [신설] research/simulation/PHASE_ROADMAP.md — Phase 0~5 단계별 로드맵 (5월~10월)
- 📋 [신설] research/simulation/00_kickoff.md — Phase 0 W1 킥오프
- 📋 [신설] agent/external-dependencies.md — 외부 의존 / 사용자 수동 작업 누적
- 📧 [개편] 메일 [4-A] 외부 의존 섹션 신설 (사용자 수동 작업 매일 노출)
- 🗂️ [구조] 보고용 트랙 ↔ 실제 연구 트랙 분리 (월별 계획서는 그대로 유지, 시뮬은 선행)

### 2026-04-29
- 🤖 [마이그레이션] OpenClaw → Hermes Agent (Mac Mini M5 24/7 로컬 운영) 완료
- 🔧 [정리] fcc-proxy 배제, NVIDIA NIM 직결 라우팅
- 📝 [업데이트] AGENT_PROCESS.md 플랫폼 표기 (OpenClaw → Hermes)

### 2026-04-22
- 📋 [초안] 2026-04-22_sim2real-gap-techniques.md — Sim2Real 격차 해소 최신 기법 (Digital Cousins, Sim2Real-VLA, RL Co-Training, PACE, lerobot-sim2real)

### 2026-04-21
- 📁 [구조] research/drafts/ 폴더 신설 (초안 보관용)
- 📁 [구조] research/latest-tech/ 확정본 전용으로 용도 명확화
- 📁 [구조] research/decisions/ 결정 로그 폴더 신설
- 📋 [초안] 리서치 자동화 시작 — 매일 23:00 크론으로 drafts/ 에 초안 생성 예정
- 📋 [초안] 2026-04-21_isaac-lab-sim-rl-trends.md — Isaac Lab/Isaac Sim 강화학습 최신 동향 (v2.3.x → 3.0, Isaac Sim 6.0 EAR)
