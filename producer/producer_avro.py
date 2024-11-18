import os
import time
from confluent_kafka import Producer
from confluent_kafka.serialization import SerializationContext, MessageField, StringSerializer
from confluent_kafka.schema_registry import SchemaRegistryClient
from config import sr_config, config
from product_generator import generate_data
from confluent_kafka.schema_registry.avro import AvroSerializer


topic = os.getenv('KAFKA_TOPIC', 'result.overall.avro')
schema_registry_client = SchemaRegistryClient(sr_config)
producer = Producer(config)

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
    while True:
        fake_data = generate_data()
        producer.produce(topic=topic,
                         key=string_serializer(fake_data['transaction']['trusted_system']),
                         value=avro_serializer(fake_data,
                                               SerializationContext(topic, MessageField.VALUE)),
                         on_delivery=delivery_report)
        producer.flush()
        time.sleep(5)