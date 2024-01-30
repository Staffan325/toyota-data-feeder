if [ -z "${MQTT_USERNAME+set}" ]; then
  echo "MQTT_USERNAME not set"
else
  MQTT_EXTRA_ARGS="$MQTT_EXTRA_ARGS -u $MQTT_USERNAME"
fi
if [ -z "${MQTT_PASSWORD+set}" ]; then
  echo "MQTT_PASSWORD not set"
else
  MQTT_EXTRA_ARGS="$MQTT_EXTRA_ARGS -P $MQTT_PASSWORD"
fi

echo "MQTT_EXTRA_ARGS: $MQTT_EXTRA_ARGS"

mosquitto_sub \
  -h $MQTT_URL \
  -p $MQTT_PORT \
  -t "#" \
  --cafile /mosquitto/config/ca.crt \
  -v --insecure ${MQTT_EXTRA_ARGS}
