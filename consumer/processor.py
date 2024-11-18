from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean, inspect, update    #, DateTime
from sqlalchemy.dialects.postgresql import UUID    #, JSON
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError
import uuid
import datetime
import json
import os


# Define the SQLAlchemy base and engine
Base = declarative_base()
user = os.getenv('POSTGRES_USER', 'postgres')
password = os.getenv('POSTGRES_PASSWORD', 'postgres')
db = os.getenv('POSTGRES_DB', 'postgres')

#Define ORM models
class TrustedSystem(Base):
    __tablename__ = "trusted_system"
    trusted_system_id = Column(Integer, primary_key=True, autoincrement=True)
    trusted_system_code = Column(String, unique=True)
    trusted_system_name = Column(String)
    is_registrar = Column(Boolean, nullable=False, default=False)
    
    @classmethod
    def insert_trusted_system(cls, session, system_code, system_name, is_registrar=True):
        # Check if a trusted system with the same system_code already exists
        existing_trusted_system = session.query(cls).filter_by(trusted_system_code=system_code).first()
        
        # If it does not exist, insert it
        if not existing_trusted_system:
            trusted_system = cls(
                trusted_system_name=system_name,
                trusted_system_code=system_code,
                is_registrar=is_registrar
            )
            session.add(trusted_system)
            session.flush()
            print(f"Inserted new TrustedSystem: {system_code}")
            return trusted_system
        else:
            print(f"TrustedSystem with code {system_code} already exists.")
            return existing_trusted_system
    
    @classmethod
    def initialize_default_trusted_systems(cls, session):
        #Initialize the table with a predefined set of trusted systems if not already present.
        initial_values = [
            {"trusted_system_name": "GSMR", "trusted_system_code": "GSMR", "is_registrar": True},
            {"trusted_system_name": "RegMol", "trusted_system_code": "REGM", "is_registrar": True},
            {"trusted_system_name": "Benchling", "trusted_system_code": "BNCH", "is_registrar": True}
        ]

        # Insert each default value only if it doesn't already exist
        for value in initial_values:
            cls.insert_trusted_system(
                session,
                system_code=value["trusted_system_code"],
                system_name=value["trusted_system_name"],
                is_registrar=value["is_registrar"]
            )

        session.commit()
        print("TrustedSystem table initialized with default values.")

    @classmethod
    def initialize_trusted_systems(cls, session, kafka_message_system_code, kafka_message_system_name):
        # Insert only if the trusted system with the provided code is not already in the database
        cls.insert_trusted_system(session, kafka_message_system_code, kafka_message_system_name)
        session.commit()

    @classmethod
    def process_trusted_system(cls, session, system_code):
        if system_code:
            cls.insert_trusted_system(session, system_code, system_code)
        #else:
        #    print("Trusted system code missing or invalid.")




class CodingSystem(Base):
    __tablename__ = "coding_system"
    coding_system_id = Column(Integer, primary_key=True)
    coding_system_code = Column(String)
    coding_system_display_name = Column(String)
    trusted_system_id = Column(Integer, ForeignKey("trusted_system.trusted_system_id"))
    url_prefix = Column(String)

    trusted_system = relationship("TrustedSystem", backref="coding_systems")

    CODE_TO_CODING_SYSTEM_DISPLAY_NAME_MAP = {
        "REGM": "RegMol",
        "GSMR": "GSMR",
        "BNCH": "Benchling"
    }

    @classmethod
    def insert_coding_system(cls, session, coding_system_code, url_prefix, display_name=None):
        display_name = display_name or cls.CODE_TO_CODING_SYSTEM_DISPLAY_NAME_MAP.get(coding_system_code, "Unknown")

        trusted_system = session.query(TrustedSystem).filter_by(trusted_system_code=coding_system_code).first()
        trusted_system_id = trusted_system.trusted_system_id if trusted_system else None

        coding_system = cls(
            coding_system_code=coding_system_code,
            coding_system_display_name=display_name,
            trusted_system_id=trusted_system_id,
            url_prefix=url_prefix
        )
        session.add(coding_system)
        session.flush()
        return coding_system

    @classmethod
    def initialize_default_coding_systems(cls, session):
        initial_values = [
            {"coding_system_code": "REGM", "display_name": "RegMol", "url_prefix":"https://link_1_ONE"},
            {"coding_system_code": "GSMR", "display_name": "GSMR", "url_prefix":"https://link_2_TWO"},
            {"coding_system_code": "BNCH", "display_name": "Benchling", "url_prefix":"https://link_3_THREE"}
        ]
        for value in initial_values:
            cls.insert_coding_system(
                session,
                coding_system_code=value["coding_system_code"],
                display_name=value["display_name"],
                url_prefix = value["url_prefix"]
            )
        session.commit()
        print("CodingSystem table initialized with default values.")

    @classmethod
    def get_or_create_coding_system(cls, session, coding_system_code, url_prefix):
        coding_system = session.query(cls).filter_by(coding_system_code=coding_system_code).first()
        if not coding_system:
            coding_system = cls.insert_coding_system(session, coding_system_code, url_prefix)
        return coding_system.coding_system_id





