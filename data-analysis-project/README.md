# 보험계약 이탈 위험 분석과 유지관리 우선순위 탐색

생명보험 해지·실효 방지 업무 및 논문 주제와 연결하기 위한 공개 건강보험 데이터 예비 분석 프로젝트.

## 현재 상태

2026-10-04: 1차 기획 작성 및 공개 원자료 확보·기초 구조 확인 완료. 본 분석·모델 학습은 아직 수행하지 않았다. 스페인 건강보험 자료이며 국내 생명보험 결과로 일반화하지 않는다.

- [1차 제출 파일](01_proposal/01_proposal.md)
- [1차 발표 자료](01_proposal/01_presentation.pptx)
- [발표 대본·예상 질문·오늘 할 일](01_proposal/presentation_notes.md)
- [확보·구조 점검 결과](docs/data_feasibility.json)
- [출처와 파일 체크섬](data/source_manifest.json)
- [AI 활용·검증 기록](docs/ai_usage.md)

## 구성

```text
data-analysis-project/
├─ README.md
├─ requirements.txt
├─ 01_proposal/             # 제안서, 발표 자료, 발표 메모
├─ 02_data-eda/             # 다음 단계에서 작성
├─ 03_analysis-modeling/    # 다음 단계에서 작성
├─ 04_final/               # 다음 단계에서 작성
├─ data/                   # 출처 기록; 원본은 로컬에만 보관
├─ app/                    # 최종 결과 전달용, 선택 사항
└─ docs/                   # 데이터 확보 코드·검증·AI 활용 기록
```

## 데이터 확보 결과 재현

Python 3.12 환경을 권장한다. 저장소의 `data-analysis-project` 폴더에서 다음 명령을 실행한다. 개인 식별자나 원본 행은 출력하지 않으며, 데이터 다운로드·해시 검증·집계 점검만 수행한다.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python docs/check_source_data.py
```

최초 실행에는 네트워크 연결이 필요하며 원본 약 45.5MB와 변수 설명서를 다운로드한다. `data/raw/`와 가상환경은 Git에서 제외한다. 결과는 `docs/data_feasibility.json`에 저장된다. 원본이 바뀌면 기존 버전과 섞지 않고 버전·체크섬을 확인한다.

## 제출

LMS에는 아래 **제안서 파일 URL 하나**를 제출한다. 발표 파일은 보조 자료다.

https://github.com/risa0122/llm-data-analysis-study/blob/main/data-analysis-project/01_proposal/01_proposal.md

공식 1차 자료 제출일은 10월 5일이며 LMS의 정확한 마감 시각은 별도 확인한다. 제출 버튼 클릭과 접수 확인은 본인이 수행한다.

## 데이터 출처

Lledó, J.; Espinosa Adamez, P.; Perez Gimenez, V. (2025), *Dataset of health insurance portfolio*, Mendeley Data, V4, [doi:10.17632/386vmj2tbk.4](https://doi.org/10.17632/386vmj2tbk.4), CC BY 4.0. 본 프로젝트는 해당 파일을 집계·연결해 분석하며 원본 파일은 수정하지 않는다.
