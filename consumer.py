from confluent_kafka import Consumer
from confluent_kafka.schema_registry.json_schema import JSONDeserializer
from confluent_kafka.serialization import SerializationContext, MessageField

from config import config

topic = 'result.overall'

with open('schema.json', 'r') as f:
    schema_str = f.read()

def set_consumer_configs():
    config['group.id'] = 'temp_group'
    config['auto.offset.reset'] = 'earliest'

set_consumer_configs()
json_deserializer = JSONDeserializer(schema_str)
consumer = Consumer(config)
consumer.subscribe([topic])
while True:
    try:
        event = consumer.poll(1.0)
        if event is None:
            continue
        urp_object = json_deserializer(event.value(),
                                 SerializationContext(topic, MessageField.VALUE))
        if urp_object is not None:
            print(f'Latest urp_object {urp_object}')

    except KeyboardInterrupt:
        break

consumer.close()
