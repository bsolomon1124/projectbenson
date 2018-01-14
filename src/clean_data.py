"""Find first-discrete-difference ridership from Q1 2017 MTA data."""

from collections import defaultdict
import pandas as pd


pickle_dir = '/Users/brad/Scripts/python/metis/metisgh/projectbenson/pickled/'
mta = pd.read_pickle(pickle_dir + 'mta.pickle')

# One correction - these are used interchangeably
mta['STATION'] = mta['STATION'].str.replace('14TH STREET', '14 ST')

# There are some naming issues with LINENAME in the raw dataset.
# For instance, Borough Hall may use either of these LINENAMEs:
# - R2345
# - 2345R
# While Times Sq-42 St may use:
# - 1237ACENQRS
# - 1237ACENQRSW
demo_dir = ('/Users/brad/Scripts/python/metis/metisgh/'
            'projectbenson/demographics/')
names = pd.read_csv(demo_dir + 'DuplicateNames.csv', usecols=['Old Name'],
                    squeeze=True)
names = names.str.split(' -- ', expand=True)
names = names.rename(columns={0: 'station', 1: 'line'})
station, lines = names.to_dict(orient='list').values()

# LINENAMES to replace (use 0th within each tuple)
to_change = defaultdict(list)
for s, l in zip(station, lines):
    to_change[s].append(l)

for k, v in to_change.items():
    cond = (mta['STATION'] == k) & (mta['LINENAME'].isin(v[1:]))
    mta.loc[cond, 'LINENAME'] = v[0]

# The ENTRIES and EXITS fields are *cumulative*.  We want a first
#     discrete difference, but we first need to effectively form some
#     unique ID for each turnstile, which here is a combination of the
#     five fields below.
# Pass sort=False for a small speedup.
mta['NEW_ENTRIES'] = mta.groupby(['LINENAME', 'STATION', 'C/A', 'UNIT', 'SCP'],
                                 sort=False)['ENTRIES'].transform(lambda s:
                                                                  s.diff())

# Manual inspection showed us that first-differences > 3350 were
#     illegitimate, for one of several reasons.  These composed about
#     25 entries of the >2 million total.
#     (3350 entries per 4 hrs = 1 person per ~4.5 seconds - not impossible.)
# However, because we have irregular timeslot frequencies (not all 4 hrs), we
#     can be more exact by dropping entries that exceed  *rate* rather than
#     nominal threshold.  3,500/4hrs -> 0.243 entries per second.
threshold = 3500/4/60/60
mta['ELAPSED'] = mta.groupby(['LINENAME', 'STATION', 'C/A', 'UNIT', 'SCP'],
                             sort=False)['DATE_TIME'].transform(lambda s:
                                                                s.diff())
mta['ENTRIES_PER_SEC'] = mta['NEW_ENTRIES'].divide(
    mta['ELAPSED'].dt.total_seconds())
mta = mta[(mta['NEW_ENTRIES'].ge(0)) & (mta['ENTRIES_PER_SEC'].lt(threshold))]
mta['NEW_ENTRIES'] = pd.to_numeric(mta.NEW_ENTRIES, downcast='integer')

# Lastly, we need to roll *back up* to the station level, upsampling from
#     individual turnstiles, so to speak.
groupers = ['LINENAME', 'STATION', 'C/A', pd.Grouper(freq='4H')]
totals = mta.set_index('DATE_TIME').groupby(groupers)['NEW_ENTRIES'].sum()
# Or: mta.groupby(['LINENAME', 'STATION', 'C/A'])\
#     .resample(4H, on='DATE_TIME')['NEW_ENTRIES'].sum()
totals = totals.sort_values(ascending=False).reset_index()
totals.to_pickle(pickle_dir + 'totals.pickle')
