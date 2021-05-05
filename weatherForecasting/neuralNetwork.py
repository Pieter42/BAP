'''
Authors: Aart Rozendaal and Pieter Van Santvliet
Description: In this script, weather data is used to predict the average capacity factor 
of wind turbines in Rotterdam. This is done using an Artificial Neural Network.
'''

import os
os.system('cls') # clears the command window
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' # suppress tf warnings
import datetime as dt; start_time = dt.datetime.now()
# display a "Run started" message
print('Run started at ', start_time.strftime("%X"), '\n')

import functions as f
import numpy as np
import sklearn as sk
import sklearn.impute
from keras.layers import Dense
from keras.models import Sequential
from keras.wrappers.scikit_learn import KerasRegressor
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


# extracting data from csv file
try:
    data = np.genfromtxt('weatherForecasting/relevantData/y_2011-data-points.csv', 
    dtype=float, delimiter=',', skip_header=1, skip_footer=12)
    y = data[:,1] # only relevant stuff; all rows of column 1
except:
    print('Error while retrieving y'); exit()

# extracting data from txt file
try:
    data = np.genfromtxt('weatherForecasting/relevantData/x_2011-data-points.txt', 
    dtype=float, delimiter=',', skip_header=33)
    X = data[:,3:] # only relevant stuff; all rows of column 3 till end
except:
    print('Error while retrieving X')
    exit()

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.3, random_state=42)
# f.printSets(X_train, X_test, y_train, y_test) # enable to print set shapes

# checking and handling missing values 
imp = sk.impute.SimpleImputer(missing_values=np.nan, strategy='median')
X_train = imp.fit_transform(X_train)
X_test = imp.fit_transform(X_test)

# from https://machinelearningmastery.com/regression-tutorial-keras-deep-learning-library-python/
# define base model
def baseline_model():
    # create model
    model = Sequential()
    model.add(Dense(22, input_dim=22, kernel_initializer='normal', activation='relu'))
    model.add(Dense(1, kernel_initializer='normal'))
    # Compile model
    model.compile(loss='mean_squared_error', optimizer='adam')
    return model

# baseline_model().summary() # enable to print a summary of the NN model

# make a single model and evaluate it with the test set
'''
estimators = []
estimators.append(('standardize', StandardScaler()))
estimators.append(('mlp', KerasRegressor(build_fn=baseline_model, epochs=5, batch_size=5, verbose=2)))
# verbose =0 will show nothing; =1 will show animated progress; =2 will mention the number of epochs
pipeline = Pipeline(estimators)
pipeline.fit(X_train,y_train)

y_pred = pipeline.predict(X_test)
mse_krr = mean_squared_error(y_test, y_pred)

print(mse_krr)
'''

# make multiple models using cross_val_score and evaluate it using validation sets from the training set
'''
# evaluate model with standardized dataset
estimators = []
estimators.append(('standardize', StandardScaler()))
estimators.append(('mlp', KerasRegressor(build_fn=baseline_model, epochs=5, batch_size=5, verbose=2)))
# verbose =0 will show nothing; =1 will show animated progress; =2 will mention the number of epochs

pipeline = Pipeline(estimators)
kfold = KFold(n_splits=3)
results = cross_val_score(pipeline, X_train, y_train, cv=kfold)

print("Standardized: %.7f (%.7f) MSE" % (results.mean(), results.std()))
'''

# print the runtime
print('\nRuntime was', (dt.datetime.now() - start_time).total_seconds(), 'seconds')