class ObjectType(Base):
    __tablename__ = "object_type"
    object_type_id = Column(Integer, primary_key=True)
    object_type_code = Column(String)
    object_type_display_name = Column(String)
    parent_object_type = Column(ForeignKey("object_type.object_type_id"))

    parent = relationship("ObjectType", remote_side=[object_type_id], backref="subtypes")
    
    CODE_TO_OBJECT_TYPE_DISPLAY_NAME_MAP = {
        "COMP": "Compound",
        "BATCH": "Batch",
        "SMPL": "Sample"
    }

    @classmethod
    def insert_object_type(cls, session, object_type_code, display_name=None, parent_object_type=None):
        
        # Use the mapped display name
        display_name = display_name or cls.CODE_TO_OBJECT_TYPE_DISPLAY_NAME_MAP.get(object_type_code, "Unknown")

        object_type = cls(
            object_type_code=object_type_code,
            object_type_display_name=display_name,
            parent_object_type=parent_object_type
        )
        session.add(object_type)
        session.flush()
        return object_type
    
    @classmethod
    def get_or_create_object_type(cls, session, object_type_code):
        obj_type = session.query(cls).filter_by(object_type_code=object_type_code).first()
        if not obj_type:
            obj_type = cls.insert_object_type(session, object_type_code)
        return obj_type.object_type_id





class Object(Base):
    __tablename__ = "object"
    urpid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    object_subtype_display_name = Column(String)
    object_subtype = Column(String)
    aliases = Column(String)
    object_type_id = Column(ForeignKey("object_type.object_type_id"))
    version = Column(Integer, nullable=False, default=0)

    object_type = relationship("ObjectType")
    alternatives = relationship("Alternative", back_populates="object")

    #Define a mapping from code to display name
    CODE_TO_OBJECT_SUBTYPE_DISPLAY_NAME_MAP = {
        "SMMOL": "Small Molecule",
        "PLMD": "Plasmid",
        "BATCH": "Batch",
        "MOL": "Molecule",
        "RNASS": "RNA Sense Strand",
        "RNAASS": "RNA Antisense Strand",
        "RNADUP": "RNA Duplex",
        "RNATRI": "RNA Triplex",
        "LEGOLIG": "Lego Oligo",
        "REGCL": "Registered Cell Line",
        "CLON": "Clone",
        "DCONJ": "Drug Conjugate",
        "LNP": "LNP",
        "LIP": "Lipids",
        "BATCH": "Batch",
        "SMPL": "Sample",
        "MXT": "Mixture"
    }

    @classmethod
    def insert_object(cls, session, urpid, object_subtype, object_type_id):

        # Use the mapped display name
        display_name = cls.CODE_TO_OBJECT_SUBTYPE_DISPLAY_NAME_MAP.get(object_subtype, "Unknown")
        
        # Try to insert a new row or check for an existing one
        existing_obj = session.query(cls).filter_by(urpid=urpid).first()

        if existing_obj:
            # If it exists, update it with OCC
            updated = session.execute(
                update(cls)
                .where(cls.urpid == urpid)
                .where(cls.version == existing_obj.version)  # OCC condition
                .values(
                    object_subtype=object_subtype,
                    object_subtype_display_name=display_name,
                    object_type_id=object_type_id,
                    version=existing_obj.version + 1  # Increment version
                )
            )
            # Check if the update succeeded
            if updated.rowcount == 0:
                raise StaleDataError("OCC Conflict: The row was updated by another transaction.")
            return existing_obj
        else:
            # Insert if it doesn’t already exist
            obj = cls(
                urpid=urpid,
                object_subtype=object_subtype,
                object_subtype_display_name=display_name,
                object_type_id=object_type_id
            )
            session.add(obj)
            session.flush()
            return obj
    
    # Metod of updating aliases in Objects (creating list of altern_ids from Alternatives table) 
    def update_aliases(self, session):
        self.aliases = ', '.join([f"{self.object_subtype}|{alt.alternative_id}" for alt in self.alternatives])
        session.commit()
    
    @classmethod
    def process_objects(cls, session, objects_data):
        object_map = {}
        for obj_data in objects_data:
            obj = cls.insert_object(
                session,
                urpid=obj_data["urpid"],
                object_subtype=obj_data["object_subtype"],
                object_type_id=ObjectType.get_or_create_object_type(session, obj_data["object_type"])
            )
            object_map[obj_data["urpid"]] = obj
            obj.process_alternatives(session, obj_data["alternative_ids"])
            obj.update_aliases(session)

        return object_map

    def process_alternatives(self, session, alternative_ids):
        for alt_data in alternative_ids:
            Alternative.process_alternative(session, alt_data, self.urpid)






