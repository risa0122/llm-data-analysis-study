# 본 분석·모델링·검증 — 예비 결과

실행일: 2026년 11월 2일. 나이·성별·지역 지표를 포함해 처음 실행한 예비 모델 결과다. 교육 자료의 시점 제약 때문에 실무 배치용 사전 예측 성능이 아닌 **사후 연구용 비교**로 해석한다.

## 1. 분석 질문과 변수

고객·계약·지역 정보를 고려한 뒤에도 보험금 비용이 다음 해 이탈 예측에 추가 가치를 갖는가?

- M0: 가입 기간 2개·보험료·상품·채널, 총 5개.
- M1: M0 + 나이·성별 + 지역 소득·교육·인구 규모·보험 가입 밀도, 총 18개.
- M2: M1 + 기준연도 보험금 비용, 총 19개.
- S1/S2: M1/M2에서 2021년 교육 지표 6개를 제외한 민감도 분석.

전체 컬럼은 [변수 구성](../docs/variable_specification.md)과 [실행 설정](analysis_results.json)에 있다. 종속변수는 다음 해 lapse 1 또는 3이며 ID·미래 종료일·다음 해 정보는 입력에서 제외했다.

## 2. 분석 방법과 검증 설계

2017년 정보→2018년 이탈로 개발하고 2018년 정보→2019년 이탈로 평가했다. 개발 내부는 계약 단위 75:25 분할이며 같은 계약이 양쪽에 겹치지 않음을 검증했다. 설정은 사전에 고정하고 평가 결과를 보고 튜닝하지 않았다.

로지스틱 회귀는 C=1, 최대 2,000회 반복, 수치 표준화와 범주 원핫 인코딩을 사용했다. 랜덤 포레스트는 트리 100개, 최대 깊이 12, 잎 최소 30개, max_features=sqrt다. 결측 대체·표준화·인코딩은 각 학습 구간에만 적합했다. 시드 20261102를 사용했다.

AP와 ROC-AUC를 함께 보고한다. AP의 기준이 되는 평가연도 이탈 비율은 11.28%다. M0/M1/M2와 S1/S2는 같은 대상에서 비교했다. 같은 계약을 함께 재표집한 paired bootstrap 200회로 성능 차이의 탐색적 95% 구간을 계산했다. 이 구간은 고정된 예측의 평가 표본 변동만 반영하며 재학습 변동은 포함하지 않는다.

## 3. 실제 평가 결과

| algorithm          | features                         |     n |   lapse_rate |     AP |   ROC_AUC |
|:-------------------|:---------------------------------|------:|-------------:|-------:|----------:|
| LogisticRegression | M0_contract                      | 59831 |       0.1128 | 0.1774 |    0.6319 |
| LogisticRegression | M1_personal_region               | 59831 |       0.1128 | 0.1704 |    0.6329 |
| LogisticRegression | M2_plus_claims                   | 59831 |       0.1128 | 0.1711 |    0.6343 |
| LogisticRegression | S1_without_education             | 59831 |       0.1128 | 0.1710 |    0.6337 |
| LogisticRegression | S2_without_education_plus_claims | 59831 |       0.1128 | 0.1716 |    0.6351 |
| RandomForest       | M0_contract                      | 59831 |       0.1128 | 0.1831 |    0.6402 |
| RandomForest       | M1_personal_region               | 59831 |       0.1128 | 0.1989 |    0.6659 |
| RandomForest       | M2_plus_claims                   | 59831 |       0.1128 | 0.2018 |    0.6758 |
| RandomForest       | S1_without_education             | 59831 |       0.1128 | 0.1985 |    0.6698 |
| RandomForest       | S2_without_education_plus_claims | 59831 |       0.1128 | 0.2029 |    0.6806 |

