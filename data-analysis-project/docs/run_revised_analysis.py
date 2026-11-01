"""고객·계약·지역 특성의 EDA와 다음 해 이탈 예비 모델 비교."""
from pathlib import Path
import hashlib
import json
import platform
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
EDA = ROOT / '02_data-eda'
MODEL = ROOT / '03_analysis-modeling'
for path in [EDA, MODEL]:
    path.mkdir(exist_ok=True)
SEED = 20261102
CONTRACT = ['seniority_insured', 'seniority_policy', 'premium', 'type_product', 'distribution_channel']
PERSONAL = ['age', 'gender']
EDUCATION = ['C_IE_P', 'C_IE_S', 'C_IE_T', 'C_GE_P', 'C_GE_S', 'C_GE_T']
REGION = ['C_H', 'C_GI', 'C_II'] + EDUCATION + ['IICIMUN', 'IICIPROV']
SETS = {'M0_contract': CONTRACT,
        'M1_personal_region': CONTRACT + PERSONAL + REGION,
        'M2_plus_claims': CONTRACT + PERSONAL + REGION + ['cost_claims_year'],
        'S1_without_education': CONTRACT + PERSONAL + [c for c in REGION if c not in EDUCATION],
        'S2_without_education_plus_claims': CONTRACT + PERSONAL + [c for c in REGION if c not in EDUCATION] + ['cost_claims_year']}

def table(frame):
    return frame.to_markdown(index=False, floatfmt='.4f')

def score(y, pred):
    return {'n': len(y), 'lapse_rate': float(np.mean(y)),
            'AP': float(average_precision_score(y, pred)),
            'ROC_AUC': float(roc_auc_score(y, pred))}

def build_model(cols, algorithm):
    cats = [c for c in cols if c in ['gender', 'C_H', 'type_product', 'distribution_channel']]
    nums = [c for c in cols if c not in cats]
    prep = ColumnTransformer([
        ('numeric', make_pipeline(SimpleImputer(strategy='median', add_indicator=True), StandardScaler()), nums),
        ('categorical', make_pipeline(SimpleImputer(strategy='constant', fill_value='Unknown'), OneHotEncoder(handle_unknown='ignore', sparse_output=False)), cats)])
    estimator = (LogisticRegression(max_iter=2000, C=1.0, random_state=SEED)
                 if algorithm == 'LogisticRegression' else
                 RandomForestClassifier(n_estimators=100, max_depth=12, min_samples_leaf=30, max_features='sqrt', n_jobs=4, random_state=SEED))
    return make_pipeline(prep, estimator)

