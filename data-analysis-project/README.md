# 건강보험 계약 이탈과 보험금 비용 특성 분석

생명보험 계약 유지관리 업무와 연결해 스페인 공개 건강보험 자료의 이탈 특성을 분석한다. 나이·성별·계약·지역 사회경제 정보를 고려하고 보험금 비용의 추가 예측 가치를 비교한다.

## 현재 프로젝트 진행 상태

2026년 11월 6일, 로지스틱 회귀·랜덤 포레스트·XGBoost와 M0·M1·M2의 두 축 비교를 실행했다. 지역 교육 지표가 2021년 통계를 사용하므로 이번 결과는 사후 연구용이다. 당시 실무 예측 성능이나 이탈 방어 효과로 해석하지 않는다.

## 단계별 산출물

- [1차 — 데이터분석 프로젝트 기획](01_proposal/01_proposal.md)
- [2차 — 데이터 확보·전처리·EDA](02_data-eda/02_eda_report.md)
- [3차 — 예비 분석·모델링·검증](03_analysis-modeling/03_preliminary_results.md)
- 4차 — 최종 프로젝트: 진행 예정
- [변수 구성과 의미](docs/variable_specification.md)
- [알고리즘 × 변수 구성 비교](03_analysis-modeling/algorithm_feature_comparison.md)
- [IBEX 35 경제 상황 후보 변수](docs/ibex35_context.md)
- [변경 사항과 남은 확인](docs/change_log.md)
- [AI 활용 및 검증](docs/ai_usage.md)

## 데이터 출처 및 수집 방법

Lledó, Espinosa Adamez, Perez Gimenez, Dataset of health insurance portfolio, Mendeley Data V4, [DOI 10.17632/386vmj2tbk.4](https://doi.org/10.17632/386vmj2tbk.4), CC BY 4.0. 2017~2019년 228,711행·42열이다. 원자료는 로컬에 보관하며 공개 산출물은 집계값·코드·문서다. [수집 파일·체크섬](data/source_manifest.json).

## 실행 및 재현 방법

Python 3.12 환경에서 이 폴더를 기준으로 실행한다.

```bash
python -m pip install -r requirements.txt
python docs/check_source_data.py
python docs/run_revised_analysis.py
python docs/render_revised_reports.py
```

## 분석의 한계

개인 소득·학력은 없다. 지역 지표를 개인 속성으로 단정하지 않는다. 상태는 연중·연말 종료를 구분하며 해지·실효 사유를 구분하지 않는다. 보험금 비용·지역 지표의 시점, 외부 검증, 지역·집단별 오류 검토가 남아 있다. CSM 평가자료와 개입 이력이 없어 실제 CSM·방어 효과는 산출하지 않는다. 발표 준비와 개인 백업은 공개하지 않는다.