| comparison                                                               |   AP_delta | AP_95CI            |   ROC_AUC_delta | ROC_AUC_95CI      |
|:-------------------------------------------------------------------------|-----------:|:-------------------|----------------:|:------------------|
| LogisticRegression:M0_contract→M1_personal_region                        |    -0.0070 | [-0.0129, -0.0002] |          0.0010 | [-0.0039, 0.0057] |
| LogisticRegression:M1_personal_region→M2_plus_claims                     |     0.0007 | [0.0002, 0.0011]   |          0.0014 | [0.0008, 0.0021]  |
| LogisticRegression:S1_without_education→S2_without_education_plus_claims |     0.0007 | [0.0003, 0.0012]   |          0.0014 | [0.0008, 0.0020]  |
| RandomForest:M0_contract→M1_personal_region                              |     0.0158 | [0.0074, 0.0255]   |          0.0257 | [0.0203, 0.0319]  |
| RandomForest:M1_personal_region→M2_plus_claims                           |     0.0029 | [0.0009, 0.0050]   |          0.0099 | [0.0073, 0.0125]  |
| RandomForest:S1_without_education→S2_without_education_plus_claims       |     0.0045 | [0.0027, 0.0063]   |          0.0108 | [0.0081, 0.0136]  |

개발 내부 및 새 계약만의 보조 평가 결과:

| algorithm          | features                         | evaluation                 |     n |   lapse_rate |     AP |   ROC_AUC |
|:-------------------|:---------------------------------|:---------------------------|------:|-------------:|-------:|----------:|
| LogisticRegression | M0_contract                      | 2017_group_holdout         | 15350 |       0.1304 | 0.1882 |    0.6340 |
| LogisticRegression | M0_contract                      | 2018_to_2019_unseen_policy |  5938 |       0.2255 | 0.2716 |    0.5249 |
| LogisticRegression | M1_personal_region               | 2017_group_holdout         | 15350 |       0.1304 | 0.1901 |    0.6385 |
| LogisticRegression | M1_personal_region               | 2018_to_2019_unseen_policy |  5938 |       0.2255 | 0.2628 |    0.5537 |
| LogisticRegression | M2_plus_claims                   | 2017_group_holdout         | 15350 |       0.1304 | 0.1909 |    0.6392 |
| LogisticRegression | M2_plus_claims                   | 2018_to_2019_unseen_policy |  5938 |       0.2255 | 0.2633 |    0.5545 |
| LogisticRegression | S1_without_education             | 2017_group_holdout         | 15350 |       0.1304 | 0.1924 |    0.6436 |
| LogisticRegression | S1_without_education             | 2018_to_2019_unseen_policy |  5938 |       0.2255 | 0.2689 |    0.5635 |
| LogisticRegression | S2_without_education_plus_claims | 2017_group_holdout         | 15350 |       0.1304 | 0.1932 |    0.6442 |
| LogisticRegression | S2_without_education_plus_claims | 2018_to_2019_unseen_policy |  5938 |       0.2255 | 0.2690 |    0.5638 |
| RandomForest       | M0_contract                      | 2017_group_holdout         | 15350 |       0.1304 | 0.2072 |    0.6425 |
| RandomForest       | M0_contract                      | 2018_to_2019_unseen_policy |  5938 |       0.2255 | 0.2558 |    0.5535 |
| RandomForest       | M1_personal_region               | 2017_group_holdout         | 15350 |       0.1304 | 0.2252 |    0.6754 |
| RandomForest       | M1_personal_region               | 2018_to_2019_unseen_policy |  5938 |       0.2255 | 0.2764 |    0.5873 |
| RandomForest       | M2_plus_claims                   | 2017_group_holdout         | 15350 |       0.1304 | 0.2257 |    0.6820 |
| RandomForest       | M2_plus_claims                   | 2018_to_2019_unseen_policy |  5938 |       0.2255 | 0.2770 |    0.5865 |
| RandomForest       | S1_without_education             | 2017_group_holdout         | 15350 |       0.1304 | 0.2293 |    0.6825 |
| RandomForest       | S1_without_education             | 2018_to_2019_unseen_policy |  5938 |       0.2255 | 0.2695 |    0.5809 |
| RandomForest       | S2_without_education_plus_claims | 2017_group_holdout         | 15350 |       0.1304 | 0.2328 |    0.6901 |
| RandomForest       | S2_without_education_plus_claims | 2018_to_2019_unseen_policy |  5938 |       0.2255 | 0.2715 |    0.5846 |