class Alternative(Base):
    __tablename__ = "alternative"
    alternative_id = Column(String, primary_key=True)
    coding_system_id = Column(ForeignKey("coding_system.coding_system_id"))
    object_urpid = Column(ForeignKey("object.urpid"))
    version = Column(Integer, nullable=False, default=0)

    object = relationship("Object", back_populates="alternatives")
    coding_system = relationship("CodingSystem")

    @classmethod
    def insert_alternative(cls, session, alternative_id, coding_system_id, object_urpid):
        alt = cls(
            alternative_id=alternative_id,
            coding_system_id=coding_system_id,
            object_urpid=object_urpid
        )
        session.add(alt)
        #session.flush()
        return alt
    
    @classmethod
    def process_alternative(cls, session, alt_data, object_urpid):
        coding_system_data = alt_data.get("coding_system")
        coding_system_code, url_prefix = cls.parse_coding_system_data(coding_system_data)

        if coding_system_code:
            coding_system_id = CodingSystem.get_or_create_coding_system(session, coding_system_code, url_prefix)
            cls.insert_alternative(session, alt_data["alternative_id"], coding_system_id, object_urpid)
        else:
            print("Missing or invalid coding system data.")

    @staticmethod
    def parse_coding_system_data(coding_system_data):
        if isinstance(coding_system_data, str):
            return coding_system_data, 'default_url_prefix'
        elif isinstance(coding_system_data, dict):
            return coding_system_data.get("coding_system_code"), coding_system_data.get("url_prefix", 'default_url_prefix')
        else:
            return None, None






class RelationshipType(Base):
    __tablename__ = "relationship_type"
    relationship_type_id = Column(Integer, primary_key=True)
    relationship_type_code = Column(String)
    relationship_type_display_name = Column(String)
    
    # Define a mapping from code to display name
    CODE_TO_RELATIONSHIP_TYPE_DISPLAY_NAME_MAP = {
        "COMP_BATCH": "Compound has Batches",
        "BATCH_SMPL": "Batch has Samples",
        "COMP_SMPL": "Compound has Samples",
        "MXT_COMP": "Mixture made of components"
    }

    @classmethod
    def insert_relationship_type(cls, session, relationship_type_code, display_name=None):
        
        # Use the mapped display name
        display_name = display_name or cls.CODE_TO_RELATIONSHIP_TYPE_DISPLAY_NAME_MAP.get(relationship_type_code, "Unknown")

        relationship_type = cls(
            relationship_type_code=relationship_type_code,
            relationship_type_display_name=display_name
        )
        session.add(relationship_type)
        session.flush()
        return relationship_type
    
    @classmethod
    def get_or_create_relationship_type(cls, session, relationship_type_code):
        rel_type = session.query(cls).filter_by(relationship_type_code=relationship_type_code).first()
        if not rel_type:
            rel_type = cls.insert_relationship_type(session, relationship_type_code)
        return rel_type.relationship_type_id






class Relationship(Base):
    __tablename__ = "relationship"
    relationship_id = Column(Integer, primary_key=True)
    relationship_code = Column(String)
    relationship_type_id = Column(ForeignKey("relationship_type.relationship_type_id"))
    parent_object = Column(ForeignKey("object.urpid"))
    child_object = Column(ForeignKey("object.urpid"))
    version = Column(Integer, nullable=False, default=0)

    relationship_type = relationship("RelationshipType")
    parent = relationship("Object", foreign_keys=[parent_object])
    child = relationship("Object", foreign_keys=[child_object])

    @classmethod
    def insert_relationship(cls, session, relationship_code, relationship_type_id, parent_object, child_object):
        parent_exists = session.query(Object).filter_by(urpid=parent_object).first()
        child_exists = session.query(Object).filter_by(urpid=child_object).first()

        if not parent_exists or not child_exists:
            print(f"Skipping relationship insertion due to missing parent or child object. Parent: {parent_object}, Child: {child_object}")
            return None

        relationship = cls(
            relationship_code=relationship_code,
            relationship_type_id=relationship_type_id,
            parent_object=parent_object,
            child_object=child_object
        )
        session.add(relationship)
        session.flush()
        return relationship
    
    @classmethod
    def process_relationships(cls, session, relationships_data, object_map):
        for rel_data in relationships_data:
            relationship_type_code = rel_data["relationship_type"]
            parent_urpid = rel_data["parent_object_urpid"]
            child_urpid = rel_data["child_object_urpid"]

            if parent_urpid in object_map and child_urpid in object_map:
                relationship_type_id = RelationshipType.get_or_create_relationship_type(session, relationship_type_code)
                cls.insert_relationship(session, relationship_type_code, relationship_type_id, parent_urpid, child_urpid)
            else:
                print(f"Skipping relationship due to missing parent or child object: {parent_urpid}, {child_urpid}")






