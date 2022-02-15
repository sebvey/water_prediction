# Neural Network Prediction API

from fastapi import FastAPI
from water_prediction_api import util

import pandas as pd

app = FastAPI()

@app.get("/")
def index():
    return {'ok':'NN Prediction API running'}

@app.get("/stations_prediction")
def station_endpoint(station_id):

    # Asserts Station_id is an Integer
    try :
        station_id = int(station_id)
    except ValueError :
        return {'Error':'Station_id badly formatted, must be an Integer'}

    # Asserts Station_id is a known value
    stations = util.get_stations_df()
    # if station_id not in stations.index :
    #     return {'Error': 'Station_id unknown'}

    # # Building Features data
    # stations = util.get_stations_df()
    # weather = util.get_weather_df(station_id)
    # data = util.build_features_data(station_id, stations, weather)

    # # Adding the prediction to the data
    # util.add_prediction_to_the_data(data)

    # return {
    #     'weather': weather[['day', 'temperature', 'precipitation', 'maxwind']],
    #     'prediction': data[['day', 'prediction']]
    # }
