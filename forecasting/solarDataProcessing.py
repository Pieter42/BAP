'''
Authors: Aart Rozendaal and Pieter Van Santvliet
Description: In this script, the data of solar panels next to the EEMCS building is processed.
'''


print('\n\nrunning...\n')

import numpy as np
import datetime as dt
import math



# data = np.load('tempData.npy')
# retrieve the data
data = np.genfromtxt('forecasting/generationData/2019Bikechargerdata_voltageandcurrentWithoutQuotes.csv', dtype=None, encoding=None, delimiter=',', skip_header=0, comments='#')
# note on the data: date, id, charger on/off, charge state, pv voltage, pv current, ...
# np.save('tempData', arr=data) # saving the data (to decrease runtime)


# return the hour of the year, given a certain date
def hourOfYear(date): 
    beginningOfYear = dt.datetime(date.year, 1, 1, tzinfo=date.tzinfo)
    return int((date - beginningOfYear).total_seconds() // 3600)


# extract the date from the data
time = []
for t in data: 
    time.append(dt.datetime(year=2019, month=int(t['f0'][3:5]), day=int(t['f0'][0:2]), hour=int(t['f0'][9:11]))) 
time = np.array(time)

# convert the date to the hour of the year
timeAsHour = []
for t in time: timeAsHour.append(hourOfYear(t))
timeAsHour = np.array(timeAsHour)

# create a numpy array from the hour, volt, and current data
data = np.concatenate((data['f4'][:,np.newaxis],data['f5'][:,np.newaxis]), axis=1, dtype=None)

# calculate power from the voltage and current
irregularPowerData = []
for t in data: irregularPowerData.append(t[0]*t[1])
irregularPowerData = np.array(irregularPowerData)

# initialize
hourlyPowerData = np.empty(np.max(timeAsHour)+1)
hourlyPowerData[:] = np.NaN
i = 0
w = np.ones(np.max(timeAsHour)+1)

# mean for every hour
for t in timeAsHour:

    if math.isnan(hourlyPowerData[t]):
        hourlyPowerData[t] = irregularPowerData[i]
    else:
        hourlyPowerData[t] = (hourlyPowerData[t]*w[t]+irregularPowerData[i])/(w[t]+1) # weight is equal for every variable
        w[t] += 1 # this requires the weight factor to be increased throughout iterations

    i += 1

# replace all nans with the mean
replacementValue = np.nanmean(hourlyPowerData)      # calculate the mean
nanCount = 0
for i in range(len(hourlyPowerData)):   # loop through all elements
    if math.isnan(hourlyPowerData[i]):  # check for nans
        hourlyPowerData[i] = hourlyPowerData[i-24]
        # hourlyPowerData[i] = replacementValue       # replace nans with the mean
        nanCount += 1

# print('{} NaNs were replaced with {:.1f}'.format(nanCount, replacementValue))
print('NaNs per total amount of datapoints = {:.3f}'.format(nanCount/len(hourlyPowerData)))

### check for nans present
k = 0
for i in hourlyPowerData: 
    if math.isnan(i): print('error present at position ', k)
    k+=1

# save the acquired array
np.save('numpyDataFiles/processedSolarData_V3', hourlyPowerData)

print('\n...finished\n\n')