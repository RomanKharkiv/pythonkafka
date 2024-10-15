import json
from kafka import KafkaConsumer


topic = 'object-created'
broker = 'kafka1:29092'

consumer = KafkaConsumer(topic,
                         value_deserializer=lambda m: json.loads(m.decode('ascii')),
                         group_id='my-group2',
                         auto_offset_reset='earliest',
                         bootstrap_servers=[broker]
                         )
for message in consumer:
    print("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
                                         message.offset, message.key,
                                         message.value))
