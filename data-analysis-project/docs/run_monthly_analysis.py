"""월초 유지 관계의 당월 이탈 예비 분석: 전년도 정보 + 전월 IBEX 35.

실행: python docs/run_monthly_analysis.py
개별 예측·패널은 로컬 .local-experiment에만 저장한다.
"""
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score, brier_score_loss
from run_revised_analysis import build_model, CONTRACT, PERSONAL, REGION, PARAMETERS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '03_analysis-modeling/monthly'
LOCAL = ROOT / '.local-experiment/monthly'
SOURCE = 'https://www.bolsasymercados.es/dam/descargas/exchange/estadisticas/tabla0101-graf-ibex-mensual.xlsx'
SEASON = ['calendar_month']
# 월은 수치의 선형 추세로 가정하지 않고 모든 알고리즘에 동일한 원핫 변수를 제공한다.
MONTHS = [f'month_{m:02d}' for m in range(1, 13)]
SETS = {
    'M0': CONTRACT + MONTHS,
    'M1': CONTRACT + PERSONAL + REGION + MONTHS,
    'M2': CONTRACT + PERSONAL + REGION + ['cost_claims_year'] + MONTHS,
    'M3_IBEX': CONTRACT + PERSONAL + REGION + ['cost_claims_year'] + MONTHS + ['ibex35_return_1m_lag'],
}