def main():
    manifest = json.loads((ROOT / 'data/source_manifest.json').read_text())
    for item in manifest['files']:
        assert hashlib.sha256((ROOT / 'data/raw' / item['filename']).read_bytes()).hexdigest() == item['sha256']
    # 첫 실행에서 원본을 읽고 이후에는 원본·캐시 체크섬을 함께 확인한다.
    cache = ROOT / 'data/raw/revised_verified_cache.pkl'
    receipt = ROOT / 'data/raw/revised_verified_cache.json'
    source_sha = hashlib.sha256((ROOT / 'data/raw/health_insurance_portfolio.xlsx').read_bytes()).hexdigest()
    valid_cache = False
    if cache.exists() and receipt.exists():
        saved = json.loads(receipt.read_text())
        valid_cache = saved['source_sha256'] == source_sha and saved['cache_sha256'] == hashlib.sha256(cache.read_bytes()).hexdigest()
    if valid_cache:
        frame = pd.read_pickle(cache)
    else:
        frame = pd.read_excel(ROOT / 'data/raw/health_insurance_portfolio.xlsx')
        frame.to_pickle(cache)
        receipt.write_text(json.dumps({'source_sha256':source_sha,'cache_sha256':hashlib.sha256(cache.read_bytes()).hexdigest()}))
    frame.columns = frame.columns.str.strip()
    assert not frame.duplicated(['ID', 'period']).any()
    assert set(frame.lapse.unique()) == {1, 2, 3}
    date = pd.to_datetime(frame.date_lapse_insured, errors='coerce')
    year_end = pd.to_datetime(frame.period.astype(str) + '-12-31')
    rules = ((frame.lapse.eq(1) & date.dt.year.eq(frame.period) & date.lt(year_end)) |
             (frame.lapse.eq(3) & date.eq(year_end)) |
             (frame.lapse.eq(2) & (date.isna() | date.gt(year_end))))
    date_audit = {'inconsistent_status_dates': int((~rules).sum()),
                  'active_rows_with_future_termination_date': int((frame.lapse.eq(2) & date.gt(year_end)).sum())}
    assert rules.all(), date_audit
    cohorts, counts = {}, []
    for year in [2017, 2018]:
        origin = frame.loc[frame.period.eq(year) & frame.lapse.eq(2)].copy()
        later = frame.loc[frame.period.eq(year+1), ['ID', 'lapse']].rename(columns={'lapse': 'next_lapse'})
        joined = origin.merge(later, on='ID', how='left', validate='one_to_one')
        unknown = int(joined.next_lapse.isna().sum())
        joined = joined.loc[joined.next_lapse.notna()].copy()
        joined['target'] = joined.next_lapse.isin([1, 3]).astype(int)
        cohorts[year] = joined.reset_index(drop=True)
        counts.append({'feature_year': year, 'outcome_year': year+1, 'n': len(joined), 'unknown': unknown,
                       'lapses': int(joined.target.sum()), 'lapse_rate': joined.target.mean()})
    count_frame = pd.DataFrame(counts)
    count_frame.to_csv(EDA / 'cohorts.csv', index=False)
    quality = frame[CONTRACT + PERSONAL + REGION + ['cost_claims_year']].isna().sum().rename_axis('variable').reset_index(name='missing')
    quality['missing_pct'] = quality['missing'] / len(frame) * 100
    quality.to_csv(EDA / 'variable_quality.csv', index=False)
    summaries = []
    for year, g in cohorts.items():
        for col in ['age', 'gender'] + REGION + ['type_product', 'distribution_channel', 'seniority_insured', 'premium']:
            if col == 'age':
                group = pd.cut(g[col], [-1, 17, 29, 39, 49, 59, 69, np.inf], labels=['0–17','18–29','30–39','40–49','50–59','60–69','70+'])
            elif col.startswith('C_') and col != 'C_H':
                group = pd.cut(g[col], [0, 25, 50, 75, 100], labels=['P01–25','P26–50','P51–75','P76–100'])
            elif col == 'seniority_insured':
                group = pd.cut(g[col], [-np.inf, 1, 3, 5, 10, np.inf], labels=['≤1','1–3','3–5','5–10','>10'])
            elif col in ['premium', 'IICIMUN', 'IICIPROV']:
                # 개발연도의 경계를 다음 연도에도 동일하게 적용한다.
                cuts = np.unique(cohorts[2017][col].quantile([.25,.5,.75]).to_numpy())
                group = pd.cut(g[col], [-np.inf,*cuts,np.inf], labels=[f'B{i+1}' for i in range(len(cuts)+1)])
            else:
                group = g[col]
            temp = g.assign(group=group.astype('string').fillna('Unknown'))
            out = temp.groupby('group', dropna=False).agg(n=('target','size'), lapses=('target','sum'), premium_sum=('premium','sum'), claims_sum=('cost_claims_year','sum')).reset_index()
            out['lapse_rate'] = out.lapses / out.n
            out['claims_to_premium'] = out.claims_sum / out.premium_sum
            out.insert(0,'variable',col); out.insert(0,'feature_year',year)
            assert out.n.sum() == len(g)
            assert out.lapses.sum() == g.target.sum()
            summaries.append(out)
    grouped = pd.concat(summaries,ignore_index=True)
    grouped.to_csv(EDA / 'grouped_lapse.csv',index=False)
    costs=[]
    for year,g in cohorts.items():
        for scope,sub in [('all',g),('full_exposure',g.loc[np.isclose(g.exposure_time,1)])]:
            for target,part in sub.groupby('target'):
                costs.append({'feature_year':year,'scope':scope,'next_lapse':target,'n':len(part),'premium_sum':part.premium.sum(),'claims_sum':part.cost_claims_year.sum(),'claims_to_premium':part.cost_claims_year.sum()/part.premium.sum()})
    pd.DataFrame(costs).to_csv(EDA/'claims_ratios.csv',index=False)
    train, test = cohorts[2017], cohorts[2018]
    train_i, valid_i = next(GroupShuffleSplit(n_splits=1,test_size=.25,random_state=SEED).split(train,groups=train.ID_policy))
    assert not set(train.iloc[train_i].ID_policy) & set(train.iloc[valid_i].ID_policy)
    unseen = ~test.ID_policy.isin(train.ID_policy)
    results, predictions = [], {}
    for algo in ['LogisticRegression','RandomForest']:
        for name,cols in SETS.items():
            print('FIT',algo,name,flush=True)
            pipe=build_model(cols,algo)
            pipe.fit(train.iloc[train_i][cols],train.iloc[train_i].target)
            p=pipe.predict_proba(train.iloc[valid_i][cols])[:,1]
            results.append({'algorithm':algo,'features':name,'evaluation':'2017_group_holdout',**score(train.iloc[valid_i].target,p)})
            pipe.fit(train[cols],train.target)
            p=pipe.predict_proba(test[cols])[:,1]
            predictions[(algo,name)]=p
            results.append({'algorithm':algo,'features':name,'evaluation':'2018_to_2019_all',**score(test.target,p)})
            if test.loc[unseen,'target'].nunique()==2:
                results.append({'algorithm':algo,'features':name,'evaluation':'2018_to_2019_unseen_policy',**score(test.loc[unseen,'target'],p[unseen])})
    metrics=pd.DataFrame(results)
    metrics.to_csv(MODEL/'metrics.csv',index=False)
    # 같은 계약의 구성원을 함께 재표집하고 모델 간 동일 가중치를 사용한다.
    codes,policies=pd.factorize(test.ID_policy)
    rng=np.random.default_rng(SEED)
    deltas={}
    comparisons=[('M0_contract','M1_personal_region'),('M1_personal_region','M2_plus_claims'),('S1_without_education','S2_without_education_plus_claims')]
    for algo in ['LogisticRegression','RandomForest']:
        for a,b in comparisons:
            samples=[]
            for _ in range(200):
                weights=np.bincount(rng.integers(0,len(policies),len(policies)),minlength=len(policies))[codes]
                samples.append([average_precision_score(test.target,predictions[(algo,b)],sample_weight=weights)-average_precision_score(test.target,predictions[(algo,a)],sample_weight=weights),roc_auc_score(test.target,predictions[(algo,b)],sample_weight=weights)-roc_auc_score(test.target,predictions[(algo,a)],sample_weight=weights)])
            ci=np.quantile(samples,[.025,.975],axis=0)
            deltas[f'{algo}:{a}→{b}']={'AP_delta':score(test.target,predictions[(algo,b)])['AP']-score(test.target,predictions[(algo,a)])['AP'],'AP_95CI':ci[:,0].tolist(),'ROC_AUC_delta':score(test.target,predictions[(algo,b)])['ROC_AUC']-score(test.target,predictions[(algo,a)])['ROC_AUC'],'ROC_AUC_95CI':ci[:,1].tolist()}
    report={'analysis_date':'2026-11-02','seed':SEED,'python':platform.python_version(),'pandas':pd.__version__,'sklearn':sklearn.__version__,
            'feature_sets':SETS,'date_audit':date_audit,'cohorts':counts,'test_unseen_policy_n':int(unseen.sum()),'bootstrap_repeats':200,'paired_policy_bootstrap':deltas,
            'interpretation':'Retrospective exploratory analysis. Education context uses 2021 census information; other context availability at historical prediction time is not fully established. Not a deployment-valid prospective estimate.'}
    (MODEL/'analysis_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    final=metrics.loc[metrics.evaluation.eq('2018_to_2019_all')].drop(columns='evaluation')
    (MODEL/'results_table.md').write_text(table(final)+'\n')
    print(final.to_string(index=False),flush=True)
    print('DONE',json.dumps(date_audit),flush=True)

if __name__=='__main__':
    main()
