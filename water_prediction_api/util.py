import os
from dotenv import dotenv_values

from sqlalchemy import create_engine, text
import requests

from datetime import date, datetime, timedelta
import pandas as pd
import numpy as np

from tensorflow import keras



def get_sql_engine():
    """
    Returns a sqlalchemy engine proprerly configured
    for the Google Cloud SQL database
    """

    # Settings from .env file
    settings = dotenv_values()

    MODULE_PATH = os.path.dirname(os.path.realpath(__file__))
    ROOT = os.path.join(MODULE_PATH, '..')  # root of the project

    db_uri = (f"mysql+pymysql://{settings['SQL_USER']}:{settings['SQL_PWD']}"
            f"@{settings['SQL_HOST']}/{settings['SQL_DB']}"
            f"?ssl_ca={os.path.join(ROOT,settings['SQL_SSL_CA'])}"
            f"&ssl_cert={os.path.join(ROOT,settings['SQL_SSL_CERT'])}"
            f"&ssl_key={os.path.join(ROOT,settings['SQL_SSL_KEY'])}"
            f"&ssl_check_hostname=false")

    return create_engine(db_uri, echo=False, future=False)

def get_stations_df():
    """
    Queries the SQL database and returns the stations DataFrame.
    """

    engine = get_sql_engine()
    query = "SELECT * FROM stations ;"


    stations = pd.read_sql_query(query, engine)
    stations.set_index('station_id', inplace=True, drop=True)
    return stations

def get_weather_df(station_id):
    """
    Queries Cloud SQL Weather History Database (60 days before today)
    Requests weatherAPI.com forecast API (today + 9 days of forecast)
    Returns the concatenated weather data as a DataFrame
    """
    # SQL CONFGURATION
    engine = get_sql_engine()

    # WeatherAPI CONFIGURATION
    url = 'http://api.weatherapi.com/v1/forecast.json'
    settings = dotenv_values()
    key = settings['WA_KEY']

    # Stations DataFrame
    stations = get_stations_df()

    # list of the 60 days before today (for History data)
    history_days = pd.date_range(date.today() - timedelta(60), periods=60)

    # list of today + 9 following days (for Forecast data)
    forecast_days = pd.date_range(date.today(), periods=10)
    forecast_days

    # Weather History dataframe

    query = """
    SELECT day, station_id, temperature, precipitation, maxwind
    FROM weather
    WHERE station_id = {}
    AND day BETWEEN '{}' AND '{}' ;
    """

    # We can use str.format() here, injection safe, pd.read_sql_query() used
    f_query = query.format(station_id, history_days[0].strftime('%Y-%m-%d'),
                        history_days[-1].strftime('%Y-%m-%d'))

    history_weather = pd.read_sql_query(f_query, engine)
    history_weather.day = pd.to_datetime(history_weather.day)


    # Weather Forecast dataframe (weather forecast, from WeatherAPI.com API)

    gps_coord = f"{stations.loc[station_id,'lat']},{stations.loc[station_id,'lon']}"

    params = {
        'key': key,
        'q': gps_coord,
        'days': 10,
    }

    response = requests.get(url, params)
    json_resp = response.json()
    forecast_days = json_resp.get('forecast').get('forecastday')

    # Tests
    assert response  # response in 2XX and 3XX
    assert len(forecast_days) == 10  # 10 days in the response
    assert forecast_days[0].get('date') == datetime.today().strftime(
        '%Y-%m-%d')  # First day is today

    list_forecast = {
        'day': [],
        'temperature': [],
        'precipitation': [],
        'maxwind': []
    }

    for day in forecast_days:

        str_date = datetime.strptime(day.get('date'), '%Y-%m-%d')
        list_forecast['day'].append(str_date)

        temperature = day.get('day').get('avgtemp_c')
        list_forecast['temperature'].append(temperature)

        maxwind = day.get('day').get('maxwind_kph')
        list_forecast['maxwind'].append(maxwind)

        precipitation = day.get('day').get('totalprecip_mm')
        list_forecast['precipitation'].append(precipitation)

    forecast_weather = pd.DataFrame(list_forecast)
    forecast_weather['station_id'] = station_id

    # Returns the concatenated DataFrame
    return pd.concat([history_weather, forecast_weather])

def build_features_data(station_id,stations,weather):
    """
    Constitute the data used by the model to predict the Nitrate Concentration
    Returns it as a DataFrame
    INPUT :
    - station_id : the ID of the station where the prediction is done
    - stations : the DataFrame with stations information
    - the DataFrame with weather information
    """

    # First, adding days to the DataFrame
    days = pd.date_range(date.today() - timedelta(60), periods=70)
    data = pd.DataFrame(days, columns=['day'])

    # Adding mean_nitrate
    data['mean_nitrate'] = stations.loc[station_id, 'mean_nitrate']

    # Adding weather
    data = pd.merge(data, weather, on='day', how='left')

    # Adding previous temperatures, maxwinds and precipitations
    DELTA = 60

    for delta in range(1, DELTA + 1):
        data[f'maxwind_{delta}'] = data['maxwind'].shift(periods=delta)
        data[f'temperature_{delta}'] = data['temperature'].shift(periods=delta)
        data[f'precipitation_{delta}'] = data['precipitation'].shift(periods=delta)
        data = data.copy()

    data.dropna(inplace=True)

    # Adding day_of_year columns
    data['doy'] = data['day'].dt.dayofyear  # doy = day of year

    # Turns day of year to cyclical feature (sin,cos)
    data['sin_doy'] = np.sin((data['doy'] - 1) * 2 * np.pi / 365)
    data['cos_doy'] = np.cos((data['doy'] - 1) * 2 * np.pi / 365)

    return data.copy()

def add_prediction_to_the_data(data):
    """
    From a DataFrame with the needed features, loads the keras model
    and adds a prediction column with the predicted data
    """

    model = keras.models.load_model('../keras_model')

    feature_columns = [
        'sin_doy',
        'cos_doy',
        'mean_nitrate',
        'temperature',
        'precipitation',
        'maxwind',
    ]


    for delta in range(1, 61): # we have 60 previous weather for each row
        feature_columns += [f'precipitation_{delta}']
        feature_columns += [f'temperature_{delta}']
        feature_columns += [f'maxwind_{delta}']

    X = data[feature_columns]
    data['prediction'] = model.predict(X)
