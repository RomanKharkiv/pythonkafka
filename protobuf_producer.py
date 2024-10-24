# After installing protoc execute the following command from the examples
# directory to regenerate the urpd_product_pb2 module.
# `make`

import argparse
import sys

from protobuf import urpd_product_pb2 as urpd_product
from confluent_kafka import Producer
from confluent_kafka.serialization import StringSerializer, SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.protobuf import ProtobufSerializer
from config import config, sr_config
from product_generator import generate_data

with open('protobuf/urpd_product_pb2.py', 'r') as f:
    file = f.read()
    print(file)


def delivery_report(err, msg):
    if err is not None:
        print("Delivery failed for User record {}: {}".format(msg.key(), err))
        return
    print('User record {} successfully produced to {} [{}] at offset {}'.format(
        msg.key(), msg.topic(), msg.partition(), msg.offset()))


def main():
    topic = 'result.overall.proto'

    schema_registry_client = SchemaRegistryClient(sr_config)
    protobuf_serializer = ProtobufSerializer(urpd_product.UrpProduct,
                                             schema_registry_client,
                                             {'use.deprecated.format': False})

    producer = Producer(config)

    print("Producing records to topic {}. ^C to exit.".format(topic))
    # while True:
    producer.poll(0.0)
    try:
        fake_data = generate_data()
        print(fake_data)
        transactions = []
        for transaction in fake_data['transactions']:
            new_objects = []
            for new_object in transaction['new_objects']:
                alternatives = []
                for alternative in new_object['alternative_ids']:
                    alternatives.append(urpd_product.Alternative_id(alternative_id=alternative['alternative_id'],
                                                                        coding_system=alternative['coding_system']))
                aliases = []
                for alias in new_object['aliases']:
                    aliases.append(urpd_product.Alias(aliases=alias))
                new_objects.append(urpd_product.UrpObject(urpid=new_object['urpid'],
                                                          alias=aliases,
                                                          object_type=new_object['object_type'],
                                                          object_subtype=new_object['object_subtype'],
                                                          alternative_ids=alternatives))

            existing_objects = []
            for existing_object in transaction['update_objects']:
                existing_alternative_ids = []
                for alternative in existing_object['alternative_ids']:
                    existing_alternative_ids.append(urpd_product.Alternative_id(alternative_id=alternative['alternative_id'],
                                                                             coding_system=alternative[
                                                                                 'coding_system']))
                aliases = []
                for alias in existing_object['aliases']:
                    aliases.append(urpd_product.Alias(name=alias))

                existing_objects.append(urpd_product.UrpObject(urpid=existing_object['urpid'],
                                                               alias=aliases,
                                                               object_type=existing_object['object_type'],
                                                               object_subtype=existing_object['object_subtype'],
                                                               alternative_ids=existing_alternative_ids))

            relationship_pb = []
            for relationship in transaction['relationships']:
                relationship_pb.append(urpd_product.Relationship(relationship_type=relationship['relationship_type'],
                                                                 parent_object_urpid=relationship[
                                                                     'parent_object_urpid'],
                                                                 child_object_urpid=relationship['child_object_urpid']))

            transactions.append(urpd_product.Transaction(request_id=transaction['request_id'],
                                                         trusted_system=transaction['trusted_system'],
                                                         new_objects=new_objects,
                                                         existing_objects=existing_objects,
                                                         relationships=relationship_pb,
                                                         date_time=transaction['dateTime']))

        urp_product = urpd_product.UrpProduct(request_id=fake_data['request_id'],
                                              transactions=transactions)

        producer.produce(topic=topic, partition=0,
                         value=protobuf_serializer(urp_product, SerializationContext(topic, MessageField.VALUE)),
                         on_delivery=delivery_report)

        producer.flush()


    except ValueError:
        print("Could not convert data to an integer.")
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise


if __name__ == '__main__':
    main()
