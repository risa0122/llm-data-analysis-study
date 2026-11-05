"""알고리즘·변수 구성의 두 비교 축과 실제 차이의 해석을 생성한다."""
import pandas as pd

ALGOS = ['LogisticRegression', 'RandomForest', 'XGBoost']
CORE = ['M0_contract', 'M1_personal_region', 'M2_plus_claims']
LABELS = {'LogisticRegression':'로지스틱 회귀', 'RandomForest':'랜덤 포레스트', 'XGBoost':'XGBoost'}

def md(df):
    return df.to_markdown(index=False, floatfmt='.4f')

def ci_text(v):
    return f"AP 차이 {v['AP_delta']:+.4f}, 탐색적 95% 구간 [{v['AP_95CI'][0]:+.4f}, {v['AP_95CI'][1]:+.4f}]"

def interpretation(v):
    lo, hi = v['AP_95CI']
    if lo > 0:
        return '이 평가 표본에서는 AP 증가가 관찰되며 차이 구간도 0보다 높다. 다른 기간·보험사에서도 유지되는지는 확인되지 않았다.'
    if hi < 0:
        return '이 평가 표본에서는 AP가 낮아졌으며 차이 구간도 0보다 낮다. 더 많은 변수나 복잡한 모형이 항상 유리한 것은 아니다.'
    return 'AP 차이 구간이 0을 포함한다. 점추정치의 차이만으로 일관된 우위를 주장하기 어렵다.'

