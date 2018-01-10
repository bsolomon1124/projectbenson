"""Find first-discrete-difference ridership from Q1 2017 MTA data."""

import pandas as pd

mta = pd.read_pickle('mta.pickle')

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

totals.to_pickle('totals.pickle')
