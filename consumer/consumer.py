import os

from confluent_kafka import Consumer
from confluent_kafka.schema_registry.json_schema import JSONDeserializer
from confluent_kafka.serialization import SerializationContext, MessageField
from config import config


with open('schema.json', 'r') as f:
    schema_str = f.read()

def set_consumer_configs():
    config['group.id'] = 'temp_group'
    config['auto.offset.reset'] = 'earliest'


def print_assignment(cons, partitions):
    print(f'Assignment partition for {cons}: {partitions}')


set_consumer_configs()
json_deserializer = JSONDeserializer(schema_str)
topic = os.getenv('KAFKA_TOPIC', 'result.overall')

consumer = Consumer(config)
consumer.subscribe([topic], on_assign=print_assignment)
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
