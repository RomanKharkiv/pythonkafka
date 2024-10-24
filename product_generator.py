import random
import datetime
import uuid

def generate_random_urpid():
    return f"{uuid.uuid4()}"


def generate_random_request_id():
    return f"gsmr_{random.randint(1000, 9999)}"


def generate_random_alternative():
    return {
        "alternative_id": f"{random.randint(10000, 99999)}",
        "coding_system" : random.choice(["GSMR", "BNCH"])
    }



def generate_random_datetime():
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")


def generate_new_object():
    return {
        "urpid": generate_random_urpid(),
        "object_type": random.choice(["LSN", "SMPL", "BTCH"]),
        "object_subtype": random.choice(["SMPL", "SMMOL", "REGMOL"]),
        "aliases": [f"Alias_{random.randint(1, 10)}", f"Alias_{random.randint(11, 20)}"],
        "alternative_ids": [generate_random_alternative() for _ in range(10)]
        }


def generate_update_object():
    return {
        "urpid": generate_random_urpid(),
        "aliases": [f"Alias_{random.randint(1, 10)}", f"Alias_{random.randint(11, 20)}"],
        "object_type": random.choice(["LSN", "SMPL", "BTCH"]),
        "object_subtype": random.choice(["SMPL", "SMMOL", "REGMOL"]),
        "alternative_ids": [generate_random_alternative() for _ in range(10)]
    }


def generate_relationship(parent_urpid, child_urpid):
    return {
        "relationship_type": random.choice(["LSN", "SMPL", "BTCH"]) + "_" + random.choice(["LSN", "SMPL", "BTCH"]),
        "parent_object_urpid": parent_urpid,
        "child_object_urpid": child_urpid
    }


def generate_transaction():
    request_id = generate_random_request_id()
    new_object = generate_new_object()
    update_object = generate_update_object()
    relationship = generate_relationship(generate_random_urpid(), new_object["urpid"])
    dateTime = generate_random_datetime()

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
        "transactions": [generate_transaction()]
    }