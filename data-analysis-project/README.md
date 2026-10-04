# 건강보험 계약 이탈 특성 분석과 유지관리 우선순위 탐색

CSM 관리 업무의 계약 유지 문제와 연결해, 공개 건강보험 데이터로 이탈 특성과 사전 예측 가능성을 분석하는 개인 프로젝트다. 이탈 비율과 보험료 규모를 함께 비교해 우선 점검할 계약군을 탐색한다.

## 현재 프로젝트 진행 상태

2026년 10월 4일 기준, 1차 기획서 작성과 원자료 확보·기초 구조 확인을 마쳤다. 전처리 기준 확정과 본 분석·모델링은 이후 단계에서 수행한다.

## 단계별 산출물

- [1차 — 데이터분석 프로젝트 기획](01_proposal/01_proposal.md)
- 2차 — 데이터 확보·전처리·EDA: 진행 예정
- 3차 — 본 분석·모델링·검증: 진행 예정
- 4차 — 프로젝트 최종 완료: 진행 예정

## 데이터 출처 및 수집 방법

Lledó, J.; Espinosa Adamez, P.; Perez Gimenez, V. (2025), *Dataset of health insurance portfolio*, Mendeley Data, V4, [DOI: 10.17632/386vmj2tbk.4](https://doi.org/10.17632/386vmj2tbk.4), CC BY 4.0.

원자료와 변수 설명서를 공개 다운로드로 확보했다. 스페인 건강보험사의 2017~2019년 자료이며, 원본은 로컬에 보관한다.

- [데이터 구조 및 품질 확인 결과](docs/data_feasibility.json)
- [수집 파일 URL 및 체크섬](data/source_manifest.json)
- [생성형 AI 활용 및 검증 기록](docs/ai_usage.md)

## 실행 및 재현 방법

Python 3.12 환경을 권장한다. 저장소의 `data-analysis-project` 폴더에서 실행한다.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python docs/check_source_data.py
```

최초 실행 시 원자료 약 45.5MB와 변수 설명서를 다운로드한다. 파일 무결성·행과 열 수·결측·중복·연도 간 연결 결과는 `docs/data_feasibility.json`에 저장된다. 원본 행은 출력하지 않는다.

## 분석의 한계

스페인 단일 보험사의 연간 갱신형 건강보험 자료다. 국내 생명보험사도 건강보험을 취급하지만, 국내 장기 보장성 계약에 적용하려면 보장 내용·보험기간·갱신 구조의 차이를 검토해야 한다. 상태 코드는 연중·연말 종료를 구분하지만 자발적 해지와 미납 실효를 구분하지 않는다. 상담 이력이 없어 실제 이탈 방어 효과는 분석하지 않는다. 보험료 규모를 CSM이나 이익으로 해석하지 않으며, 실제 CSM 변동액은 산출하지 않는다.
