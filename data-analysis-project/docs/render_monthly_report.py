"""월별 실험 결과를 표·문서로 정리한다. 예측 결과를 새로 만들지 않는다."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'03_analysis-modeling/monthly'

def main():
    audit=json.loads((OUT/'audit.json').read_text())
    scores=pd.read_csv(OUT/'metrics.csv')
    by_month=pd.read_csv(OUT/'metrics_by_month.csv')
    cohorts=pd.read_csv(OUT/'monthly_cohorts.csv')
    comparison=pd.read_csv(OUT/'ibex_monthly_comparison.csv')
    assert len(scores)==24 and len(by_month)==144
    assert scores.groupby('scope').n.nunique().eq(1).all()
    full=scores[scores.scope.eq('all_2019')]
    table=full.pivot(index='algorithm',columns='features',values='AP')
    table['M3-M2']=table.M3_IBEX-table.M2
    nondec=scores[scores.scope.eq('Jan_Nov_2019')].pivot(index='algorithm',columns='features',values='AP')
    month=by_month.groupby(['algorithm','features']).AP.mean().unstack()
    month['M3-M2']=month.M3_IBEX-month.M2
    comparison_summary=comparison.groupby('algorithm').agg(mean_monthly_AP_delta=('AP_delta_IBEX','mean'),
        positive_months=('AP_delta_IBEX',lambda v:int((v>0).sum())))
    table.to_csv(OUT/'ap_comparison.csv')
    month.to_csv(OUT/'mean_monthly_ap.csv')
    baselines=pd.read_csv(OUT/'baselines.csv')
    summary=' / '.join(f"{a}: {row.M2:.6f} → {row.M3_IBEX:.6f} (차이 {row['M3-M2']:+.6f})" for a,row in table.iterrows())
    report=f'''# 월별 이탈 예비 분석과 IBEX 35 비교

실행일: 2026년 11월 6일

## 1. 분석 목적

본 연구 데이터 확보에 앞서 공개 보험 자료로 변수 구성과 알고리즘의 적용 절차를 점검한다. 고객·계약 기본정보, 유지 중 발생하는 행동 정보, 외부 금융시장 정보를 연결하고 IBEX 35 추가 전후의 예측 성능을 비교한다. 이번 결과는 본 연구의 결론이나 국내 보험사의 이탈 방어 효과가 아니다.

## 2. 월별 데이터 구성

한 행은 **월초 유지 중인 피보험 관계 하나의 해당 월 기록**이다. 종속변수는 당월 관계 종료 여부다. 전년도 말 유지 대상 중 다음 해 상태가 확인된 관계를 사용하고, 당해 신규 가입자는 포함하지 않는다. 종료한 관계는 이후 월부터 제외한다. 한 계약의 여러 피보험자는 서로 다른 관계다.

| 구분 | 학습 | 평가 |
|---|---|---|
| 이탈 관측 기간 | 2018년 1~12월 | 2019년 1~12월 |
| 보험 변수 기준 | 2017년 연간 정보 | 2018년 연간 정보 |
| 연초 피보험 관계 | 63,486개 | 59,831개 |
| 관계×월 관측 수 | {audit['train_rows']:,}행 | {audit['test_rows']:,}행 |
| 이탈 관계 | 9,924개 | 6,746개 |
| IBEX 독립 관측 시점 | 전월 수익률 12개 | 전월 수익률 12개 |

예: 2018년 4월 초 유지 대상에 2017년 계약·고객·보험금 정보와 **2018년 3월 IBEX 수익률**을 연결해 4월 이탈을 예측한다. 연간 보험 변수는 해당 예측 연도 안에서 고정한다. 월별 보험료·청구 이력이 새로 확보된 것은 아니다. 종료일은 위험집단 및 정답 구성에만 사용한다. 실제 전년도 비용 확정 시점은 확인되지 않았으므로 당시 운영 환경을 완전히 재현한 결과는 아니다.

## 3. 변수 그룹과 비교 조건

| 그룹 | 현재 사용 정보 | 아직 없는 정보 |
|---|---|---|
| 계약 특성 | 전년도 가입 기간·계약 유지 기간·보험료·상품·채널 | 납입 방법, 월별 계약 변경 이력 |
| 고객 특성 | 전년도 나이·성별 | 개인 소득 |
| 지역 특성 | 지역 소득·교육·인구 규모·보험 가입 밀도 | 개인 속성으로 해석할 수 없음 |
| 고객 행동 | 전년도 연간 보험금 비용 | 월별 청구·지급, 연체·자동이체 해지·민원 |
| 설계사 접점 | 없음 | 접촉 빈도·마지막 접촉일·담당 설계사 이탈 |
| 거시경제·금융시장 | 전월 IBEX 35 가격수익률 | 금리·실업률 등은 이번 실험 미사용 |
| 계절성 통제 | 달력 월 12개 원핫 변수 | 실무 갱신 예정일 이력 |

M0는 계약 정보, M1은 M0+고객·지역 정보, M2는 M1+보험금 비용, **M3는 M2+IBEX 35**다. 모든 구성에 같은 월 변수를 넣었다. IBEX는 `100 × (전월 종가 / 전전월 종가 − 1)`로 계산한다. 배당을 포함하지 않는다. 학습 구간에서 12개의 다른 값이 존재하며 **세 알고리즘 모두 실제 입력에 포함했다.**

로지스틱 회귀·랜덤 포레스트·XGBoost를 동일한 전체 학습·평가 대상과 시간 분할로 비교한다. 튜닝은 하지 않고 기존 실험의 설정을 고정했다. 전처리는 학습 자료에서만 적합한다. 같은 관계의 다른 월이 평가 자료에 등장할 수 있는 기존 계약 모니터링 설정이며 신규 고객 일반화 실험은 아니다. 구체적 변수·설정은 [실행 기록](audit.json)에 있다.

## 4. 알고리즘과 변수 구성별 결과

AP는 높을수록 좋다. 아래 값은 **2019년 관계×월 관측 전체**의 AP이며, 연간 예측의 AP와 직접 비교하지 않는다.

{table.to_markdown(floatfmt='.6f')}

**관찰:** {summary}. XGBoost에서는 소폭 상승했지만 로지스틱 회귀에서는 거의 같고 랜덤 포레스트에서는 하락했다.

**해석:** 추가 변수의 효과는 알고리즘별로 다를 수 있다. 값이 올랐더라도 IBEX가 이탈의 원인이라는 의미는 아니다.

**본 연구 시사점:** IBEX를 추가하면 일관되게 좋아진다는 결과는 아니다. 외부 지표를 실제 모델에 연결하고 추가 전후를 비교하는 절차를 확인했다. 본 연구 데이터에서는 더 긴 기간과 월별 행동 이력을 확보해 다시 평가한다.

학습 자료의 전체 이탈률만 예측한 기준선과, 학습 자료의 같은 달 이탈률만 적용한 기준선도 함께 계산했다. 평가 자료로 기준선을 추정하지 않았다.

{baselines[['baseline','scope','AP','ROC_AUC','Brier']].to_markdown(index=False,floatfmt='.6f')}

## 5. 연말 집중과 월별 재확인

2018년 이탈 9,924건 중 8,004건(80.65%), 2019년 6,746건 중 4,826건(71.54%)이 12월이다. 연중 종료와 연말 갱신 종료가 섞여 있으므로 전체 AP만으로 판단하지 않는다.

**1~11월 평가 AP:**

{nondec.to_markdown(floatfmt='.6f')}

**각 월 AP를 계산한 뒤 12개월을 동일 가중 평균한 값:**

{month.to_markdown(floatfmt='.6f')}

**IBEX 추가 후 월별 AP 변화:**

{comparison_summary.to_markdown(floatfmt='.6f')}

**관찰:** 전체 기간 AP와 월별 평균 AP는 집계 기준이 달라 수치가 다르다. 상세 수치는 [월별 평가](metrics_by_month.csv)와 [동일 월 차이](ibex_monthly_comparison.csv)에서 확인한다.

**해석:** 월 안에서 IBEX 값은 모든 관계에 동일하다. 특히 로지스틱 회귀에서는 월별 순위에 기여하지 않는 공통 절편 효과가 생길 수 있다. 2018년 한 해만 학습하므로 IBEX 변수는 월 원핫 변수의 선형 결합으로도 표현된다. 따라서 계절성과 구분되는 독립적인 거시경제 효과는 식별할 수 없다. 트리 모델의 변화도 12개 학습 월의 분할에 의존한다.

**본 연구 시사점:** 이번 비교는 연결·학습·평가 절차의 시험이다. 여러 해의 같은 달에 서로 다른 경제 상황이 반복되는 자료를 확보해야 추가 가치의 지속성을 검증할 수 있다. 개별 행을 독립 표본으로 간주한 유의성 검정은 수행하지 않았다.

## 6. 검증 및 한계

- ID·월 중복 0건, 관계별 연간 종료 최대 1회, 종료 후 관측 제외를 확인했다.
- 월별 이탈 합계가 기존 연간 코호트의 9,924건·6,746건과 일치한다.
- 보험 변수 기준연도와 IBEX 원천 월이 이탈 관측 기간보다 앞선다. 다만 정보의 실제 공표·확정 시점까지 입증한 것은 아니다.
- 다음 해 상태 미확인 1건·2건은 유지나 이탈로 임의 분류하지 않았다.
- 지역 변수의 사후 작성 문제는 기존 자료의 한계로 남는다. 나이·가입 기간도 전년도 측정값으로 사용하며 실제 월별 변화라고 해석하지 않는다.
- 관계 종료는 자발적 해지·실효·보험사 전체 고객 이탈과 동일하지 않다. CSM과 실제 방어 효과는 추정하지 않는다.
- 동일 학습 구간·평가 대상·설정을 사용했다. 이번 평가 결과를 보고 설정을 변경하지 않았다.
- 원자료·개별 패널·개별 예측값은 로컬에 보관하고 공개 문서에는 집계값만 포함한다.

## 7. 출처와 재현

보험 원자료: [Mendeley Data V4](https://doi.org/10.17632/386vmj2tbk.4), CC BY 4.0. IBEX: [BME 공식 월별 자료]({audit['source']}). BME 월 표기일은 월 식별자이며 해당 월 종가는 그 월이 끝난 후에만 사용한다. 2016~2019년 12월 값을 기존 연말 자료와 대조했다.

대조 중 기존 수기 입력의 2016년 말 지수 9,352.10을 **9,532.10**으로 정정했다. 2017년 연간 수익률도 7.40%에서 **5.37%**로 수정했다. 기존 연간 모델은 IBEX를 사용하지 않았으므로 해당 모델 성능에는 영향이 없다.

```bash
python docs/run_revised_analysis.py  # 보험 원자료 검증 캐시 준비
python docs/run_monthly_analysis.py
python docs/render_monthly_report.py
```

[월별 위험집단·이탈 집계](monthly_cohorts.csv) · [IBEX 월별 연결 값](ibex35_monthly.csv) · [전체 평가 지표](metrics.csv) · [실행 코드](../../docs/run_monthly_analysis.py)
'''
    (OUT/'monthly_results.md').write_text(report)
    print(table.to_string())

if __name__=='__main__':main()
