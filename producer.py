import json
import random
import datetime
import time
import uuid

from kafka import KafkaProducer
from kafka.client_async import log


topic = 'object-created'
broker1 = 'kafka1:29092'

def generate_random_urpid():
    return f"{uuid.uuid4()}"


def generate_random_request_id():
    return f"gsmr_{random.randint(1000, 9999)}"


def generate_random_alternative_id():
    return f"{random.randint(10000, 99999)}"


def generate_random_datetime():
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")


def generate_new_object():
    return {
        "urpid": generate_random_urpid(),
        "object_type": random.choice(["LSN", "SMPL", "BTCH"]),
        "object_subtype": random.choice(["SMPL", "SMMOL", "REGMOL"]),
        "aliases": [f"Alias_{random.randint(1, 10)}", f"Alias_{random.randint(11, 20)}"],
        "alternative_ids": [
            {
                "alternative_id": generate_random_alternative_id(),
                "coding_system": random.choice(["GSMR", "BNCH"])
            }
        ]  # ,
        # "dateTime": generate_random_datetime(),
    }


def generate_update_object():
    return {
        "urpid": generate_random_urpid(),
        "object_type": random.choice(["LSN", "SMPL", "BTCH"]),
        "object_subtype": random.choice(["SMPL", "SMMOL", "REGMOL"]),
        "alternative_ids": [
            {
                "alternative_id": generate_random_alternative_id(),
                "coding_system": random.choice(["GSMR", "BNCH"])
            }
        ]
    }


def generate_relationship(parent_urpid, child_urpid):
    return {
        "relationship_type": random.choice(["LSN", "SMPL", "BTCH"]) + "_" + random.choice(["LSN", "SMPL", "BTCH"]),
        "parent_object_urpid": parent_urpid,
        "child_object_urpid": child_urpid
    }


def generate_transaction():
    dateTime = generate_random_datetime()
    request_id = generate_random_request_id()
    new_object = generate_new_object()
    update_object = generate_update_object()
    relationship = generate_relationship(generate_random_urpid(), new_object["urpid"])

    return {
        "dateTime": dateTime,
        "trusted_system": random.choice(["GSMR", "REGMOL", "BNCH"]),
        "request_id": request_id,
        "new_objects": [new_object],
        "update_objects": [update_object],
        "relationships": [relationship]
    }


def generate_data():
    return {
        "request_id": generate_random_request_id(),
        # "transactions": [generate_transaction() for _ in range(random.randint(1, 5))]
        "transactions": generate_transaction()
    }


producer = KafkaProducer(bootstrap_servers=broker1,
                         value_serializer=lambda m: json.dumps(m).encode('ascii'),
                         retries=5)
def on_send_success(record_metadata):
    print(record_metadata.topic)
    print(record_metadata.partition)
    print(record_metadata.offset)


def on_send_error(excp):
    log.error('I am an errback', exc_info=excp)


while True:
    fake_data = generate_data()
    print(json.dumps(fake_data, indent=2))
    producer.send(topic, fake_data).add_callback(on_send_success).add_errback(on_send_error)
    producer.flush()
    time.sleep(5)
