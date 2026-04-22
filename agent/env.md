# 환경 설정 (Environment)

> 이 문서는 다른 AI 에이전트가 이 프로젝트를 이어받을 때 필요한 **모든 환경 정보**를 담고 있습니다.

---

## VM 정보

| 항목 | 값 |
|------|-----|
| **VM 이름** | `$OPENCLAW_VM_NAME` (환경변수로 참조) |
| **Public IP** | `104.210.221.70` |
| **Provider FQDN** | `xaqwer-6ffab8b1-6148-vm.azure.gensparkclaw.com` |
| **User Domain** | `ookixght.gensparkclaw.com` |
| **OS** | Linux (Azure, Ubuntu) |
| **Shell** | bash |
| **작업 홈** | `/home/work/` (passwordless sudo) |
| **워크스페이스** | `/home/work/.openclaw/workspace/` |

---

## GitHub 설정

| 항목 | 값 |
|------|-----|
| **레포 URL** | `https://github.com/kiheon-jang/2026-cop-physical-ai` |
| **계정** | `kiheon-jang` |
| **인증 방식** | `gh` CLI (사전 로그인 완료) |
| **로컬 경로** | `/home/work/.openclaw/workspace/2026-cop-physical-ai` |

### Git Push 전 반드시 실행

```bash
git remote set-url origin https://$(gh auth token)@github.com/kiheon-jang/2026-cop-physical-ai.git
```

### 외부 클론 시 (크론 isolated 세션 등)

```bash
git config --global url."https://$(gh auth token)@github.com/".insteadOf "https://github.com/"
git clone https://github.com/kiheon-jang/2026-cop-physical-ai.git /tmp/cop-repo \
  || (cd /tmp/cop-repo && git pull)
cd /tmp/cop-repo
```

---

## 이메일 설정

| 항목 | 값 |
|------|-----|
| **발신자 주소** | `xaqwer@genspark.email` |
| **발송 CLI** | `gsk vm_email send` |
| **from 플래그** | `-f $OPENCLAW_VM_NAME` (반드시 포함) |

### 수신자 목록 (allowlist 등록 완료)

| 이름 | 이메일 |
|------|--------|
| 장기헌 (CoP 리더) | `xaqwer@gmail.com` |
| 금인수 | `insoo.kum@hyundaielevator.com` |
| 장기헌(현대) | `giheon.jang@hyundaielevator.com` |

### 발송 명령어 예시

```bash
gsk vm_email send "xaqwer@gmail.com" \
  -s "[CoP Physical AI] 제목" \
  -b "$HTML_OR_TEXT_BODY" \
  -f $OPENCLAW_VM_NAME
```

> ⚠️ **주의**: `-f $OPENCLAW_VM_NAME` 없이 보내면 발신자가 잘못 지정될 수 있습니다.

---

## 웹 서비스

| 서비스 | URL | 설명 |
|--------|-----|------|
| 결정 폼 | `https://ookixght.gensparkclaw.com/decisions.html` | 팀원 기술결정 입력 폼 |
| 메일 미리보기 | `https://ookixght.gensparkclaw.com/mail-preview.html` | 메일 템플릿 확인용 |
| 정적 파일 루트 | `/var/www/html/` | Caddy가 서빙 (caddy 유저 권한) |

### Caddy 설정 파일

```
/etc/caddy/conf.d/custom.caddy
```

```caddy
ookixght.gensparkclaw.com {
    root * /var/www/html
    file_server
    encode gzip
}
```

> 파일 수정 후 반영: `sudo systemctl reload caddy`

---

## 하드웨어 (물리 로봇)

| 항목 | 값 |
|------|-----|
| **로봇 모델** | SO-ARM101 (Leader + Follower) |
| **Robot ID** | `hdel_iot_01` |
| **Follower 포트** | `/dev/tty.usbmodem5AE60573201` |
| **Leader 포트** | `/dev/tty.usbmodem5AE60537131` |
| **모터** | Feetech STS3215 × 6 |
| **컴퓨터** | NVIDIA Orin Nano Super + Raspberry Pi 5 |
| **카메라** | 웹캠 2개 (Top + Gripper) |

> ⚠️ 하드웨어는 VM에서 직접 제어 불가. 팀원이 현장에서 LeRobot 명령어로 조작.

---

## 주요 CLI 도구

| 도구 | 용도 | 설치 위치 |
|------|------|----------|
| `gsk` | 웹검색, 이미지생성, 이메일 발송 | pre-installed |
| `gh` | GitHub API 호출, 인증 | pre-installed |
| `openclaw` | 크론 관리, 세션 | pre-installed |
| `python3` | 스크립트 실행 | pre-installed |
| `caddy` | HTTPS 정적 서빙 | pre-installed |

---

## OpenClaw 크론 플랫폼 주의사항

> ⚠️ **크론은 OpenClaw 플랫폼에 등록된 Job입니다.**  
> 다른 AI 도구(Claude Code, Codex 등)에서는 자동 실행되지 않습니다.  
> 새 플랫폼으로 이전 시 → [cron-jobs.md](./cron-jobs.md) 참조하여 수동 재등록 필요.

### 크론 관리 명령어

```bash
openclaw cron list                    # 전체 목록
openclaw cron run <jobId>             # 즉시 실행
openclaw cron update <jobId> [opts]   # 수정
openclaw cron remove <jobId>          # 삭제
```
