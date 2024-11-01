import os
import sys
import time

from protobuf import urpd_product_pb2
from confluent_kafka import Producer
from confluent_kafka.serialization import SerializationContext, MessageField, StringSerializer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.protobuf import ProtobufSerializer
from config import config, sr_config
from producer.product_generator import generate_data
from google.protobuf.json_format import ParseDict



def delivery_report(err, msg):
    if err is not None:
        print("Delivery failed for User record {}: {}".format(msg.key(), err))
        return
    print('User record {} successfully produced to {} [{}] at offset {}'.format(
        msg.key(), msg.topic(), msg.partition(), msg.offset()))


def main():
    topic = os.getenv('KAFKA_TOPIC', 'result.overall.proto')

    schema_registry_client = SchemaRegistryClient(sr_config)
    string_serializer = StringSerializer('utf8')
    protobuf_serializer = ProtobufSerializer(urpd_product_pb2.UrpProduct,
                                             schema_registry_client,
                                             {'use.deprecated.format': False})

    producer = Producer(config)
    print("Producing records to topic {}. ^C to exit.".format(topic))

    try:
        producer.poll(0.0)
        while True:
            fake_data = generate_data()
            new_product = ParseDict(generate_data(), urpd_product_pb2.UrpProduct())
            producer.produce(topic=topic,
                             # partition=0,
                             key=string_serializer(fake_data['transaction']['trusted_system']),
                             value=protobuf_serializer(new_product, SerializationContext(topic, MessageField.VALUE)),
                             on_delivery=delivery_report)

            producer.flush()
            time.sleep(5)
    except ValueError:
        print("Could not convert data to an integer.")
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise

if __name__ == '__main__':
    main()
