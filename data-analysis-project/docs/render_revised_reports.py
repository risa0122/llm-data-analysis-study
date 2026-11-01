"""실제 실행 산출물에서 보고서·그래프·이식용 요약을 생성한다."""
from pathlib import Path
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
EDA=ROOT/'02_data-eda'
MODEL=ROOT/'03_analysis-modeling'

def md(df):
    return df.to_markdown(index=False,floatfmt='.4f')

def main():
    from add_ibex_context import main as add_ibex
    add_ibex()
    result=json.loads((MODEL/'analysis_results.json').read_text())
    metrics=pd.read_csv(MODEL/'metrics.csv')
    groups=pd.read_csv(EDA/'grouped_lapse.csv')
    costs=pd.read_csv(EDA/'claims_ratios.csv')
    cohorts=pd.read_csv(EDA/'cohorts.csv')
    quality=pd.read_csv(EDA/'variable_quality.csv')
    images=EDA/'images';images.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False})
    for col,label in [('age','Age'),('gender','Gender'),('C_GI','Area income percentile (general population)'),('C_H','Municipality population category')]:
        data=groups.loc[groups.variable.eq(col)].pivot(index='group',columns='feature_year',values='lapse_rate').sort_index()*100
        ax=data.plot.bar(figsize=(8,4),color=['#217565','#BA6C47'],rot=0)
        ax.set(xlabel=label,ylabel='Next-year lapse (%)',title='Observed rates; unadjusted group comparison')
        ax.set_ylim(0,max(25,float(data.max().max())*1.2))
        ax.legend(title='Feature year');plt.tight_layout()
        plt.savefig(images/f'{col}_lapse.png',dpi=160);plt.close()
    core=groups.loc[groups.variable.isin(['age','gender','C_GI','C_H']),['feature_year','variable','group','n','lapses','lapse_rate']]
    obs=groups.loc[groups.feature_year.eq(2018)].set_index(['variable','group'])
    observation=(f"2018년 기준 여성은 {obs.loc[('gender','F'),'lapse_rate']:.2%}, 남성은 {obs.loc[('gender','M'),'lapse_rate']:.2%}로 단순 이탈 비율이 비슷하다. "
                 f"연령대별로는 0~17세 {obs.loc[('age','0–17'),'lapse_rate']:.2%}, 60~69세 {obs.loc[('age','60–69'),'lapse_rate']:.2%}다. "
                 f"지역 소득 백분위 26~50 집단은 {obs.loc[('C_GI','P26–50'),'lapse_rate']:.2%}, 76~100 집단은 {obs.loc[('C_GI','P76–100'),'lapse_rate']:.2%}다. "
                 "연령·상품·계약 기간 등의 구성 차이를 통제하지 않은 비교다.")
    text=f'''# 데이터 확보·전처리·EDA

분석일: 2026년 11월 2일. 공개 건강보험 원본 V4를 다시 읽어 실행했다. 이번 결과는 10월 기획 이후 처음 수행한 예비 EDA다.

IBEX 35 연간 가격수익률을 경제 상황 후보 변수로 연결했다. [확보 결과·연도 연결·모델 적용 한계](../docs/ibex35_context.md). 스페인 주식시장 지표이며 글로벌 경제 전체를 대변하지 않는다.

## 1. 1차 이후 변경된 내용

계약 정보 외에 나이·성별과 지역 소득·교육·인구 규모·보험 가입 밀도를 포함했다. 지역 지표는 개인 소득이나 학력이 아니다. 정의는 [분석 변수 구성](../docs/variable_specification.md)에 정리했다.

## 2. 실제 데이터와 분석 범위

원자료는 228,711행·42열이다. 기준연도 유지 중인 피보험 관계를 다음 해와 연결했다. 미확인 기록은 이탈로 간주하지 않았다. 아래 이탈 비율은 0~1 단위다.

{md(cohorts)}

## 3. 데이터 품질 확인 및 처리 기준

원자료·설명서의 체크섬을 확인하고 ID·연도 중복 0건, 상태·종료일 불일치 {result['date_audit']['inconsistent_status_dates']}건을 확인했다. 유지 상태지만 이후 연도의 종료일을 가진 행은 {result['date_audit']['active_rows_with_future_termination_date']:,}건으로, 해당 날짜를 예측 변수에 넣으면 미래 정보가 들어갈 수 있어 제외했다.

{md(quality)}

지역 결측 행을 일괄 삭제하지 않는다. EDA에서 Unknown으로 구분하고 모델에서는 학습 자료의 중앙값·결측 표시 또는 범주형 Unknown으로 처리한다. 백분위 구간은 1~25, 26~50, 51~75, 76~100으로 고정했다. 보험료·보험 가입 밀도의 사분위 경계는 2017년 자료에서 정해 다음 해에도 적용했다. 모든 변수별 집계의 대상 수와 이탈 수가 원본 코호트와 일치하는지 검증했다.

## 4. 주요 EDA 결과

![연령대별 이탈 비율](images/age_lapse.png)

![성별 이탈 비율](images/gender_lapse.png)

![지역 소득 백분위별 이탈 비율](images/C_GI_lapse.png)

![거주 지자체 인구 규모별 이탈 비율](images/C_H_lapse.png)

{md(core)}

교육·보험 가입 밀도·상품·채널·가입 기간·보험료를 포함한 전체 집계는 [그룹별 결과](grouped_lapse.csv)에 있다. 각 변수는 같은 대상을 다른 기준으로 나눈 것이므로 변수 간 대상 수를 합산하지 않는다.

## 5. 결과 관찰

2017→2018 이탈 비율은 {cohorts.iloc[0].lapse_rate:.2%}, 2018→2019는 {cohorts.iloc[1].lapse_rate:.2%}다. 동일한 기간·대상 기준 안에서 연령·성별·지역 집단별 비율을 비교할 수 있다. 연도별 전체 이탈 비율이 달라 단순히 두 연도의 집단 비율 차이를 특정 속성의 효과라고 볼 수 없다.

{observation}

지역 소득 지표 C_GI 미확인 집단은 2017년 4,580건 중 1,913건(41.77%), 2018년 2,835건 중 218건(7.69%)이 다음 해 이탈했다. 결측 집단의 구성과 이탈 비율이 크게 달라 결측 표시가 안정적인 예측 신호인지 후속 확인이 필요하다. 이 차이의 발생 원인은 현재 확인되지 않았다.

이탈·유지 집단의 기준연도 보험료 대비 보험금 비용은 아래와 같다. 비율은 개인 비율의 평균이 아닌 집단 합계의 비율이며 0~1 단위다.

{md(costs)}

## 6. 나의 해석과 판단

개인·지역 정보를 제외한 계약 변수만으로는 집단의 구성 차이를 충분히 확인하기 어렵다. 따라서 개인·지역 특성을 함께 분석하되, 위 집단별 차이는 다른 변수를 통제하지 않은 관찰로 해석한다. 비용 비율의 연령·지역별 집계도 grouped_lapse.csv에 기록했지만, 고객·계약·지역을 동시에 통제한 이탈·유지 비용 차이는 아직 검증하지 않았다.

## 7. 업무·분석적 의미

연령과 거주 지역 특성을 포함해 유지관리 대상의 구성을 파악할 수 있다. 다만 지역 소득으로 개인의 납입 능력을 단정하거나 보험금 비용만으로 유지관리 우선순위를 정하지 않는다. 예측 추가 가치는 별도의 [예비 모델 결과](../03_analysis-modeling/03_preliminary_results.md)로 판단한다.

## 8. 한계와 추가 확인 사항

지역 교육 지표는 2021년 통계를 과거 계약 자료에 연결한 사후 지표다. 교육 수준과 이탈의 인과관계를 주장하지 않는다. 지역 결측, 지역 변수 간 상관, 관측 기간 차이, 같은 계약의 피보험자 간 의존성도 고려해야 한다. 원자료에 우편번호가 공개되지 않아 지역을 완전히 분리한 검증은 수행하지 못했다. 국내 생명보험, 해지·실효 원인, 실제 CSM·상담 효과로 일반화하지 않는다.

실행 코드: [run_revised_analysis.py](../docs/run_revised_analysis.py). 출처: [원자료 V4](https://data.mendeley.com/datasets/386vmj2tbk/4), [설명 논문](https://www.nature.com/articles/s41597-025-06372-z).
'''
    (EDA/'02_eda_report.md').write_text(text)
    main_metrics=metrics.loc[metrics.evaluation.eq('2018_to_2019_all')].drop(columns='evaluation')
    ci_rows=[]
    for name,v in result['paired_policy_bootstrap'].items():
        ci_rows.append({'comparison':name,'AP_delta':v['AP_delta'],'AP_95CI':f"[{v['AP_95CI'][0]:.4f}, {v['AP_95CI'][1]:.4f}]",'ROC_AUC_delta':v['ROC_AUC_delta'],'ROC_AUC_95CI':f"[{v['ROC_AUC_95CI'][0]:.4f}, {v['ROC_AUC_95CI'][1]:.4f}]"})
    ci=pd.DataFrame(ci_rows)
    model_text=f'''# 본 분석·모델링·검증 — 예비 결과

실행일: 2026년 11월 2일. 나이·성별·지역 지표를 포함해 처음 실행한 예비 모델 결과다. 교육 자료의 시점 제약 때문에 실무 배치용 사전 예측 성능이 아닌 **사후 연구용 비교**로 해석한다.

IBEX 35 수익률은 후보 변수·연도별 배경 자료로 추가했다. 학습 구간이 단일 연도여서 상수이므로 아래 모델에는 투입하지 않았으며 성능도 변경하지 않았다. [IBEX 35 검토](../docs/ibex35_context.md).

## 1. 분석 질문과 변수

고객·계약·지역 정보를 고려한 뒤에도 보험금 비용이 다음 해 이탈 예측에 추가 가치를 갖는가?

- M0: 가입 기간 2개·보험료·상품·채널, 총 5개.
- M1: M0 + 나이·성별 + 지역 소득·교육·인구 규모·보험 가입 밀도, 총 18개.
- M2: M1 + 기준연도 보험금 비용, 총 19개.
- S1/S2: M1/M2에서 2021년 교육 지표 6개를 제외한 민감도 분석.

전체 컬럼은 [변수 구성](../docs/variable_specification.md)과 [실행 설정](analysis_results.json)에 있다. 종속변수는 다음 해 lapse 1 또는 3이며 ID·미래 종료일·다음 해 정보는 입력에서 제외했다.

## 2. 분석 방법과 검증 설계

2017년 정보→2018년 이탈로 개발하고 2018년 정보→2019년 이탈로 평가했다. 개발 내부는 계약 단위 75:25 분할이며 같은 계약이 양쪽에 겹치지 않음을 검증했다. 설정은 사전에 고정하고 평가 결과를 보고 튜닝하지 않았다.

로지스틱 회귀는 C=1, 최대 2,000회 반복, 수치 표준화와 범주 원핫 인코딩을 사용했다. 랜덤 포레스트는 트리 100개, 최대 깊이 12, 잎 최소 30개, max_features=sqrt다. 결측 대체·표준화·인코딩은 각 학습 구간에만 적합했다. 시드 {result['seed']}를 사용했다.

AP와 ROC-AUC를 함께 보고한다. AP의 기준이 되는 평가연도 이탈 비율은 {cohorts.iloc[1].lapse_rate:.2%}다. M0/M1/M2와 S1/S2는 같은 대상에서 비교했다. 같은 계약을 함께 재표집한 paired bootstrap 200회로 성능 차이의 탐색적 95% 구간을 계산했다. 이 구간은 고정된 예측의 평가 표본 변동만 반영하며 재학습 변동은 포함하지 않는다.

## 3. 실제 평가 결과

{md(main_metrics)}

{md(ci)}

개발 내부 및 새 계약만의 보조 평가 결과:

{md(metrics.loc[~metrics.evaluation.eq('2018_to_2019_all')])}

새 계약만 평가한 대상은 {result['test_unseen_policy_n']:,}행이다. 기존 계약 대상과 모집단이 달라 그 성능을 전체 고객의 성능으로 바꾸어 해석하지 않는다.

## 4. 결과 관찰

'''
    for algo in ['LogisticRegression','RandomForest']:
        v=main_metrics.loc[main_metrics.algorithm.eq(algo)].set_index('features')
        model_text+=f"- {algo}: M0→M1 AP {v.loc['M0_contract','AP']:.4f}→{v.loc['M1_personal_region','AP']:.4f}, M1→M2 AP {v.loc['M1_personal_region','AP']:.4f}→{v.loc['M2_plus_claims','AP']:.4f}. ROC-AUC는 각각 {v.loc['M0_contract','ROC_AUC']:.4f}→{v.loc['M1_personal_region','ROC_AUC']:.4f}→{v.loc['M2_plus_claims','ROC_AUC']:.4f}다.\n"
    model_text+='''
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
'''
    (MODEL/'03_preliminary_results.md').write_text(model_text)
    notes=ROOT/'.local-presentation/presentation_notes.md'
    notes.write_text('''# 발표 준비 — 2026년 11월 2일 수정본

기존 10월 발표본은 당시 기획 기록이다. 현재 변수 구성과 실행 결과는 이 문서와 최신 슬라이드를 사용한다. 발표 자료는 GitHub에 업로드하지 않는다.

추가 설명: IBEX 35 연간 가격수익률은 스페인 시장의 배경 변수로 확보했다. 현 모델에서는 단일 학습 연도의 상수여서 투입하지 않았다. 슬라이드의 18개·19개 변수 수와 모델 성능은 실제 학습 기준이며 IBEX 35를 포함한 성능이 아니다.

## 1장. 프로젝트 주제 — 25초
생명보험 계약 유지관리 업무와 연결해 건강보험 이탈을 분석한다. 실제 자료는 스페인 건강보험이므로 국내 생명보험 결과라고 말하지 않는다.

## 2장. 핵심 분석 질문 — 40초
고객·계약·지역별 이탈 차이, 이탈·유지 집단의 과거 비용 특성, 보험금 비용의 추가 예측 가치라는 세 질문이다. 나이·성별과 지역 지표를 기존 설계에서 누락해 이번에 포함했다.

## 3장. 개인·계약 변수 — 40초
나이와 성별은 피보험자의 속성이다. 가입 기간은 피보험자와 계약 기준을 구분한다. 보험료는 고객이 낸 금액이며 상품·채널도 함께 사용한다. 다음 해 이탈 여부가 종속변수이고 식별자와 미래 종료일은 입력에서 제외한다.

## 4장. 지역 변수 — 45초
C_GI와 C_II는 지역 소득의 백분위로 실제 개인 소득이 아니다. 교육 지표도 개인 학력이 아닌 지역의 상대적 위치다. C_H는 지자체 인구 규모이며 IICIMUN과 IICIPROV는 해당 보험사의 지역 가입 밀도다. 교육 지표에 2021년 자료가 사용되어 당시 예측으로 해석할 수 없다는 한계가 있다.

## 5장. EDA 관찰 — 35초
'''+f'다음 해 상태를 확인한 대상은 63,486건과 59,831건이다. 이탈 비율은 각각 {cohorts.iloc[0].lapse_rate:.2%}, {cohorts.iloc[1].lapse_rate:.2%}다. 연령·성별·지역별 집계를 수행했으며 집단 차이가 원인을 증명하지는 않는다.\n'+'''
## 6장. 예비 모델 결과 — 50초
계약 변수만 사용한 M0, 고객·지역 정보를 더한 M1, 보험금 비용을 더한 M2를 비교했다. 2017년으로 학습하고 2018년 정보에 대한 다음 해 상태로 평가했다. 아래 실제 수치를 사용하되 사후 연구용 결과임을 먼저 밝힌다.

'''+md(main_metrics.loc[main_metrics.features.isin(['M0_contract','M1_personal_region','M2_plus_claims'])])+'''

## 7장. 결과 검증과 한계 — 35초
계약 단위 분할, 다음 해 연결, 날짜·상태 대조를 확인했다. 교육 지표를 뺀 모델도 비교했다. 다만 지역 지표 공표 시점, 비용 확정 시점, 외부 검증이 남아 있다. 현재 성능은 이탈 방어 효과나 CSM 개선액이 아니다.

## 8장. 향후 진행 계획 — 20초
지역 지표의 시점과 오류 사례, 고객·지역 집단별 성능을 더 확인한다. 예비 분석을 최종 결과로 과장하지 않고 실제 실행 근거와 한계를 함께 보고한다.

## 예상 질문

**왜 개인 속성을 추가했는가?** 기존 제외에 실증 근거가 부족했다. 고객·지역 구성을 함께 살펴보는 것이 질문에 더 적합해 수정했다.

**고객의 소득을 아는가?** 아니다. 거주 지역의 소득 백분위만 알 수 있다.

**미래 정보 문제가 해결됐는가?** 아니다. 직접적인 미래 종료일은 제외했지만 교육 지표는 사후 통계다. 제외 민감도도 제시하며 실무 사전 예측으로 주장하지 않는다.

**보험금 비용이 도움이 되는가?** 위 M1과 M2의 AP·ROC-AUC 및 보고서의 차이 구간을 함께 설명한다. 단일 수치가 증가한 것만으로 보편적인 개선을 주장하지 않는다.
''')
    readme=f'''# 건강보험 계약 이탈과 보험금 비용 특성 분석

생명보험 계약 유지관리 업무와 연결해 스페인 공개 건강보험 자료의 이탈 특성을 분석한다. 나이·성별·계약·지역 사회경제 정보를 고려하고 보험금 비용의 추가 예측 가치를 비교한다.

## 현재 프로젝트 진행 상태

2026년 11월 2일, 변수 구성을 수정하고 EDA와 예비 모델 비교를 실행했다. 지역 교육 지표가 2021년 통계를 사용하므로 이번 결과는 사후 연구용이다. 당시 실무 예측 성능이나 이탈 방어 효과로 해석하지 않는다.

## 단계별 산출물

- [1차 — 데이터분석 프로젝트 기획](01_proposal/01_proposal.md)
- [2차 — 데이터 확보·전처리·EDA](02_data-eda/02_eda_report.md)
- [3차 — 예비 분석·모델링·검증](03_analysis-modeling/03_preliminary_results.md)
- 4차 — 최종 프로젝트: 진행 예정
- [변수 구성과 의미](docs/variable_specification.md)
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
'''
    (ROOT/'README.md').write_text(readme)
    backup=ROOT.parent/'개인백업/프로젝트1_이식_20261102'
    backup.mkdir(exist_ok=True)
    (backup/'프로젝트1_다른LLM에전달.md').write_text('# 프로젝트 인수인계 — 2026년 11월 2일\n\n이전 20261014 버전 대신 사용한다. 실제 변수는 아래 보고서와 코드에 명시한다. 개인·지역 변수 제외 계획은 폐기했다. 교육 지표 시점 제약을 삭제하지 않는다. 발표 자료는 GitHub에 올리지 않는다.\n\n'+readme+'\n\n'+(ROOT/'docs/variable_specification.md').read_text()+'\n\n'+model_text)
    print('Reports, figures, local notes and handover updated.')

if __name__=='__main__':
    main()
