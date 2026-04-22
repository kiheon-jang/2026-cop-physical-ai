# 사용 스킬 목록 (Skills)

> 이 프로젝트에서 AI 에이전트가 사용하는 OpenClaw 스킬 목록입니다.  
> 각 스킬 파일은 `agent/skills/` 폴더에 복사되어 있습니다.

---

## 사용 스킬

| 스킬 이름 | 용도 | 파일 |
|-----------|------|------|
| `gsk-vm-email-send` | VM 이메일 발송 (일일 보고) | [gsk-vm-email-send.md](./gsk-vm-email-send.md) |
| `gsk-shared` | gsk CLI 공통 인증/플래그 | [gsk-shared.md](./gsk-shared.md) |
| `gsk-web-search` | 최신 기술 리서치 검색 | [gsk-web-search.md](./gsk-web-search.md) |
| `gsk-crawler` | 논문/문서 URL 크롤링 | [gsk-crawler.md](./gsk-crawler.md) |

---

## 핵심 사용 패턴

### 이메일 발송 (일일 보고)

```bash
# 스킬: gsk-vm-email-send
gsk vm_email send "recipient@example.com" \
  -s "제목" \
  -b "$HTML_BODY" \
  -f $OPENCLAW_VM_NAME
```

- `-f $OPENCLAW_VM_NAME` 필수 — 없으면 발신자 오류
- `-b` 에 HTML 문자열 직접 전달 가능
- 수신자는 VM allowlist 등록 필요 (현재 3명 등록 완료)

### 웹 검색 (리서치 초안)

```bash
# 스킬: gsk-web-search
gsk search "ACT vs Diffusion Policy 2026 benchmark"
gsk search "Isaac Lab SO-ARM101 tutorial"
```

### 웹 크롤링 (논문/문서)

```bash
# 스킬: gsk-crawler
gsk crawl "https://arxiv.org/abs/2304.13705"
gsk crawl "https://github.com/huggingface/lerobot" --render_js
```

---

## 스킬 원본 경로 (VM)

```
~/.openclaw/workspace/skills/gsk-vm-email-send/SKILL.md
~/.openclaw/workspace/skills/gsk-shared/SKILL.md
~/.openclaw/workspace/skills/gsk-web-search/SKILL.md
~/.openclaw/workspace/skills/gsk-crawler/SKILL.md
```
