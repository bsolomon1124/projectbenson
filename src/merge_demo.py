import pandas as pd
import numpy as np


totals = pd.read_pickle('totals.pickle')
totals['IDS'] = totals['STATION'].str.cat(totals['LINENAME'], sep=' -- ')

ct = pd.read_csv('county_tract.csv').drop_duplicates()
merged = pd.read_csv('merged.csv', index_col=0).drop_duplicates()


demos = ct.merge(merged, how='left', left_on=['county', 'tract'],
                 right_on=['county', 'tract'])

totals = totals.merge(demos, how='left', left_on='IDS', right_on='Combined')

totals['Median_income'] = pd.to_numeric(totals['Median_income']
    .replace('-', np.nan)
    .replace('250,000+', 250000))

cols = totals.columns[9:]
medians = totals[cols].median()
totals[cols] = totals[cols].fillna(medians).rank(pct=True)
totals['score'] = totals[cols].mean(axis=1)

totals['weighted'] = totals['NEW_ENTRIES'].values * totals['score'].values
totals.sort_values('weighted', inplace=True)
totals.to_pickle('totals.pickle')
