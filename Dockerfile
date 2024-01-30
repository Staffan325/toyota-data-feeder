FROM python:3.12-alpine

WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY ca.crt feeder_influx.py toyota_data.csv points.json /app/

CMD ["python3", "feeder_influx.py"]