def metrics(y, p):
    return dict(n=len(y), events=int(np.sum(y)), event_rate=float(np.mean(y)),
                AP=float(average_precision_score(y, p)),
                ROC_AUC=float(roc_auc_score(y, p)), Brier=float(brier_score_loss(y, p)))

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    LOCAL.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ROOT/'data/source_manifest.json').read_text())
    for item in manifest['files']:
        assert hashlib.sha256((ROOT/'data/raw'/item['filename']).read_bytes()).hexdigest() == item['sha256']
    cache = ROOT/'data/raw/revised_verified_cache.pkl'
    receipt = json.loads((ROOT/'data/raw/revised_verified_cache.json').read_text())
    assert hashlib.sha256(cache.read_bytes()).hexdigest() == receipt['cache_sha256']
    assert receipt['source_sha256'] == manifest['files'][0]['sha256']
    frame = pd.read_pickle(cache)
    frame.columns = frame.columns.str.strip()
    assert not frame.duplicated(['ID', 'period']).any()
    source_path = ROOT/'data/raw/ibex35_monthly_bme.xlsx'
    if not source_path.exists():
        import requests
        response = requests.get(SOURCE, timeout=60)
        response.raise_for_status()
        source_path.write_bytes(response.content)
    market = pd.read_excel(source_path)
    market.columns = ['month', 'close']
    market['month'] = pd.to_datetime(market.month).dt.to_period('M')
    market['close'] = pd.to_numeric(market.close)
    market = market.sort_values('month').set_index('month')
    assert market.index.is_unique
    assert market.index.equals(pd.period_range(market.index.min(), market.index.max(), freq='M'))
    # BME는 월을 1일로 표기한다. 값은 해당 월 종가이며 연말 원천 값으로 대조한다.
    annual = pd.read_csv(ROOT/'data/ibex35_year_end.csv')
    for row in annual.itertuples():
        assert np.isclose(market.loc[pd.Period(f'{row.year}-12'), 'close'], row.close_points)
    market['return_1m_pct'] = market.close.pct_change(fill_method=None)*100
    market['ibex35_return_1m_lag'] = market.return_1m_pct.shift(1)
    market['source_month'] = market.index-1
    market.loc['2017-11':'2019-12'].to_csv(OUT/'ibex35_monthly.csv')

    panels, audits = [], []
    for year in (2018, 2019):
        origin = frame.loc[frame.period.eq(year-1) & frame.lapse.eq(2)].copy()
        later = frame.loc[frame.period.eq(year), ['ID', 'lapse', 'date_lapse_insured']].rename(
            columns={'lapse':'outcome_status', 'date_lapse_insured':'outcome_end'})
        cohort = origin.merge(later, on='ID', how='left', validate='one_to_one')
        unknown = int(cohort.outcome_status.isna().sum())
        cohort = cohort.loc[cohort.outcome_status.notna()].copy()
        cohort['outcome_end'] = pd.to_datetime(cohort.outcome_end)
        event = cohort.outcome_status.isin([1,3])
        assert cohort.loc[event,'outcome_end'].notna().all()
        assert cohort.loc[event,'outcome_end'].dt.year.eq(year).all()
        assert pd.to_datetime(cohort.date_effect_insured).le(pd.Timestamp(year-1,12,31)).all()
        # 종료일은 라벨·위험집단 구성에만 사용. 설명변수에 넣지 않는다.
        cohort['event_date'] = cohort.outcome_end.where(event)
        for month in range(1,13):
            start = pd.Timestamp(year,month,1)
            end = start + pd.offsets.MonthEnd(0)
            active = cohort.event_date.isna() | cohort.event_date.ge(start)
            part = cohort.loc[active, ['ID','ID_policy','period']+CONTRACT+PERSONAL+REGION+['cost_claims_year','event_date']].copy()
            part['target'] = part.event_date.between(start,end).astype('int8')
            part['month'] = pd.Period(start, freq='M')
            part['calendar_month'] = month
            for m in range(1,13):
                part[f'month_{m:02d}'] = int(m==month)
            part['ibex35_return_1m_lag'] = market.loc[part['month'].iloc[0],'ibex35_return_1m_lag']
            assert market.loc[pd.Period(start, freq='M'),'source_month'] < pd.Period(start, freq='M')
            assert (part.period < year).all()
            panels.append(part.drop(columns='event_date'))
        audits.append(dict(outcome_year=year, baseline_year=year-1, baseline_n=len(origin),
                           observed_n=len(cohort), unknown_n=unknown, events=int(event.sum())))
    panel = pd.concat(panels, ignore_index=True)
    assert not panel.duplicated(['ID','month']).any()
    assert panel.ibex35_return_1m_lag.notna().all()
    assert panel.groupby(['period','ID']).target.sum().le(1).all()
    for audit in audits:
        assert panel.loc[panel.period.eq(audit['baseline_year']),'target'].sum()==audit['events']
    monthly = panel.groupby('month').agg(at_risk=('target','size'),events=('target','sum'),
        ibex35_return_1m_lag=('ibex35_return_1m_lag','first')).reset_index()
    monthly['lapse_rate'] = monthly.events/monthly.at_risk
    monthly.to_csv(OUT/'monthly_cohorts.csv',index=False)
    panel.to_pickle(LOCAL/'panel.pkl')
    train = panel.loc[panel.period.eq(2017)].reset_index(drop=True)
    test = panel.loc[panel.period.eq(2018)].reset_index(drop=True)
    assert train.ibex35_return_1m_lag.nunique()==12
    assert test.ibex35_return_1m_lag.nunique()==12
    assert train.month.max()<test.month.min()
    baseline_rows=[]
    for name,pred in [('constant', np.full(len(test),train.target.mean())),
                      ('calendar_only', test.calendar_month.map(train.groupby('calendar_month').target.mean()).to_numpy())]:
        for scope,mask in [('all_2019', np.ones(len(test),dtype=bool)),('Jan_Nov_2019',test.calendar_month.ne(12).to_numpy())]:
            baseline_rows.append(dict(baseline=name,scope=scope,**metrics(test.loc[mask,'target'],pred[mask])))
    pd.DataFrame(baseline_rows).to_csv(OUT/'baselines.csv',index=False)
    results, by_month = [], []
    predictions = test[['ID','ID_policy','month','target']].copy()
    # 모델 설정 사전 고정. 튜닝 없이 전건 학습하고 동일 대상으로 비교한다.
    for algorithm in PARAMETERS:
        for name, columns in SETS.items():
            print('FIT',algorithm,name,len(train),len(test),flush=True)
            model = build_model(columns,algorithm)
            model.fit(train[columns],train.target)
            p = model.predict_proba(test[columns])[:,1]
            predictions[f'{algorithm}_{name}'] = p
            results.append(dict(algorithm=algorithm,features=name,scope='all_2019',**metrics(test.target,p)))
            mask=test.calendar_month.ne(12)
            results.append(dict(algorithm=algorithm,features=name,scope='Jan_Nov_2019',**metrics(test.loc[mask,'target'],p[mask])))
            for month, idx in test.groupby('month').groups.items():
                by_month.append(dict(algorithm=algorithm,features=name,month=str(month),**metrics(test.loc[idx,'target'],p[idx])))
            pd.DataFrame(results).to_csv(OUT/'metrics.csv',index=False)
            pd.DataFrame(by_month).to_csv(OUT/'metrics_by_month.csv',index=False)
            predictions.to_pickle(LOCAL/'predictions.pkl')
    # 동일 월·동일 대상으로 비교한 AP 차이. 12개 월이므로 유의성 주장 없이 그대로 제시.
    month_scores=pd.DataFrame(by_month)
    pivot=month_scores.pivot(index=['algorithm','month'],columns='features',values='AP').reset_index()
    pivot['AP_delta_IBEX']=pivot.M3_IBEX-pivot.M2
    pivot.to_csv(OUT/'ibex_monthly_comparison.csv',index=False)
    source_audit=dict(source=SOURCE,sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),
        feature='ibex35_return_1m_lag',unit='percent',formula='100*(close[t-1]/close[t-2]-1)',
        train_months=12,test_months=12,train_unique=12,test_unique=12,included_in_fitted_models=True,
        cohorts=audits,train_rows=len(train),test_rows=len(test),parameters=PARAMETERS,feature_sets=SETS,
        checks=['unique ID/month','one event per relation/year','annual event totals reconciled',
                'no post-lapse rows','IBEX source month before outcome month','prior-year insurance features',
                'December close matches annual BME values','same full training/evaluation population'],
        limitation='Retrospective prototype. Prior-year claims finalization and regional data publication dates not established. Annual covariates frozen within year; no monthly behavior history. Only 12 independent training market months; December renewal concentration.')
    (OUT/'audit.json').write_text(json.dumps(source_audit,ensure_ascii=False,indent=2)+'\n')
    print('DONE',json.dumps(audits),flush=True)

if __name__=='__main__': main()
