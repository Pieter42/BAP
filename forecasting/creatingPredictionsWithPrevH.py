'''
Authors: Aart Rozendaal and Pieter Van Santvliet
Description: In this script, ANN models are trained with a training set and evaluated on a test set. The training set consists of the data of the previous hour: either the actual value or a prediction.
'''

import os
# os.system('cls') # clears the command window
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' # suppress tf warnings
import datetime as dt; start_time = dt.datetime.now()
# display a "Run started" message
print('\nRun started at', start_time.strftime("%X"), '\n')

import matplotlib.pyplot as plt
import numpy as np
import functions as fs
import sklearn as sk
import sklearn.impute
import math
from keras.layers import Dense
from keras.models import Sequential
from keras.wrappers.scikit_learn import KerasRegressor
from tensorflow import keras
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GridSearchCV


# suppress depreciation warnings
import tensorflow.python.util.deprecation as deprecation
deprecation._PRINT_DEPRECATION_WARNINGS = False


# retrieve all input and output data
X_s, y_s = fs.retrieveSolarData()
X_w, y_w = fs.retrieveWindData()
X_d, y_d = fs.retrieveDemandData()

# check for nans in the output data
if sum(np.isnan(y_s))+sum(np.isnan(y_w))+sum(np.isnan(y_d)) != 0: print('nans found')

# scaling
meanSunPower = 12.27*10**6/365/24 # average sun generation per hour
y_s = meanSunPower/np.mean(y_s)*y_s # [Wh/hour] # scale the data

meanWindPower = 10.87*10**6/365/24 # [W] # average wind generation per hour
y_w = meanWindPower/np.mean(y_w)*y_w # [Wh/hour] # scale the data


# adding data of the previous hour
dataForControl = np.load('dataForControl.npz')
# realSolar =     dataForControl['realSolar']
# realWind =      dataForControl['realWind']
# predWind =      dataForControl['predWind']
# realDemand =    dataForControl['realDemand']
predSolar =     dataForControl['predSolar']
predWind =      np.load('y_pred_w.npy')
predDemand =    dataForControl['predDemand']

# # using the actual previous hour
# newFeature = np.delete(np.insert(y_s,0,y_s[0]),-1)[:,np.newaxis]
# X_s = np.append(X_s, newFeature, axis=1)
# newFeature = np.delete(np.insert(y_w,0,y_w[0]),-1)[:,np.newaxis]
# X_w = np.append(X_w, newFeature, axis=1)
# newFeature = np.delete(np.insert(y_d,0,y_d[0]),-1)[:,np.newaxis]
# X_d = np.append(X_d, newFeature, axis=1)

# using the prediction of the previous hour
newFeature = np.delete(np.insert(predSolar,0,predSolar[0]),-1)[:,np.newaxis]
X_s = np.append(X_s, newFeature, axis=1)
newFeature = np.delete(np.insert(predWind,0,predWind[0]),-1)[:,np.newaxis]
X_w = np.append(X_w, newFeature, axis=1)
newFeature = np.delete(np.insert(predDemand,0,predDemand[0]),-1)[:,np.newaxis]
X_d = np.append(X_d, newFeature, axis=1)


# X_s_week = X_s[:7*24,:]
# X_w_week = X_w[105194-2:105194-2+7*24,:]
# X_d_week = X_d[:7*24,:]
# y_s_week = y_s[:7*24]
# y_w_week = y_w[105194-2:105194-2+7*24]
# y_d_week = y_d[:7*24]

# 3865:4060

X_s_week = X_s[3865:4060,:]
X_w_week = X_w[105194-2+3865:105194-2+4060,:]
X_d_week = X_d[3865:4060,:]
y_s_week = y_s[3865:4060]
y_w_week = y_w[105194-2+3865:105194-2+4060]
y_d_week = y_d[3865:4060]

X_s = np.delete(X_s, np.s_[3865:4060], 0)
X_w = np.delete(X_w, np.s_[105194-2+3865:105194-2+4060], 0)
X_d = np.delete(X_d, np.s_[3865:4060], 0)
y_s = np.delete(y_s, np.s_[3865:4060], 0)
y_w = np.delete(y_w, np.s_[105194-2+3865:105194-2+4060], 0)
y_d = np.delete(y_d, np.s_[3865:4060], 0)

# X_s = X_s[7*24:,:]
# X_w = X_w[:105194-2,:]
# X_d = X_d[7*24:,:]
# y_s = y_s[7*24:]
# y_w = y_w[:105194-2]
# y_d = y_d[7*24:]



# splitting data in test and training sets
X_train_s, X_test_s, y_train_s, y_test_s = train_test_split(X_s, y_s, test_size=.3, random_state=42)
X_train_w, X_test_w, y_train_w, y_test_w = train_test_split(X_w, y_w, test_size=.3, random_state=42)
X_train_d, X_test_d, y_train_d, y_test_d = train_test_split(X_d, y_d, test_size=.3, random_state=42)

# checking and handling missing values 
imp = sk.impute.SimpleImputer(missing_values=np.nan, strategy='median')

X_s = imp.fit_transform(X_s)
X_train_s = imp.fit_transform(X_train_s)
X_test_s = imp.fit_transform(X_test_s)

X_w = imp.fit_transform(X_w)
X_train_w = imp.fit_transform(X_train_w)
X_test_w = imp.fit_transform(X_test_w)

X_d = imp.fit_transform(X_d)
X_train_d = imp.fit_transform(X_train_d)
X_test_d = imp.fit_transform(X_test_d)

X_s_week = imp.fit_transform(X_s_week)
X_w_week = imp.fit_transform(X_w_week)
X_d_week = imp.fit_transform(X_d_week)

# defining certain variables
verbose = 0         # 0 to show nothing; 1 (much) or 2 (little) to show the progress
n_splits = 5

