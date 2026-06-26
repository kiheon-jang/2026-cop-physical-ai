---
id: magazines
title: "보고용 자료"
order: 7
menu_route: magazines
screenshot: magazines.png
category: 핵심
---
## 기능명세
<!-- slide title="보고용 자료 — 개요" -->

보고용 자료 화면(`view-magazines`)은 Obsidian에 작성된 월별 활동보고서를 대시보드 안에 임베드해 보여주는 화면이다. 인쇄(⌘P) 친화 레이아웃.

**헤더**
제목: "보고용 자료". 부제(`mag-sub`): "Obsidian 월별 활동보고서. 카드 클릭 시 본문 펼침. 인쇄(⌘P) 친화."

**월별 카드 목록 (report-picker)**
`build_monthly_reports()`가 `~/Documents/second-brain/03 Areas/회사문서/CoP_PhysicalAI/CoP_PhysicalAI_YYYY-MM_활동보고서*.md` 파일을 스캔해 반환한 목록에서 월별 카드를 생성. 같은 월에 복수 파일이 있으면 최신 mtime 파일 1건만 노출. 월 역순 정렬.

각 카드에 표시:
- 월(YYYY-MM) 레이블
- 보고서 제목(`first_h1()` 추출)
- 발췌 텍스트(`excerpt`, 최대 400자)
- 파일명

<!-- slide title="본문 영역 · FORM-1 지원" screenshot="" -->

**본문 영역 (report-body)**
카드를 클릭하면 `report-body` 영역에 보고서 본문 전체가 마크다운 렌더링되어 펼쳐진다. 클릭 전에는 "위 카드를 클릭하면 본문이 펼쳐집니다."라는 안내만 표시된다.

**FORM-1 지원**
보고서 파일에 YAML frontmatter가 있으면(`_parse_frontmatter()` 처리) `form` 필드로 emit되어 대시보드 폼 양식 렌더러가 처리한다. frontmatter가 없으면 `body_md` 마크다운을 `renderMarkdown()`으로 변환해 표시한다.

<!-- slide title="데이터 출처 · 상호작용" screenshot="" -->

**데이터 출처**: `build_monthly_reports()`. 소스 파일은 Obsidian PARA vault의 `03 Areas/회사문서/CoP_PhysicalAI/` 디렉토리. `build.py` 실행 환경(로컬 Mac Mini)에서만 파일 접근 가능. 파일이 없으면 화면은 빈 상태.

**상호작용**
- 월별 카드 클릭 → 본문 펼침.
- 한 번에 하나의 보고서만 본문 영역에 표시.
- 인쇄: ⌘P(macOS) 또는 브라우저 인쇄. `report-body` 영역이 인쇄 친화 스타일로 적용됨.

## 사용가이드
<!-- slide title="사용가이드 — 개요" -->

보고용 자료는 월별 활동보고서를 대시보드에서 바로 읽을 수 있는 화면입니다. Obsidian에서 작성한 보고서를 이곳에서 확인하고 인쇄할 수 있습니다.

**사용 방법**
1. 화면 위쪽에 월별 카드가 나열됩니다(예: 2026-06 · 활동보고서 2026년 6월).
2. 보고 싶은 월의 카드를 클릭하면 아래 본문 영역에 전체 보고서가 펼쳐집니다.
3. 여러 카드를 차례로 클릭해 월별 보고서를 비교할 수 있습니다.

<!-- slide title="인쇄 · 문제 해결" screenshot="" -->

**인쇄 방법**
보고서를 펼친 상태에서 ⌘P(Mac) 또는 Ctrl+P(Windows)를 누르면 인쇄 친화적 형태로 출력됩니다.

**보고서가 안 보인다면**
이 화면은 Obsidian의 `CoP_PhysicalAI` 폴더에 보고서 파일이 있어야 표시됩니다. 보고서를 먼저 Obsidian에서 작성하고 저장하면, 다음 자동 빌드(매일 23:30) 이후 이 화면에 나타납니다.
