# Neural Network Prediction API

from fastapi import FastAPI
from water_prediction_api import util

import pandas as pd

app = FastAPI()

@app.get("/")
def index():
    return {'ok':'NN Prediction API running'}

@app.get("/stations")
def stations_endpoint():
    """Returns a json with all the stations information"""

    stations = util.get_stations_df()
    return stations.to_dict(orient='index')


@app.get("/predictions")
def predictions_endpoint(station_id):
    """
    Use the NN model to make a prediction of the nitrate concentration
    at the given station. Priction for today and the next 9 days

    INPUT :
    - station_id - id of the station where to make the prediction (integer)

    OUTPUT : a formatted json with the following keys
    - weather : weather data used for the prediction
    - prediction : the predicted nitrate concentrations
    """

    # Asserts Station_id is an Integer
    try :
        station_id = int(station_id)
    except ValueError :
        return {'Error':'Station_id badly formatted, must be an Integer'}

    # Asserts Station_id is a known value
    stations = util.get_stations_df()
    if station_id not in stations.index :
        return {'Error': 'Station_id unknown'}

    # Builds Features data
    stations = util.get_stations_df()
    weather = util.get_weather_df(station_id)
    data = util.build_features_data(station_id, stations, weather)

    # Adds the prediction to the data
    util.add_prediction_to_the_data(data)


    # JSON FORMATTING

    # Converts datetime to string
    weather['day'] = weather['day'].dt.strftime('%Y-%m-%d')
    data['day'] = data['day'].dt.strftime('%Y-%m-%d')

    # Sets the date as index
    weather.set_index('day',drop=True,inplace=True)
    data.set_index('day', drop=True, inplace=True)

    # Restricts the DataFrames to returned columns
    weather = weather[['temperature', 'precipitation', 'maxwind']]
    data = data[['prediction']]

    return {
        'weather': weather.to_dict(orient='index'),
        'prediction': data.to_dict(orient='index')
    }
