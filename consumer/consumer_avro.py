import os
from confluent_kafka import Consumer
from confluent_kafka.serialization import SerializationContext, MessageField
from config import config, consumer_conf, sr_config
from processor import process_message_with_retry, Session
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer

with open('schema.avsc', 'r') as f:
    schema_str = f.read()

def print_assignment(cons, partitions):
    print(f'Assignment partition for {cons}: {partitions}')

topic = os.getenv('KAFKA_TOPIC', 'result.overall.avro')

schema_registry_client = SchemaRegistryClient(sr_config)
avro_deserializer = AvroDeserializer(schema_registry_client, schema_str)

config.update(consumer_conf)
consumer = Consumer(config)
consumer.subscribe([topic], on_assign=print_assignment)

while True:
    session = Session()
    try:
        event = consumer.poll(1.0)
        if event is None:
            continue
        
        raw_message = event.value()
        message = avro_deserializer(raw_message, SerializationContext(event.topic(), MessageField.VALUE))

        if message is not None:
            print(f'Latest message {message}')
            try:
                if isinstance(message, dict):
                    process_message_with_retry(session, message, 3)
                    print("Data committed successfully.")
                else:
                    print("Received message is not in the expected format (not a dictionary). Skipping message.")
            except Exception as e:
                session.rollback()
                print(f"Error inserting data: {e}")

    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

consumer.close()
