---
created: 2026-01-14 10:29
tags: 
aliases: []
status: HISTORICAL — 초기 기획 문서 (2026-01-14 작성)
---

> ⚠️ **이 문서는 초기 기획 단계(2026-01)의 요구사항입니다.** 현재(2026-05-01) 기준으로 일부 내용은 진화했습니다:
> - **시뮬레이터**: IsaacSim → **MuJoCo 3.x** (Phase 0~2 메인) + Isaac Lab (차년도)
> - **자동화 플랫폼**: 외부 클라우드 → **Hermes Agent (로컬 Mac Mini M5)**
> - **현재 활성 계획**: [`research/simulation/PHASE_ROADMAP.md`](../../research/simulation/PHASE_ROADMAP.md) 참조
>
> 이 문서는 **역사 기록**으로 보존됩니다. 신규 에이전트는 PHASE_ROADMAP.md 와 AGENT_PROCESS.md 를 우선 참조하세요.

---

사내 CoP 학습조직을 진행 하려고해 준비과정 및 상세 Action Plan 과 도달하려고하는 목표 등을 아래의 간단하게 리서치한 내용을 바탕으로 준비해줘

---
Physical AI 관련되어 CoP 학습을 진행하고 구체적으로 업무에 활용할 수 있는 프로젝트를 실시 한다.

- 1.VLA에 대한 이해
- 2.LeRobot 프로젝트에 대한 확인
- 3. Soarm
	- 하드웨어 준비
	- 기본 인퍼런스
	- 모방 학습 
	- 인퍼런스
- 4. 시뮬레이션 환경에서의 강화학습
	-  IsaacSim 기반 시뮬레이션 환경 구축
	- soarm 및 환경 모델링 반영
	- 강화학습 진행
	- 인퍼런스 진행
- 5. 5단계는 2가지 Option 에 대한 결정 하여 진행함
	- LeKiwi
	- XLeRobot 
- 6. CoP 정리

- 필요 하드웨어
	- 로봇팔을 위한 하드웨어
	- 인퍼런스를 위한 하드웨어
	- 모델학습을 위한 하드웨어

- 소프트웨어
	- 모델학습
	- IsaacSim
	- 인퍼런스

- 학습을 통한 목표
	- 1단계 : 물체의 이동
	- 2단계 : PCB 제품의 리셋과 DIP S/W 조정
	- 3단계 : PCB의 RS232 포트에 HHT(Hand Held Terminal) 꽂기

- 현재 갖고있는 하드웨어
	- nvidia orin nano super
	- raspberry pi 5

- 예상되는 하드웨어
	- 학습
	- 카메라


Soarm : 로봇팔 만
https://github.com/TheRobotStudio/SO-ARM100


LeKiwi : 이동체 까지 
https://github.com/SIGRobotics-UIUC/LeKiwi?tab=readme-ov-file


XLeRobot : 이동체 인데 먼가 더 함
https://xlerobot.readthedocs.io/en/latest/index.html


---
링크 : 구매 및 자료

https://shop.wowrobo.com/

https://velog.io/@choonsik_mom/Leisaac-LeRobot-Gr00t-IsaacSim%EC%9C%BC%EB%A1%9C-%EC%9E%85%EB%AC%B8%ED%95%98%EB%8A%94-VLA-Finetuning