# from https://machinelearningmastery.com/regression-tutorial-keras-deep-learning-library-python/

# define solar base model
def solarBaselineModel():
    # create model
    model = Sequential()
    model.add(Dense(20, input_dim=23, kernel_initializer='normal', activation='relu'))
    model.add(Dense(5, kernel_initializer='normal', activation='relu'))
    model.add(Dense(30, kernel_initializer='normal', activation='relu'))
    model.add(Dense(1, kernel_initializer='normal'))
    # Compile model
    model.compile(loss='mean_squared_error', optimizer='adam')
    return model

# define generation base model
def windBaselineModel():
    # create model
    model = Sequential()
    model.add(Dense(10, input_dim=23, kernel_initializer='normal', activation='relu'))
    model.add(Dense(15, kernel_initializer='normal', activation='relu'))
    model.add(Dense(25, kernel_initializer='normal', activation='relu'))
    model.add(Dense(1, kernel_initializer='normal'))
    # Compile model
    model.compile(loss='mean_squared_error', optimizer='adam')
    return model

# define demand base model
def demandBaselineModel():
    # create model
    model = Sequential()
    model.add(Dense(150, input_dim=8, kernel_initializer='normal', activation='relu'))
    model.add(Dense(200, kernel_initializer='normal', activation='relu'))
    model.add(Dense(50, kernel_initializer='normal', activation='relu'))
    model.add(Dense(25, kernel_initializer='normal', activation='relu'))
    model.add(Dense(20, kernel_initializer='normal', activation='relu'))
    model.add(Dense(1, kernel_initializer='normal'))
    # Compile model
    model.compile(loss='mean_squared_error', optimizer='adam')
    return model

# solar
batch_size_s = 200
epochs_s = 500

# wind
batch_size_w = 200
epochs_w = 200

# demand
batch_size_d = 500
epochs_d = 1000


# combine base models, batch sizes, and epochs
solarModel = KerasRegressor(build_fn=solarBaselineModel, epochs=epochs_s, batch_size=batch_size_s, verbose=verbose)
windModel = KerasRegressor(build_fn=windBaselineModel, epochs=epochs_w, batch_size=batch_size_w, verbose=verbose)
demandModel = KerasRegressor(build_fn=demandBaselineModel, epochs=epochs_d, batch_size=batch_size_d, verbose=verbose)


# make predictions on the test set
MSE_s = fs.trainWithoutCurve(X_train_s, y_train_s, X_test_s, y_test_s, solarModel)
y_pred_s = solarModel.predict(X_s)

MSE_w = fs.trainWithoutCurve(X_train_w, y_train_w, X_test_w, y_test_w, windModel)
y_pred_w = windModel.predict(X_w)

MSE_d = fs.trainWithoutCurve(X_train_d, y_train_d, X_test_d, y_test_d, demandModel)
y_pred_d = demandModel.predict(X_d)

# print(X_s_week)
y_pred_s_week = solarModel.predict(X_s_week)
print(y_pred_s_week)
y_pred_w_week = windModel.predict(X_w_week)
print(y_pred_w_week)
y_pred_d_week = demandModel.predict(X_d_week)


# print all results
print('######################################################################')
print('########################### WITH PREV HOUR ###########################')
print('######################################################################')
print('\n')

print('\n############################## SOLAR ##############################\n')
fs.printTrainingResults(X_s, epochs_s, batch_size_s, n_splits, solarBaselineModel, MSE_s)
print('Mean Error as fraction of Maximum:', abs(MSE_s)**0.5/np.max(y_s))

print('\n\n############################## WIND ##############################\n')
fs.printTrainingResults(X_w, epochs_w, batch_size_w, n_splits, windBaselineModel, MSE_w)
print('Mean Error as fraction of Maximum:', abs(MSE_w)**0.5/np.max(y_w))

print('\n\n############################# DEMAND #############################\n')
fs.printTrainingResults(X_d, epochs_d, batch_size_d, n_splits, demandBaselineModel, MSE_d)
print('Mean Error as fraction of Maximum:', abs(MSE_d)**0.5/np.max(y_d))

### mapping
# realSolar = y_s
# predSolar = y_pred_s
# realWind = y_w
# predWind = y_pred_w
# realDemand = y_d
# predDemand = y_pred_d

# realWind = realWind[105194-2:113953+1-2]
# predWind = predWind[105194-2:113953+1-2]

### saving
# np.savez('dataForControl_with-previous-hour',
# realSolar = realSolar,
# predSolar = predSolar,
# realWind = realWind,
# predWind = predWind,
# realDemand = realDemand,
# predDemand = predDemand)

np.savez('dataForFigure',
realSolar   = y_s_week,
predSolar   = y_pred_s_week,
realWind    = y_w_week,
predWind    = y_pred_w_week,
realDemand  = y_d_week,
predDemand  = y_pred_d_week)

# print('\n\n############################# TOTALS #############################\n')
# print('total generated in a year by realSolar:', np.sum(realSolar)/1000000, 'MWh')
# print('total generated in a year by predSolar:', np.sum(predSolar)/1000000, 'MWh')
# print('total generated in a year by realWind:', np.sum(realWind)/1000000, 'MWh')
# print('total generated in a year by predWind:', np.sum(predWind)/1000000, 'MWh')
# print('total generated in a year by realDemand:', np.sum(realDemand)/1000000, 'MWh')
# print('total generated in a year by predDemand:', np.sum(predDemand)/1000000, 'MWh')

# print the runtime
print('\nRuntime was', (dt.datetime.now() - start_time).total_seconds(), 'seconds')

from playsound import playsound
playsound('C:/Users/piete/OneDrive/Documents/My Education/06 BAP/Code/sound.wav')
