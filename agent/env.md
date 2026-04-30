# 환경 설정 (env.md)

> 이 문서는 다른 AI 에이전트가 이 프로젝트를 이어받을 때 필요한 **모든 환경 정보**를 담고 있습니다.
> **최종 업데이트**: 2026-05-01 (Mac Mini M5 / Hermes Agent 환경)

---

## 머신 정보

| 항목 | 값 |
|------|-----|
| **머신** | Mac Mini M5 16GB (사용자 소유) |
| **OS** | macOS (Apple Silicon ARM64) |
| **Shell** | zsh |
| **사용자 홈** | `/Users/markmini/` |
| **워크스페이스** | `/Users/markmini/Documents/dev/` |
| **로컬 레포** | `/Users/markmini/Documents/dev/2026-cop-physical-ai` |
| **자동화 에이전트** | Hermes Agent (`~/.hermes/`, 24/7 가동) |
| **메인 모델** | Claude Code → NVIDIA NIM 라우팅 (smart_model_routing) |
| **보조 모델** | Gemini 2.5 Flash (간단한 요청용, 무료 RPM 15) |

> ⚠️ **레거시 환경 제거**: OpenClaw Azure VM (104.210.221.70, /home/work/.openclaw/workspace/) 은 2026-04-29부로 폐기됨.

---

## GitHub 설정

| 항목 | 값 |
|------|-----|
| **레포 URL** | `https://github.com/kiheon-jang/2026-cop-physical-ai` |
| **계정** | `kiheon-jang` |
| **인증 방식** | `gh` CLI (사전 로그인 완료) |
| **로컬 경로** | `/Users/markmini/Documents/dev/2026-cop-physical-ai` |

### Git push 전 반드시 실행

```bash
git config --global url."https://$(gh auth token)@github.com/".insteadOf "https://github.com/"
```

### 외부 동작 (크론 등 isolated 세션) 시

```bash
cd /Users/markmini/Documents/dev/2026-cop-physical-ai
git pull origin main
# 작업 수행
git add -A
git commit -m "..."
git push origin main
```

---

## Obsidian Vault

| 항목 | 값 |
|------|-----|
| **Vault 경로** | `~/Documents/second-brain/` |
| **AI Wiki (쓰기 가능)** | `~/Documents/second-brain/00_AI_Wiki/` |
| **CoP 폴더** | `~/Documents/second-brain/00_AI_Wiki/CoP_PhysicalAI/` |
| **월별 폴더** | `~/Documents/second-brain/00_AI_Wiki/CoP_PhysicalAI/2026-MM/` |

> 매일 23:00, 23:30 크론이 GitHub와 Obsidian Vault를 동시 갱신.

---

## 이메일 설정

| 항목 | 값 |
|------|-----|
| **발송 방식** | `scripts/daily-report/generate_daily_report.py` (Hermes 자동 실행) |
| **메일 템플릿** | `docs/01_overview/mail-template.md`, `docs/01_overview/mail-template.html` |
| **수신자 (3명)** | `xaqwer@gmail.com`, `insoo.kum@hyundaielevator.com`, `giheon.jang@hyundaielevator.com` |

> ⚠️ **레거시 제거**: `gsk vm_email send` 명령어는 OpenClaw 전용. 더 이상 사용하지 않음.

### 수신자 상세

| 이름 | 이메일 |
|------|--------|
| 장기헌 (CoP 리더, 본인) | `xaqwer@gmail.com` |
| 금인수 | `insoo.kum@hyundaielevator.com` |
| 장기헌 (회사) | `giheon.jang@hyundaielevator.com` |

---

## 하드웨어 (물리 로봇 — Mac Mini와 별도)

| 항목 | 값 |
|------|-----|
| **로봇 모델** | SO-ARM101 (Leader + Follower) |
| **Robot ID** | `hdel_iot_01` |
| **Follower 포트** | `/dev/tty.usbmodem5AE60573201` (실기 옆 머신 기준) |
| **Leader 포트** | `/dev/tty.usbmodem5AE60537131` |
| **모터** | Feetech STS3215 × 6 (Follower 12V), STS3215 × 5 (Leader 7.4V) |
| **추론 머신** | NVIDIA Orin Nano Super (실기 옆) |
| **운영 보조** | Raspberry Pi 5 |
| **카메라** | 웹캠 2개 (Top + Gripper, 실기 옆 머신에 연결) |

> ⚠️ Mac Mini는 시뮬+학습 전담. 실기는 별도 머신(Orin Nano)에서 추론.
> 실기 카메라 캘리브레이션값은 `agent/external-dependencies.md` 의 외부 의존 항목으로 관리.

---

## 시뮬레이터 환경 (Mac Mini)

| 항목 | 값 |
|------|-----|
| **시뮬레이터** | MuJoCo 3.x (Apple Silicon 네이티브) |
| **모델** | TheRobotStudio SO-ARM100/101 MJCF |
| **모델 URL** | `https://github.com/TheRobotStudio/SO-ARM100` |
| **Python** | 3.12 + uv |
| **프레임워크** | HuggingFace LeRobot |
| **렌더링** | `mujoco.Renderer` (Apple Metal/OpenGL 백엔드) |
| **카메라** | 시뮬 가상 카메라 2대 (`<camera mode="fixed">`, `<camera>` 그리퍼 attach) |

설치:
```bash
cd /Users/markmini/Documents/dev/2026-cop-physical-ai
uv pip install mujoco
git clone https://github.com/TheRobotStudio/SO-ARM100.git ~/dev/so-arm100-models
```

---

## 주요 CLI 도구

| 도구 | 용도 | 설치 |
|------|------|------|
| `gh` | GitHub API 호출, 인증 | brew |
| `hermes` | Hermes Agent CLI | uv tool install |
| `python3` | 스크립트 실행 | brew (3.12) |
| `uv` | Python 패키지 관리 | brew |
| `mujoco` | 시뮬레이터 (Python 패키지) | uv pip install |
| `git` | 버전 관리 | macOS 내장 |

---

## Hermes Agent 운영

> **크론은 Hermes Agent (Mac Mini M5)에서 자동 관리됩니다.**

### 크론 관리

```bash
# 게이트웨이 상태 확인
launchctl list | grep hermes

# 크론 목록 (jobs.json 직접 확인)
cat ~/.hermes/cron/jobs.json | python3 -m json.tool

# 또는 hermes CLI
hermes cron list
```

### 설정 파일

- 메인 설정: `~/.hermes/config.yaml`
- 환경변수: `~/.hermes/.env`
- 크론 작업: `~/.hermes/cron/jobs.json`
- 로그: `~/.local/logs/hermes-*.log`

### 권한

- macOS Full Disk Access: Terminal에 부여 (필요시)
- Touch ID sudo: `/etc/pam.d/sudo_local` 에 `auth sufficient pam_tid.so`
- Hermes config: `terminal.sudo_password: ""` (passwordless 시도)

---

## 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-04-21 | 최초 작성 (OpenClaw Azure VM 기준) — 레거시 |
| 2026-04-29 | OpenClaw → Hermes Agent (Mac Mini M5) 마이그레이션 |
| 2026-05-01 | env.md 전면 재작성. Mac Mini 환경, MuJoCo 시뮬, Obsidian Vault 경로 추가. gsk/openclaw 레거시 명령어 제거 |
