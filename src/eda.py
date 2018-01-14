"""Exploratory data analysis/vislztn. on Q1 2017 MTA ridership data."""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns

mpl.rc('xtick', labelsize=13)

pickle_dir = '/Users/brad/Scripts/python/metis/metisgh/projectbenson/pickled/'
mta = pd.read_pickle(pickle_dir + 'mta.pickle')
totals = pd.read_pickle(pickle_dir + 'totals.pickle')

FONTSIZE = 20
SUBSIZE = 14
FIGSIZE = 8, 6

imgs_dir = pickle_dir.replace('pickled', 'imgs')


# Of the top 100 station-times, how many are in the "Big 3?"
big = ['GRD CNTRL-42 ST', '34 ST-PENN STA', 'PATH NEW WTC']
big3 = totals.nlargest(100, 'NEW_ENTRIES')['STATION'].value_counts().loc[big]
big3.plot.bar(figsize=FIGSIZE)
plt.ylabel('# Occurences in Top 100')
plt.title('"The Big 3": Number of Appearances in \n'
          ' Top 100 Station-Time Combinations', fontsize=FONTSIZE)
plt.text(0.5, 40, 'Total: %s of 100' % big3.sum(), fontsize=SUBSIZE)
plt.tight_layout()
plt.xticks(rotation=0)
plt.xlabel(fontsize=SUBSIZE)
plt.savefig(imgs_dir + 'big3.png')


# Similarly, what does the distribution of popular times look like?
mapping = {
    0: '8p-12a',
    4: '12a-4a',
    8: '4a-8a',
    12: '8a-12p',
    16: '12p-4p',
    20: '4p-8p'
    }
times = totals.nlargest(100, 'NEW_ENTRIES')['DATE_TIME'].dt.hour\
    .map(mapping).value_counts()
times.plot.bar(figsize=FIGSIZE)
plt.ylabel('# Occurences in Top 100')
plt.title('Timeslot Popularity Within Top 100 Station-Times',
          fontsize=FONTSIZE)
plt.tight_layout()
plt.xticks(rotation=0)
plt.annotate('Rush hour *entrances* \n dominated by "Big 3"',
             xy=(0.4, 50), xytext=(0.8, 52),
             arrowprops=dict(facecolor='red', shrink=0.05),
             fontsize=SUBSIZE)
plt.savefig(imgs_dir + 'times.png')


# Independent of station, what are the most popular four-hour blocks?
skew, mean, median = totals['NEW_ENTRIES']\
  .agg(['skew', 'mean', 'median']).round(2)
totals.hist(column='NEW_ENTRIES', bins=50)
plt.title('Histogram: Distribution of 4-Hour Ridership', fontsize=FONTSIZE)
plt.xlabel('Number of Station Entrants')
plt.ylabel('Number of Occurences')
plt.text(15000, 150000, 'Mean: %s' % mean, fontsize=SUBSIZE)
plt.text(15000, 125000, 'Median: %s' % median, fontsize=SUBSIZE)
plt.text(15000, 100000, 'Skewness: %s' % skew, fontsize=SUBSIZE)
plt.savefig(imgs_dir + 'hist.png')

# Day-of-week figures
mapping = {
    0: 'Mon',
    1: 'Tue',
    2: 'Wed',
    3: 'Thu',
    4: 'Fri',
    5: 'Sat',
    6: 'Sun'
    }
wkdays = totals.groupby(totals['DATE_TIME'].dt.weekday)['NEW_ENTRIES'].mean()\
    .multiply(6)  # daily, not 4hr, avg.
wkdays.index = wkdays.index.map(lambda f: mapping[f])
wkdays.plot.bar(figsize=FIGSIZE)
plt.title('Average Station Ridership by Weekday', fontsize=FONTSIZE)
plt.xlabel('Weekday', fontsize=SUBSIZE)
plt.ylabel('Average Daily Ridership', fontsize=SUBSIZE)
plt.annotate('Noticeable traffic \n decline', xy=(5, 5000),
             xytext=(4.4, 6000), arrowprops=dict(facecolor='red', shrink=0.05),
             fontsize=SUBSIZE)
plt.annotate('', xy=(6, 4000),
             xytext=(5.5, 6000), arrowprops=dict(facecolor='red', shrink=0.05),
             fontsize=SUBSIZE)
plt.savefig(imgs_dir + 'wkdays.png')


# Cumulative ridership (big 3)
cuml = totals.pivot_table(values='NEW_ENTRIES', columns=['STATION'],
                          index=['DATE_TIME'], aggfunc='first').cumsum()
