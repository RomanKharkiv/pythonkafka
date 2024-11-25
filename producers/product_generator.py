import random
from datetime import datetime 
import uuid


def generate_urpid():
    """Generate a unique URPID with at least 20 characters."""
    return str(uuid.uuid4()).replace("-", "")

def generate_alternative_id():
    """Generate a structured alternative_id with coding_system details."""
    prefixes = ["ABC", "DFG", "HIJ", "KLM", "NOP", "QRS", "TUV", "WXY"]
    suffix = str(random.randint(1000, 9999))
    return {
        "alternative_id": f"{random.choice(prefixes)}-{suffix}",
        "coding_system": {
            "coding_system_code": random.choice(["GSMR", "REGM", "BNCH"]), 
            #"coding_system_display_name": "some name",     # will be generated in consumers
            "url_prefix": random.choice(["https://link_1", "https://link_2", "https://link_3"])
            #"trusted_system": random.choice(["GSMR", "REGM", "BNCH"])    # will be a key in final
        }
    }

def generate_object(urpid):
    """Generate a 'new_object' based on the given URPID."""
    return {
        "urpid": urpid,
        "aliases": [f"ALIAS-{random.randint(1000, 9999)}"],
        "object_type": random.choice(["BATCH", "COMP", "SMPL"]),
        "object_subtype": random.choice(["SMMOL", "PLMD", "MOL", "RNASS", "RNAASS", 
                                         "RNADUP", "RNATRI", "LEGOLIG", "REGCL", "CLON", 
                                         "DCONJ", "LNP", "LIP", "BATCH", "SMPL", "MXT"]),
        "alternative_ids": [generate_alternative_id() for _ in range(random.randint(1, 3))]
    }

def generate_relationship(parent_urpid, child_urpid):
    """Generate a relationship entry between parent and child URPIDs."""
    # prefixes = "COMP"
    # suffix = ["COMP", "BATCH", "SMPL"]
    return {
        # "relationship_type": f"{prefixes}-{random.choice(suffix)}",
        "relationship_type": random.choice(["COMP_BATCH", "BATCH_SMPL", "COMP_SMPL", "MXT_COMP"]),
        "parent_object_urpid": parent_urpid,
        "child_object_urpid": child_urpid
    }

def generate_random_datetime():
    now = datetime.now()
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")

def generate_random_trusted_system():
    trusted_system = random.choice(["GSMR", "REGM", "BNCH"])
    return trusted_system

def generate_data():
    """Generate the main data structure adhering to the schema."""
    
    # Generate a list of unique URPIDs
    urpids = [generate_urpid() for _ in range(4)]
    
    # Generate new_objects using these URPIDs
    new_objects = [generate_object(urpid) for urpid in urpids]

    # Generate relationships using the generated URPIDs
    relationships = []
    for i in range(1, len(urpids)):
        parent_urpid = urpids[0]  # Keep the first URPID as the common parent
        child_urpid = urpids[i]
        relationships.append(generate_relationship(parent_urpid, child_urpid))

    # Generate the final data structure
    data = {
        "request_id": str(uuid.uuid4()),
        "transaction": {
            "trusted_system": generate_random_trusted_system(),
            "new_objects": new_objects,
            "update_objects": [],
            "relationships": relationships,
            "date_time": generate_random_datetime()
        }
    }

    return data