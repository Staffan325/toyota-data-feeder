import csv
import time
import logging
import os
import influxdb_client
from itertools import islice
import paho.mqtt.client as mqtt
import json
from datetime import datetime

BROKER_URL = os.environ.get('MQTT_URL', "localhost")
BROKER_PORT = os.environ.get('MQTT_PORT', "1887")
CLIENT_ID = os.environ.get('CLIENT_ID', "toyota")
MQTT_USERNAME = os.environ.get('MQTT_USERNAME', None)
MQTT_PASSWORD = os.environ.get('MQTT_PASSWORD', None)
INFLUX_BUCKET = os.environ.get('INFLUX_BUCKET', "toyota")
INFLUX_ORG = os.environ.get('INFLUX_ORG', "toyota")
INFLUX_TOKEN = os.environ.get('INFLUX_TOKEN')
INFLUX_URL = os.environ.get('INFLUX_URL', "http://localhost:8086")
is_connected = False


def send_data(client, data):
    """Sends data to MQTT broker.
    Data is a dictionary with timestamps as keys and values as dictionaries
    with signal names as keys and values as values."""

    # Get the first timestamp
    initial_time = next(iter(data))

    while True:
        # Set the previous timestamp to the first timestamp
        prev_time = initial_time

        for key in data.keys():
            # Calculate the delta between the current and previous timestamp
            delta = key - prev_time
            prev_time = key

            # Skip if delta is negative
            if (delta < 0):
                logging.error(f"Negative delta! {delta}")
                continue

            # Publish the data
            for data_key, value in data[key].items():
                client.publish(topic=f"{CLIENT_ID}/toyota/{data_key}", payload=f"{value}", qos=0, retain=False)

            # Wait for the delta
            time.sleep(delta)
        logging.info("Data sent, restarting from the beginning")
        time.sleep(1)


def get_value(value):
    try:
        return value.split(':')[0]
    except AttributeError:
        return value


def read_influx_data(fields=['SPEED']):
    """Reads data from InfluxDB and returns a dictionary with timestamps as
    keys and values as dictionaries with signal names as keys and values as
    values."""

    field_text = " or ".join([f"r[\"_field\"] == \"{field}\"" for field in fields])

    records = {}

    # Connect to InfluxDB
    influx_clinet = influxdb_client.InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG, verify_ssl=False)
    influx_api = influx_clinet.query_api()
    query = f"""from(bucket:\"{INFLUX_BUCKET}\")
        |> range(start: {os.environ.get('DATA_START', '-1h')}{f', start: {os.environ.get("DATA_END")}' if 'DATA_EBD' in os.environ.keys() else ''})
        |> filter(fn: (r) => {field_text})"""
    result = influx_api.query(org=INFLUX_ORG, query=query)

    # Convert the result to a dictionary with timestamps as keys and values
    # as dictionaries with signal names as keys and values as values
    for table in result:
        for record in table.records:
            time = record.get_time().astimezone().timestamp()
            records[time] = {
                record.get_field(): get_value(record.get_value())
            }

    return records


def read_gps_data():
    """Reads data from gps json and returns a dictionary with timestamps as
    keys and values as dictionaries with signal names as keys and values as
    values."""
    with open ("points.json", "r") as file:
        points = json.load(file)
        # Convert isoformat to timestamp
        return {datetime.fromisoformat(key).timestamp(): {"GPS": f"{value.get('lat')}, {value.get('lon')}"} for key, value in points.items()}


def main():
    points = read_gps_data()
    records = read_influx_data(["SPEED", "BRAKE_AMOUNT", "BRAKE_PEDAL", "GAS_PEDAL", "SET_SPEED", "STEERING_TORQUE", "YAW_RATE", "RELATIVE_THROTTLE_POS", "THROTTLE_POS", "THROTTLE_POS_B"])
    # Merge the two dictionaries
    points.update(records)
    # Sort the dictionary by timestamp
    data = dict(sorted(points.items()))

    # Connect to MQTT broker
    client = mqtt.Client()
    if MQTT_USERNAME and MQTT_PASSWORD:
        print("Setting username and password")
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.tls_set("ca.crt")
    client.tls_insecure_set(True)
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect
    client.connect(BROKER_URL, int(BROKER_PORT))
    client.loop_start()

    while not is_connected:
        logging.info("Connecting...")
        time.sleep(5)

    # Send the data
    send_data(client, data)

    # Disconnect from MQTT broker
    client.loop_stop()
    client.disconnect()


def on_connect(client, userdata, flags, rc):
    if rc==0:
        global is_connected
        is_connected = True
        logging.info("Connected to broker")
    else:
        is_connected = False
        logging.warning("Failed to connected with result " + str(rc))


def on_disconnect(client, userdata, rc):
    if rc != 0:
        logging.error("Unexpected disconnection.")


def on_publish(client, userdata, result):
        logging.debug("Msg id published: "+ str(result))


if __name__ == "__main__":
    main()
