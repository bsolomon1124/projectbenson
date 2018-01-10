"""Download & concatenate MTA data from Q1 2017."""

import pandas as pd

# Create a (NumPy array of) string representations of dates.
# We will loop over these to build URLs to the
#     MTA.info-hosted .txt files.
path = 'http://web.mta.info/developers/data/nyct/turnstile/turnstile_%s.txt'
dates = pd.date_range(start='2017-01-14', end='2017-04-01', freq='W-SAT')\
    .strftime('%y%m%d')

# Concatenate a calender-quarter's worth of data.
mta = []
for date in dates:
    # We can't enforce `dtype=` param here
    #     because of the concatenation later.
    df = pd.read_csv(path % date, parse_dates=[['DATE', 'TIME']],
                     infer_datetime_format=True)
    mta.append(df)
mta = pd.concat(mta).sort_values('DATE_TIME').drop('DIVISION', axis=1)
mta = mta[mta['DESC'] != 'RECOVR AUD']
mta.drop('DESC', axis=1, inplace=True)
mta.reset_index(drop=True, inplace=True)

# Enforce pd.categorical on a handful of column types to reduce memory usg.
# See https://www.dataquest.io/blog/pandas-big-data/
cols = ['LINENAME', 'STATION', 'C/A', 'SCP']
for col in cols:
    mta[col] = mta[col].astype('category')

mta.columns = mta.columns.str.strip()
mta.drop('EXITS', axis=1, inplace=True)
mta.drop_duplicates(subset=['C/A', 'UNIT', 'SCP', 'STATION', 'DATE_TIME'],
                    inplace=True)

# Pickle intermediate result for faster retrieval
mta.to_pickle('mta.pickle')