cuml.loc[:, big].plot(figsize=FIGSIZE)
plt.title('Cuml. Ridership: "The Big 3," Q1-17', fontsize=FONTSIZE)
plt.xlabel('Date')
plt.ylabel('Cumulative Ridership')
plt.savefig(imgs_dir + 'big3cuml.png')


# Heatmap -- "tier2" stations (excl. Big3)
# Get rid of the issue that PATH WTC didn't run in January
#     and half of Feb; focus on 1 month (March).
march = (totals.DATE_TIME.dt.month == 3) & (~totals.STATION.isin(big))

prds = {
    'morning': totals[(totals.DATE_TIME.dt.hour == 8) & march],
    'aft': totals[(totals.DATE_TIME.dt.hour == 16) & march],
    'rush': totals[(totals.DATE_TIME.dt.hour == 20) & march]
    }

top = dict.fromkeys(prds)
cols = ['LINENAME', 'STATION', 'C/A']

for key in prds:
    top[key] = prds[key].groupby([prds[key].DATE_TIME.dt.weekday] + cols)\
        ['NEW_ENTRIES'].mean().reset_index()\
            .sort_values('NEW_ENTRIES', ascending=False)\
            .drop_duplicates('DATE_TIME').sort_values('DATE_TIME')

ccat = pd.concat([top[key] for key in prds])
names = enumerate(ccat.STATION.astype(str).unique().tolist())
names = {k: v for v, k in names}
hms = pd.DataFrame(ccat['STATION'].astype(str).values.reshape(7, 3),
                   index=range(0, 7),
                   columns=prds.keys())
hms.index = hms.index.map(lambda x: mapping[x])  # can't just pass dict..
hm = hms.applymap(lambda x: names[x])
sns.heatmap(hm, annot=hms.values, linewidths=0.8, cbar=False, fmt='s')
plt.title('Key Ridership: Day+Time', fontsize=FONTSIZE)
plt.savefig(imgs_dir + 'heatmap.png')


big3_dist = totals.pivot_table(values='NEW_ENTRIES', columns=['STATION'],
                               index=['DATE_TIME'], aggfunc='first')\
    .loc[:, big]
fig, ax = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
for i, station in enumerate(big):
    sns.distplot(big3_dist[station].dropna(), ax=ax[i], bins=20)
fig.suptitle('Histogram & KDE for "Big 3" Stations', fontsize=FONTSIZE)
plt.savefig(imgs_dir + 'kde.png')


FIGSIZE = 15, 6


# Constrain ourselves to morning hours, Mon-Fri.  This is where demographics
#     matter.  (i.e. you commute from where you live in morning)
mon_thu = totals[totals['DATE_TIME'].dt.hour.isin([8, 12])]
mon_thu = totals[totals['DATE_TIME'].dt.weekday < 5]
mon_thu = mon_thu.groupby(['LINENAME', 'STATION', 'C/A'], sort=False)\
    ['weighted'].mean().sort_values(ascending=False)
# ... TODO ...
mon_thu.head().reset_index(level=0).plot.barh(figsize=FIGSIZE)
plt.xlabel('Mean Demographic-Wghtd Entries', fontsize=SUBSIZE)
plt.title('Top Station Entrances: Demographics', fontsize=FONTSIZE)
plt.savefig(imgs_dir + 'mon_thu.png')


techcenters = pd.read_csv('TechCenters.csv', squeeze=True).tolist()
tech_totals = totals[totals.IDS.isin(techcenters)]
tech_totals = tech_totals[tech_totals['DATE_TIME'].dt.hour == 20]
tech_totals = tech_totals[tech_totals['DATE_TIME'].dt.weekday < 5]
tech_totals = tech_totals.groupby(['LINENAME', 'STATION', 'C/A'], sort=False)\
    ['NEW_ENTRIES'].mean().sort_values(ascending=False)
tech_totals.head().reset_index(level=0).plot.barh(figsize=FIGSIZE)
plt.xlabel('Mean Entries', fontsize=SUBSIZE)
plt.title('Top Station Entrances: Tech Centers', fontsize=FONTSIZE)
plt.savefig(imgs_dir + 'tech.png')


nominal = totals[totals['DATE_TIME'].dt.weekday < 5]
nominal = nominal.groupby(['LINENAME', 'STATION', 'C/A'], sort=False)\
    ['NEW_ENTRIES'].mean().sort_values(ascending=False)
mon_thu.head().reset_index(level=0).plot.barh(figsize=FIGSIZE)
plt.xlabel('Mean Entries', fontsize=SUBSIZE)
plt.title('Top Station Entrances: Nominal Ridership', fontsize=FONTSIZE)
plt.savefig(imgs_dir + 'nominal.png')
