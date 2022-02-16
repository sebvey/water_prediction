FROM python:3.8.12-buster

COPY requirements_api.txt requirements.txt
COPY water_prediction_api water_prediction_api
COPY keras_model keras_model
COPY settings settings
COPY .env .env

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD uvicorn water_prediction_api.nn_api:app --host 0.0.0.0 --port $PORT
