from protobuf import urpd_product_pb2
from confluent_kafka import Consumer
from confluent_kafka.serialization import SerializationContext, MessageField
from confluent_kafka.schema_registry.protobuf import ProtobufDeserializer
from config import config, consumer_conf
import os

def main():
    topic = os.getenv('KAFKA_TOPIC', 'result.overall.proto')

    protobuf_deserializer = ProtobufDeserializer(urpd_product_pb2.UrpProduct,
                                                 {'use.deprecated.format': False})
    config.update(consumer_conf)
    consumer = Consumer(config)
    consumer.subscribe([topic])

    while True:
        try:
            # SIGINT can't be handled when polling, limit timeout to 1 second.
            msg = consumer.poll(1.0)
            if msg is None:
                continue

            urp_product = protobuf_deserializer(msg.value(), SerializationContext(topic, MessageField.VALUE))

            if urp_product is not None:
                print(F"Received product with request_id -  {urp_product.request_id}")
        except KeyboardInterrupt:
            break

    consumer.close()


if __name__ == '__main__':
    main()