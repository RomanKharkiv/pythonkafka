from protobuf import urpd_product_pb2
from confluent_kafka import Consumer
from confluent_kafka.serialization import SerializationContext, MessageField
from confluent_kafka.schema_registry.protobuf import ProtobufDeserializer
from kafka_config import config, consumer_conf
import os
from protobuf_to_dict import protobuf_to_dict
from processor import process_message, Session


def main():
    topic = os.getenv('KAFKA_TOPIC', 'result.overall.proto')

    protobuf_deserializer = ProtobufDeserializer(urpd_product_pb2.UrpProduct,
                                                 {'use.deprecated.format': False})

    def print_assignment(cons, partitions):
        print(f'Assignment partition for {cons}: {partitions}')

    config.update(consumer_conf)
    consumer = Consumer(config)
    consumer.subscribe([topic], on_assign=print_assignment)

    while True:
        try:
            session = Session()
            msg = consumer.poll(1.0)
            if msg is None:
                continue

            urp_object = protobuf_deserializer(msg.value(), SerializationContext(topic, MessageField.VALUE))

            if urp_object is not None:
                message = protobuf_to_dict(urp_object)
                if isinstance(message, dict):
                    process_message(session, message)
                    print("Data committed successfully.")
                else:
                    print("Received message is not in the expected format (not a dictionary). Skipping message.")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
     
    consumer.close()


if __name__ == '__main__':
    main()