def enrich_report(text, metrics, result, root):
    final = metrics.loc[metrics.evaluation.eq('2018_to_2019_all')]
    core = final.loc[final.features.isin(CORE)]
    assert len(core) == 9 and core.n.nunique() == 1 and core.lapse_rate.nunique() == 1
    matrices=[]
    for metric in ['AP','ROC_AUC']:
        matrix=core.pivot(index='algorithm',columns='features',values=metric).reindex(index=ALGOS,columns=CORE)
        matrix.columns=['M0','M1','M2']
        matrix.index=matrix.index.map(LABELS)
        matrix=matrix.rename_axis('알고리즘').reset_index()
        matrix.to_csv(root/'03_analysis-modeling'/f'{metric.lower()}_matrix.csv',index=False)
        matrices.append(f"### {metric}\n\n{md(matrix)}")
    audit=result['comparison_audit']
    conditions=f'''## 비교 조건

| 항목 | 공통 기준 |
|---|---|
| 알고리즘 축 | 로지스틱 회귀 / 랜덤 포레스트 / XGBoost |
| 변수 구성 축 | M0 계약 5개 / M1 고객·계약·지역 18개 / M2 보험금 비용 추가 19개 |
| 개발 분할 | 2017년 입력→2018년 이탈, 계약 단위 {audit['development_train_n']:,}행 학습·{audit['development_validation_n']:,}행 검증. 계약 중복 0 |
| 이후 연도 평가 | 2018년 입력→2019년 이탈, 같은 {audit['evaluation_n']:,}행·같은 정답 |
| 전처리 | 같은 결측 대체·표준화·원핫 방식. 각 학습 구간에서만 적합 |
| 튜닝 기준 | 재실행 전 알고리즘별 설정 1개 고정, 모두 탐색 0회·early stopping 없음. 향후 탐색은 개발 구간에서만 사전 고정한 예산으로 수행 |
| 평가 지표 | 주지표 AP, 보조지표 ROC-AUC. 설정을 최종 평가에 맞춰 변경하지 않음 |
| 변수 비교 통제 | 같은 알고리즘에서는 M0·M1·M2 모두 동일 설정 |
| 통계적 한계 | 기존 평가 결과를 본 후 확장한 연구. 완전히 미관측인 최종 시험이 아님 |

분할과 평가 대상의 해시·설정은 [comparison_audit.json](comparison_audit.json), 실행 전 고정한 계획은 [experiment_protocol.json](experiment_protocol.json)에 기록했다. 서로 다른 알고리즘에 같은 트리 수를 강제하는 대신 탐색 기회와 평가 조건을 맞췄다. 이번 비교는 각 알고리즘을 충분히 튜닝했을 때의 최대 성능 비교가 아니다.
'''
    matrix_text='## 두 축으로 보는 성능\n\n행을 비교하면 같은 변수에서의 알고리즘 차이, 열을 비교하면 같은 알고리즘에서의 변수 추가 차이다. AP는 Average Precision이며 이탈을 높은 점수에 배치하는 성능을 요약한다. 값은 0~1 단위이며 정확도나 이탈 확률로 읽지 않는다.\n\n'+'\n\n'.join(matrices)
    readings=['## 관찰 → 해석 → 본 연구 시사점']
    lookup=core.set_index(['algorithm','features'])
    deltas=result['paired_policy_bootstrap']
    for feature in CORE:
        short=feature.split('_')[0]
        row=core.loc[core.features.eq(feature)]
        winner=row.sort_values('AP',ascending=False).iloc[0].algorithm
        observations=' / '.join(f"{LABELS[a]} AP {lookup.loc[(a,feature),'AP']:.4f}, AUC {lookup.loc[(a,feature),'ROC_AUC']:.4f}" for a in ALGOS)
        v=deltas[f'{feature}:RandomForest→XGBoost']
        readings.append(f'''### 알고리즘 비교 — {short}

- **관찰:** {observations}. AP 점추정치는 {LABELS[winner]}가 가장 높다. XGBoost−랜덤 포레스트 {ci_text(v)}.
- **해석:** {interpretation(v)} 이 차이는 고정한 설정에서의 비교이며 알고리즘 전체의 일반적 우위를 뜻하지 않는다.
- **본 연구 시사점:** {short}의 정보를 동일하게 사용해도 학습 방식에 따라 결과가 달라진다. 성능 순위뿐 아니라 새 계약 보조 평가·오류와 설명 가능성을 함께 검토한다.
''')
    for algo in ALGOS:
        for a,b,meaning in [(CORE[0],CORE[1],'개인·지역 정보'),(CORE[1],CORE[2],'보험금 비용')]:
            v=deltas[f'{algo}:{a}→{b}']
            av,bv=lookup.loc[(algo,a)],lookup.loc[(algo,b)]
            readings.append(f'''### 변수 구성 비교 — {LABELS[algo]} {a.split('_')[0]}→{b.split('_')[0]}

- **관찰:** AP {av.AP:.4f}→{bv.AP:.4f}, ROC-AUC {av.ROC_AUC:.4f}→{bv.ROC_AUC:.4f}. {ci_text(v)}.
- **해석:** {interpretation(v)} {'여러 속성을 함께 추가했으므로 나이·성별·소득 한 변수의 효과로 분리할 수 없다.' if a == CORE[0] else '고객·계약·지역 정보를 유지한 상태에서 보험금 비용을 추가한 예측 차이다. 비용이 이탈을 일으켰다는 뜻은 아니다.'}
- **본 연구 시사점:** {meaning}의 추가 가치는 알고리즘별 결과로 판단한다. {'지역 지표를 개인의 소득·학력으로 읽지 않으며 집단별 오류와 공표 시점을 추가 확인한다.' if a == CORE[0] else '이탈 예측의 추가 정보로 검토하되 실제 상담 효과·이익·CSM 개선액으로 환산하지 않는다.'}
''')
    readings.append('차이 구간은 동일 계약을 함께 재표집한 200회 paired bootstrap이다. 모든 비교에 같은 재표집 시드를 사용했다. 재학습 변동과 다중 비교 보정은 포함하지 않은 탐색적 구간이다. 알고리즘 간 세 쌍의 차이는 전체 보고서와 analysis_results.json에 모두 제시한다.')
    interpretation_text='\n\n'.join(readings)
    appendix=conditions+'\n\n'+matrix_text+'\n\n'+interpretation_text
    (root/'03_analysis-modeling/algorithm_feature_comparison.md').write_text('# 알고리즘과 변수 구성 비교\n\n실행일: 2026년 11월 6일. 교육 변수의 2021년 통계 사용으로 사후 연구용 비교다. IBEX 35는 단일 학습 연도의 상수이므로 학습 입력에 포함하지 않았다.\n\n'+appendix+'\n\n[전체 결과·민감도·한계](03_preliminary_results.md)\n')
    start=text.index('## 4. 결과 관찰')
    end=text.index('## 7. 한계와 추가 확인 사항')
    text=text[:start]+interpretation_text+'\n\n'+text[end:]
    text=text.replace('## 3. 실제 평가 결과',conditions+'\n\n'+matrix_text+'\n\n## 3. 실제 평가 결과')
    return text

def write_local_notes(root):
    comparison=(root/'03_analysis-modeling/algorithm_feature_comparison.md').read_text()
    notes=root/'.local-presentation/20261106'
    notes.mkdir(parents=True,exist_ok=True)
    (notes/'알고리즘_변수비교_장표원고.md').write_text('# 발표 장표 교체 원고\n\n기존 PPT 파일을 수정한 것이 아니라 최신 실험 결과를 반영한 교체 원고다. GitHub에는 업로드하지 않는다.\n\n9번 결과 장표에는 두 성능 행렬과 공통 비교 조건을 배치한다. 아래 결과마다 관찰과 해석을 함께 말하고, 10번 시사점 장표에서는 본 연구 시사점 문장을 사용한다.\n\n'+comparison)
    current=root/'.local-presentation/presentation_notes.md'
    current.write_text(current.read_text()+'\n\n## 2026년 11월 6일 비교 실험 수정\n\n최신 성능은 [알고리즘·변수 비교 장표 원고](20261106/알고리즘_변수비교_장표원고.md)를 사용한다. 이전 PPT는 이번 실험 수치를 반영하지 않은 과거 버전이다.\n')
