import json
import os
import time
import random

from confluent_kafka import Producer
from confluent_kafka.serialization import SerializationContext, MessageField, StringSerializer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONSerializer
from kafka_config import sr_config, config
from product_generator import generate_data, generate_object

topic = os.getenv('KAFKA_TOPIC', 'result.overall')
schema_registry_client = SchemaRegistryClient(sr_config)
producer = Producer(config)
urpids = []

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
    count = 0
    while True:
        fake_data = generate_data()
        urpids.extend([x['urpid'] for x in fake_data['transaction']['new_objects']])
        # print(json.dumps(fake_data, indent=2))
        if count > 1000:
            update_objects = [generate_object(random.choice(urpids)) for _ in range(100)]
            fake_data['transaction']['update_objects'].extend(update_objects)

        producer.produce(topic=topic,
                         # partition=0,
                         key=string_serializer(fake_data['transaction']['trusted_system']),
                         value=json_serializer(fake_data,
                                               SerializationContext(topic, MessageField.VALUE)),
                         on_delivery=delivery_report)
        producer.flush()
        count += 1
        time.sleep(0.2)