class Request(Base):
    __tablename__ = "request"
    request_id = Column(String, primary_key=True)
    status = Column(Boolean)
    date_time = Column(String)

    @classmethod
    def insert_request(cls, session, request_id, date_time, status=True):
        if not session.query(cls).filter_by(request_id=request_id).first():
            formatted_date_time = date_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            request = cls(
                request_id=request_id,
                date_time=formatted_date_time,
                status=status
            )
            session.add(request)
            session.flush()
        else:
            print(f"Request with ID {request_id} already exists.")



# Parsers for date and message
def parse_message(message):
    if isinstance(message, str):
        try:
            return json.loads(message)
        except json.JSONDecodeError:
            print("Failed to decode JSON message")
            return None
    elif isinstance(message, dict):
        return message
    else:
        print("Unexpected message format")
        return None

#Date parser
def parse_date(date_string):
    return datetime.datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")


# # Drop all tables
# Base.metadata.drop_all(engine)
# # Create all tables
# Base.metadata.create_all(engine)

# Populate with initial values Trusted_System and Codung System
#TrustedSystem.initialize_default_trusted_systems(session)
#CodingSystem.initialize_default_coding_systems(session)

# Configure the database
DATABASE_URL = f"postgresql://{user}:{password}@postgres:5432/{db}"
engine = create_engine(DATABASE_URL, isolation_level="REPEATABLE READ")
Session = sessionmaker(bind=engine)
session = Session()

# Only create tables if they don't exist
def initialize_database():
    # Create an inspector object
    inspector = inspect(engine)
    
    # Check if the 'trusted_system' table exists
    if not inspector.has_table("trusted_system"):
        print("Tables do not exist. Creating new tables.")
        # If table does not exist, create all tables
        Base.metadata.create_all(engine)
        
        # Populate with initial values for TrustedSystem and CodingSystem
        TrustedSystem.initialize_default_trusted_systems(session)
        CodingSystem.initialize_default_coding_systems(session)
    else:
        print("Tables already exist. Skipping creation.")

initialize_database()


def process_message(session, message):
    data = parse_message(message)
    if not data:
        return

    # Process Trusted System and Coding System
    trusted_system_code = data.get("trusted_system_code")
    TrustedSystem.process_trusted_system(session, trusted_system_code)

    # Process Request
    request_data = data.get("request_id")
    date_time = parse_date(data["transaction"]["date_time"])
    request = Request.insert_request(session, request_data, date_time)

    try: 
        # Process Objects and Alternatives
        object_map = Object.process_objects(session, data["transaction"]["new_objects"])

        # Process Relationships
        Relationship.process_relationships(session, data["transaction"]["relationships"], object_map)

        session.commit()
    except (IntegrityError, StaleDataError) as e:
        session.rollback()
        print(f"Concurency conflict detected: {e}")
        # Ohere I can implement logic of retry or log the failure for later processing.     !!!!!!!!!!!!!!!


def process_message_with_retry(session, message, retries=3):
    """
    Process a Kafka message with retry logic to handle concurrency conflicts.
    
    :param session: SQLAlchemy session to interact with the database.
    :param message: Kafka message containing data for processing.
    :param retries: Number of retry attempts in case of concurrency conflicts.
    """
    for attempt in range(retries):
        try:
            # Attempt to process the message
            process_message(session, message)
            print("OCC: Message processed successfully.")
            break  # Exit the loop if processing is successful

        except StaleDataError:
            # Rollback the session in case of concurrency conflict
            session.rollback()
            
            if attempt < retries - 1:
                # Retry if we haven't reached the maximum retry count
                print(f"Retrying due to concurrency conflict (attempt {attempt + 1})")
            else:
                # Log or handle the failure after max retries
                print("Max retries reached. Skipping message.")

        except Exception as e:
            # Handle other potential exceptions (e.g., database issues)
            session.rollback()
            print(f"An error occurred: {e}")
            break  # Break the loop on non-recoverable errors
        finally:
            session.close()