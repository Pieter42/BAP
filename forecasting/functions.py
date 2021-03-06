'''
Authors: Aart Rozendaal and Pieter Van Santvliet
Description: Different functions are defined that are used to retrieve/process/evaluate data.
'''


import datetime as dt
import matplotlib.pyplot as plt
import numpy as np
import numpy.ma as ma
import sklearn as sk
import sklearn.impute
from keras.layers import Dense
from keras.models import Sequential
from keras.wrappers.scikit_learn import KerasRegressor
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from tensorflow import keras


# print the shapes of the train and test sets
def printSets(X_train, X_test, y_train, y_test):
    print("shape of X_train: {}".format(X_train.shape))
    print("shape of X_test: {}".format(X_test.shape))
    print("shape of y_train: {}".format(y_train.shape))
    print("shape of y_test: {}".format(y_test.shape))


# retrieve the weather data from the data file
def retrieveWeatherData():
    # extracting input data from txt file
    try:
        data = np.genfromtxt('forecasting/demandData/x_2013-data-points.txt', 
        dtype=float, delimiter=',', skip_header=33)
    except:
        print('Error while retrieving weather data'); exit()
        
    return data


# retrieve the wind data from the data file
def retrieveWindData():
    # extracting wind data from csv file
    try:
        data = np.genfromtxt('forecasting/generationData/Training-1_y.csv', 
        dtype=float, delimiter=',', skip_header=1, skip_footer=1)
        y = data[:,1] # only relevant stuff; all rows of column 1
    except:
        print('Error while retrieving y'); exit()

    # extracting weather data from txt file
    try:
        data = np.genfromtxt('forecasting/generationData/Training-1_X.csv', 
        dtype=float, delimiter=',', skip_header=33)
        X = data[:,3:] # only relevant stuff; all rows of column 3 till end
    except:
        print('Error while retrieving X'); exit()
    
    return X, y


# retrieve the solar data from the data file
def retrieveSolarData():
    y = np.load('numpyDataFiles/processedSolarData.npy')

    try:
        data = np.genfromtxt('forecasting/generationData/2019uurgeg_344_2011-2020.txt', 
        dtype=float, delimiter=',', skip_header=33)
        X = data[:,3:] # only relevant stuff; all rows of column 3 till end
    except:
        print('Error while retrieving X'); exit()

    return X, y


# retrieve the demand data from the data file; it is also already processed
def retrieveDemandData():
    # extracting input data from txt file
    try:
        data = np.genfromtxt('forecasting/demandData/x_2013-data-points.txt', 
        dtype=float, delimiter=',', skip_header=33)
        X = data[:,[1,2,7,10,21,23]] # only relevant stuff:
        # select YYYYMMDD (col 1; datum), HH (col 2; hour), T (col 7; temperature), 
        # SQ (col 10; sunshine duration), R (col 21; rain), O (col 23; storm)
    except:
        print('Error while retrieving input data'); exit()

    # we want the weeknumber and daynumber instead of the date
    timeInfo = np.empty((0,2), int)
    for i in X[:,0]:
        # get the date info from the data file
        year = int(str(i)[0:4])
        month = int(str(i)[4:6])
        day = int(str(i)[6:8])

        # make a date and season from the date info
        time = dt.datetime(year, month, day)
        season = time.month%12//3+1 # month2season: from https://stackoverflow.com/a/44124490
        month = time.month

        # timeInfo will contain the month and the daynumber (%u)
        timeInfo = np.append(timeInfo, np.array([[month,time.weekday()]]), axis=0)

    # the date-column is replaced by a season-number and daynumber column
    X = np.append(timeInfo, np.delete(X,0,1), 1)

    # extracting output data from csv file
    try:
        data = np.genfromtxt('forecasting/demandData/Zonnedael - slimme meter dataset - 2013 - Levering.csv', 
        dtype=float, delimiter=',', skip_header=1, skip_footer=34992)
        y = data[:,2:-2] # only relevant stuff:
        # select YYYYMMDD (col 1; datum), HH (col 2; hour), T (col 7; temperature), 
        # SQ (col 10; sunshine duration), R (col 21; rain), O (col 23; storm)
    except:
        print('Error while retrieving output data'); exit()

    # conversion of /15min to /1hr data
    y = y.reshape(-1,4,y.shape[-1]).sum(1) # summing every 4 columns

    # dealing with nans: from https://stackoverflow.com/q/18689235
    y = np.where(np.isnan(y), ma.array(y, mask=np.isnan(y)).mean(axis=1)[:, np.newaxis], y)
    y = y.sum(1) # summing all 'households' 

    # scaling the output data
    y_days = y.reshape(-1,24).sum(1) # create /day data
    mean_of_one_day_liander = np.mean(y_days) # calc mean of one day
    mean_of_one_day_tunect = 41000 # mean of 1 day at tunect (from DCG)
    scalingFactor = mean_of_one_day_tunect/mean_of_one_day_liander
    y = scalingFactor*y # scaling the data

    return X, y


### make a single model and evaluate it with the test set
def trainWithoutCurve(X_train, y_train, X_test, y_test, pipeline):
    pipeline.fit(X_train,y_train)
    y_pred = pipeline.predict(X_test)
    MSE = mean_squared_error(y_test, y_pred)
    return MSE


### make a single model (without the pipeline) and show the learning curve
def trainWithCurve(X_train, y_train, model):
    history = model.fit(X_train,y_train)
    print(history.history.keys())
    
    # summarize history for loss
    plt.plot(history.history['loss'])
    plt.title('model loss')
    plt.ylabel('loss')
    plt.xlabel('epoch')
    plt.show()


### make multiple models using cross_val_score and evaluate it using validation sets from the training set
def performCrossValidation(X_train, y_train, n_splits, pipeline):
    kfold = KFold(n_splits=n_splits)
    results = cross_val_score(pipeline, X_train, y_train, cv=kfold)

    MSE = results.mean().item()
    STD = results.std().item()
    rootMSE = abs(results.mean().item())**0.5

    return MSE,STD


### print the results
def printTrainingResults(X_train, epochs, batch_size, n_splits, baseline_model, MSE):
    # print('\n\n')
    baseline_model().summary() # enable to print a summary of the NN model
    
    print('\nParameters:')
    print('\tepochs:\t\t', epochs)
    print('\tbatch_size:\t', batch_size)
    # print('\tn_splits:\t', n_splits)
    print('\tinput shape:\t', X_train.shape)
    
    print('\nMSE becomes: {:.4f}'.format(abs(MSE)))
    print('Root MSE becomes: {:.4f}'.format(abs(MSE)**0.5))
