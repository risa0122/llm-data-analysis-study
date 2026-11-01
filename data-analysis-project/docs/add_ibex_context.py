"""BME 연말 지수로 수익률을 계산하고 기존 코호트에 연결한다."""
from pathlib import Path
import json
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]

def main():
    prices=pd.read_csv(ROOT/'data/ibex35_year_end.csv').sort_values('year')
    assert prices.year.tolist()==[2016,2017,2018,2019]
    assert prices.close_points.gt(0).all()
    prices['ibex35_return_pct']=prices.close_points.pct_change()*100
    annual=prices.loc[prices.year.ge(2017)].copy()
    annual.to_csv(ROOT/'02_data-eda/ibex35_annual.csv',index=False)
    cohorts=pd.read_csv(ROOT/'02_data-eda/cohorts.csv')
    merged=cohorts.merge(annual.rename(columns={'year':'feature_year'}),on='feature_year',how='left',validate='one_to_one',indicator=True)
    assert merged['_merge'].eq('both').all()
    assert merged['ibex35_return_pct'].notna().all()
    assert (merged.feature_year+1).eq(merged.outcome_year).all()
    merged.drop(columns='_merge').to_csv(ROOT/'02_data-eda/ibex35_cohort_context.csv',index=False)
    training_unique=int(merged.loc[merged.feature_year.eq(2017),'ibex35_return_pct'].nunique())
    assert training_unique==1
    audit={'checked_date':'2026-11-02','index':'IBEX 35 price index; excludes dividends',
           'candidate_feature':'ibex35_return_pct','formula':'100 * (year_end_close / prior_year_end_close - 1)',
           'alignment':'feature year t return, available after year-end close; outcome t+1',
           'training_feature_years':[2017],'test_feature_years':[2018],
           'unique_values_in_training':training_unique,'included_in_fitted_models':False,
           'reason':'Constant in the single training year; effect is not identifiable. Annual context and candidate feature only.',
           'source_transcription':'Year-end closes manually checked against BME 2017 and 2019 reports; returns computed without rounding before joining.'}
    (ROOT/'03_analysis-modeling/ibex35_feature_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
    print(annual[['year','close_points','ibex35_return_pct']].to_string(index=False))
    print('코호트 연결 통과 / 학습 구간 고유값:',training_unique)

if __name__=='__main__':
    main()
