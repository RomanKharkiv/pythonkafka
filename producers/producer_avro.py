import os
import time
from confluent_kafka import Producer
from confluent_kafka.serialization import SerializationContext, MessageField, StringSerializer
from confluent_kafka.schema_registry import SchemaRegistryClient
from kafka_config import sr_config, config
from product_generator import generate_data, generate_object
from confluent_kafka.schema_registry.avro import AvroSerializer
import random

topic = os.getenv('KAFKA_TOPIC', 'result.overall.avro')
schema_registry_client = SchemaRegistryClient(sr_config)
producer = Producer(config)
urpids = []

with open('schema.avsc', 'r') as f:
    schema_str = f.read()

string_serializer = StringSerializer('utf8')

avro_serializer = AvroSerializer(schema_registry_client, schema_str)

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
        if count > 1000:
            update_objects = [generate_object(random.choice(urpids)) for _ in range(100)]
            fake_data['transaction']['update_objects'].extend(update_objects)


        producer.produce(topic=topic,
                         key=string_serializer(fake_data['transaction']['trusted_system']),
                         value=avro_serializer(fake_data,
                                               SerializationContext(topic, MessageField.VALUE)),
                         on_delivery=delivery_report)
        producer.flush()
        count += 1
        time.sleep(0.2)