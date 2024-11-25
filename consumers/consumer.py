import os

from confluent_kafka import Consumer
from confluent_kafka.schema_registry.json_schema import JSONDeserializer
from confluent_kafka.serialization import SerializationContext, MessageField
from kafka_config import config, consumer_conf
from processor import process_message_with_retry, Session


with open('schema.json', 'r') as f:
    schema_str = f.read()

def print_assignment(cons, partitions):
    print(f'Assignment partition for {cons}: {partitions}')


json_deserializer = JSONDeserializer(schema_str)
topic = os.getenv('KAFKA_TOPIC', 'result.overall')

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
        message = json_deserializer(raw_message, SerializationContext(topic, MessageField.VALUE))  #event.value()
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
    # finally:
    #     session.close()

consumer.close()