새 계약만 평가한 대상은 5,938행이다. 기존 계약 대상과 모집단이 달라 그 성능을 전체 고객의 성능으로 바꾸어 해석하지 않는다.

## 4. 결과 관찰

- LogisticRegression: M0→M1 AP 0.1774→0.1704, M1→M2 AP 0.1704→0.1711. ROC-AUC는 각각 0.6319→0.6329→0.6343다.
- RandomForest: M0→M1 AP 0.1831→0.1989, M1→M2 AP 0.1989→0.2018. ROC-AUC는 각각 0.6402→0.6659→0.6758다.

## 5. 나의 해석과 판단

M0와 M1의 차이는 개인·지역 정보를 묶어 추가한 결과이며 성별이나 소득 한 변수의 효과가 아니다. M1과 M2의 차이로 보험금 비용의 추가 가치를 판단한다. 랜덤 포레스트에서는 개인·지역 추가 후 AP와 ROC-AUC가 모두 상승했지만 로지스틱 회귀의 AP는 낮아졌다. 변수를 추가하면 언제나 성능이 좋아진다고 볼 수 없다. AP와 ROC-AUC의 방향이 다르거나 차이의 구간이 0을 포함하면 일관된 개선이라고 단정하지 않는다. 이번 수치만으로 최적 모델을 확정하거나 평가연도에 맞춰 반복 튜닝하지 않는다.

## 6. 업무·분석적 의미

계약 정보에 고객·지역 특성을 함께 고려하는 비교 틀을 마련했다. 결과는 유지관리 대상 탐색을 위한 예비 근거이며, 이탈을 실제로 방어한 효과나 CSM 개선액이 아니다. 지역 지표를 개인의 소득·학력으로 읽지 않고 집단 간 성능과 오류도 후속 확인한다.

## 7. 한계와 추가 확인 사항

지역 교육 지표는 2021년 통계로 구축되어 2017·2018년 당시 이용할 수 없던 정보다. 이를 제외한 S1/S2도 나머지 지역 지표의 공표 시점과 보험금 비용 확정 시점이 입증되지 않아 과거 실무 성능으로 주장할 수 없다. 근거는 [원자료 논문 Methods](https://www.nature.com/articles/s41597-025-06372-z)다.

원본에는 유지 상태의 행에 미래 종료일이 기록되어 있어 날짜는 검증에만 사용했다. 이후 연도 평가에는 같은 계약이 일부 포함된다. 새 계약 보조 평가를 분리했지만 지역 분리 검증·외부 보험사 검증·보정도 평가는 남아 있다. 설명변수 간 상관 때문에 회귀계수나 중요도를 원인으로 해석하지 않는다. 보험료 대비 비용은 전체 수익성·CSM이 아니다.

지역 소득 지표 미확인 집단의 다음 해 이탈 비율은 2017년 기준 41.77%, 2018년 기준 7.69%로 달랐다. 모델이 지역의 경제적 특성보다 자료 누락의 패턴을 학습했을 가능성도 확인해야 한다. 이번 결과만으로 그 원인이나 각 변수의 기여를 특정하지 않는다.

## 8. 실행 및 재현

프로젝트 폴더에서 다음을 실행한다. 원자료가 없으면 먼저 기존 다운로드 코드를 실행한다.

```bash
python -m pip install -r requirements.txt
python docs/check_source_data.py
python docs/run_revised_analysis.py
python docs/render_revised_reports.py
```

버전·시드·변수·검증 결과는 analysis_results.json, 전체 성능은 metrics.csv에 기록했다. 개인별 예측이나 원자료 행은 공개 산출물에 저장하지 않았다. 모델 학습과 평가에 최종 연도 결과를 사용했으므로 이후 변경 사항은 이 평가 결과를 이미 확인했다는 점을 기록해야 한다.
