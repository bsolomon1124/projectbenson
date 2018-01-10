"""Exploratory data analysis on Q1 2017 MTA ridership data."""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

mta = pd.read_pickle('mta.pickle')
totals = pd.read_pickle('totals.pickle')

FONTSIZE = 20
SUBSIZE = 14
FIGSIZE = 8, 6


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
plt.savefig('big3.png')


# Similarly, what does the distribution of popular times look like?
mapping = {
    0: '8 pm - 12 am',
    4: '12 am - 4 am',
    8: '4 am - 8 am',
    12: '8 am - 12 pm',
    16: '12 pm - 4 pm',
    20: '4 pm - 8 pm'
    }
times = totals.nlargest(100, 'NEW_ENTRIES')['DATE_TIME'].dt.hour\
    .map(mapping).value_counts()
times.plot.bar(figsize=FIGSIZE)
plt.ylabel('# Occurences in Top 100')
plt.title('Timeslot Popularity Within Top 100 Station-Times',
          fontsize=FONTSIZE)
plt.tight_layout()
plt.xticks(rotation=0)
#plt.xlabel(fontsize=SUBSIZE)
plt.savefig('times.png')
# (Not surprising because we're dealing with *ENTRIES*)


# Independent of station, what are the most popular four-hour blocks?
skew = totals['NEW_ENTRIES'].skew().round(2)
mean = totals['NEW_ENTRIES'].mean().round(2)
median = totals['NEW_ENTRIES'].median().round(2)
totals.hist(column='NEW_ENTRIES', bins=50)
plt.title('Histogram: Distribution of 4-Hour Ridership', fontsize=FONTSIZE)
plt.xlabel('Number of Station Entrants')
plt.ylabel('Number of Occurences')
plt.text(15000, 150000, 'Mean: %s' % mean, fontsize=SUBSIZE)
plt.text(15000, 125000, 'Median: %s' % median, fontsize=SUBSIZE)
plt.text(15000, 100000, 'Skewness: %s' % skew, fontsize=SUBSIZE)
plt.savefig('hist.png')


# Day-of-week figures
mapping = {
    0: 'Monday',
    1: 'Tuesday',
    2: 'Wednesday',
    3: 'Thursday',
    4: 'Friday',
    5: 'Saturday',
    6: 'Sunday'
    }
wkdays = totals.nlargest(100, 'NEW_ENTRIES')['DATE_TIME']\
    .dt.dayofweek.value_counts().reindex(range(0, 7), fill_value=0)\
    .sort_index(ascending=False)
wkdays.index = wkdays.index.map(lambda i: mapping[i])
wkdays.plot.barh(figsize=FIGSIZE)
plt.title('Occurence of Weekdays within Top 100 Station-Times',
          fontsize=FONTSIZE)
plt.xlabel('Number of appearances')
plt.annotate('Sat. & Sun.: 0 occurrences', xy=(0.5, 0.5), xytext=(5, 1),
             arrowprops=dict(facecolor='red', shrink=0.05),
             fontsize=SUBSIZE)
plt.annotate('Noticeable \n "dropoff" on Fri.', xy=(14, 2), xytext=(17, 1.8),
             arrowprops=dict(facecolor='blue', shrink=0.05),
             fontsize=SUBSIZE)
plt.savefig('wkdays.png')


# 3-largest for each weekday/weekend day
# threelargest = totals.groupby(totals['DATE_TIME'].dt.weekday)\
#     .apply(lambda df: df.nlargest(3, columns='NEW_ENTRIES'))
#
# threelargest = totals.groupby([totals['DATE_TIME'].dt.weekday,
#                                totals['DATE_TIME'].dt.hour])\
#     .apply(lambda df: df.nlargest(3, columns='NEW_ENTRIES'))

# Dropping duplicates
totals.drop_duplicates('STATION')[['STATION', 'NEW_ENTRIES']]\
    .set_index('STATION')[:10].plot.bar()


# Cumulative ridership (big 3)
cuml = totals.pivot_table(values='NEW_ENTRIES', columns=['STATION'],
                          index=['DATE_TIME'], aggfunc='first').cumsum()
cuml.loc[:, big].plot()
plt.title('Cumulative Ridership: "The Big 3," Q1 2017', fontsize=FONTSIZE)
plt.xlabel('Date')
plt.ylabel('Cumulative Ridership')
plt.savefig('big3cuml.png')


# Cumulative ridership (top 8)
top8 = cuml.iloc[-1].sort_values(ascending=False).index[:8]
cuml.loc[:, top8].plot()
plt.title('Cumulative Ridership: "Top 8 Stations," Q1 2017', fontsize=FONTSIZE)
plt.xlabel('Date')
plt.ylabel('Cumulative Ridership')
plt.savefig('top8cuml.png')

big3_disc = totals.pivot_table(values='NEW_ENTRIES', columns=['STATION'],
                               index=['DATE_TIME'], aggfunc='first')\
    .loc[:, big]
fig, ax = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
for i, station in enumerate(big):
    sns.distplot(big3_disc[station].dropna(), ax=ax[i], bins=20)
fig.suptitle('Histogram & KDE for "Big 3" Stations', fontsize=FONTSIZE)
plt.savefig('kde.png')
