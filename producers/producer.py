import json
import os
import time

from confluent_kafka import Producer
from confluent_kafka.serialization import SerializationContext, MessageField, StringSerializer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONSerializer
from kafka_config import sr_config, config
from product_generator import generate_data


topic = os.getenv('KAFKA_TOPIC', 'result.overall')
schema_registry_client = SchemaRegistryClient(sr_config)
producer = Producer(config)

with open('schema.json', 'r') as f:
    schema = f.read()

string_serializer = StringSerializer('utf8')
json_serializer = JSONSerializer(schema,
                                 schema_registry_client)


def delivery_report(err, event):
    if err is not None:
        print(f'Delivery failed on reading for {event.key().decode("utf8")}: {err}')
    else:
        print(f'Fake data produced to {event.topic()} partition {event.partition()}')

if __name__ == '__main__':
    while True:
        fake_data = generate_data()
        # print(json.dumps(fake_data, indent=2))

        producer.produce(topic=topic,
                         # partition=0,
                         key=string_serializer(fake_data['transaction']['trusted_system']),
                         value=json_serializer(fake_data,
                                               SerializationContext(topic, MessageField.VALUE)),
                         on_delivery=delivery_report)
        producer.flush()
        time.sleep(5)