"""Find first-discrete-difference ridership from Q1 2017 MTA data."""

from collections import defaultdict
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib as mpl
# import seaborn as sns

mpl.rc('xtick', labelsize=13)

mta = pd.read_pickle('mta.pickle')
totals = pd.read_pickle('totals.pickle')

FONTSIZE = 20
SUBSIZE = 14
FIGSIZE = 8, 6

mta = pd.read_pickle('mta.pickle')

mta['IDS'] = mta['STATION'].str.cat(mta['LINENAME'], sep=' -- ')

# The ENTRIES and EXITS fields are *cumulative*.  We want a first
#     discrete difference, but we first need to effectively form some
#     unique ID for each turnstile, which here is a combination of the
#     five fields below.
# We pass sort=False for a small speedup.
# A `transform` operation does not reshape.
mta['NEW_ENTRIES'] = mta.groupby(['LINENAME', 'STATION', 'C/A', 'UNIT', 'SCP'],
                                 sort=False)['ENTRIES'].transform(lambda s:
                                                                  s.diff())

# Manual inspection showed us that first-differences > 3350 were
#     illegitimate, for one of several reasons.  These composed about
#     25 entries of the >2 million total.
# 3350 entries per 4 hrs = 1 person per ~4.5 seconds.
#     (Impressive but not unrealistic.)
mta = mta[(mta['NEW_ENTRIES'].ge(0)) & (mta['NEW_ENTRIES'].lt(3350))]
mta['NEW_ENTRIES'] = pd.to_numeric(mta.NEW_ENTRIES, downcast='integer')

# Lastly, we need to roll *back up* to the station level, upsampling from
#     individual turnstiles, so to speak.
groupers = ['LINENAME', 'STATION', 'C/A', pd.Grouper(freq='4H')]
totals = mta.set_index('DATE_TIME').groupby(groupers)['NEW_ENTRIES'].sum()
totals = totals.sort_values(ascending=False).reset_index()

# -----
# Some last-minute munging...

names = pd.read_csv('DuplicateNames.csv', usecols=['Old Name'],
                    squeeze=True)
names = names.str.split(' -- ', expand=True)
names = names.rename(columns={0: 'station', 1: 'line'})

station = names['station'].tolist()
lines = names['line'].tolist()

# LINENAMES to replace (use 0th)
to_change = defaultdict(list)
for s, l in zip(station, lines):
    to_change[s].append(l)

# One station rename
totals['STATION'] = totals['STATION'].replace('14TH STREET', '14 ST')

for k, v in to_change.items():
    cond = (totals['STATION'] == k) & (totals['LINENAME'].isin(v[1:]))
    totals.loc[cond, 'LINENAME'] = v[0]

totals.to_pickle('totals.pickle')


# ----

# MON-THU, weighted, 4-noon only
mon_thu = totals[totals['DATE_TIME'].dt.hour.isin([8, 12])]
mon_thu = totals[totals['DATE_TIME'].dt.weekday < 5]
mon_thu = mon_thu.groupby(['LINENAME', 'STATION', 'C/A'], sort=False)\
    ['weighted'].mean().sort_values(ascending=False)
mon_thu.to_pickle('mon_thu.pickle')
# ... TODO ...
mon_thu.head().plot.barh(figsize=FIGSIZE)
plt.xlabel('Mean Demographic-Wghtd Entries', fontsize=SUBSIZE)
plt.title('Top Station Entrances: Demographics', fontsize=FONTSIZE)
plt.savefig('mon_thu.png')


techcenters = pd.read_csv('TechCenters.csv', squeeze=True).tolist()
tech_totals = totals[totals.IDS.isin(techcenters)]
tech_totals = tech_totals[tech_totals['DATE_TIME'].dt.hour == 20]
tech_totals = tech_totals[tech_totals['DATE_TIME'].dt.weekday < 5]
tech_totals = tech_totals.groupby(['LINENAME', 'STATION', 'C/A'], sort=False)\
    ['NEW_ENTRIES'].mean().sort_values(ascending=False)
tech_totals.to_pickle('tech_totals.pickle')
tech_totals.head().plot.barh(figsize=FIGSIZE)
plt.xlabel('Mean Entries', fontsize=SUBSIZE)
plt.title('Top Station Entrances: Tech Centers', fontsize=FONTSIZE)
plt.savefig('tech.png')

nominal = totals[totals['DATE_TIME'].dt.weekday < 5]
nominal = nominal.groupby(['LINENAME', 'STATION', 'C/A'], sort=False)\
    ['NEW_ENTRIES'].mean().sort_values(ascending=False)
nominal.to_pickle('nominal.pickle')
mon_thu.head().plot.barh(figsize=FIGSIZE)
plt.xlabel('Mean Entries', fontsize=SUBSIZE)
plt.title('Top Station Entrances: Nominal Ridership', fontsize=FONTSIZE)
plt.savefig('nominal.png')
