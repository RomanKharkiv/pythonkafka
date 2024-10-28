sr_config = {
    'url': 'http://schemaregistry:8085'
}
config = {
    'bootstrap.servers': "kafka-broker-1:9092, kafka-broker-2:9092, kafka-broker-3:9092"
}
consumer_conf = {
    'group.id': 'test',
    'auto.offset.reset': "earliest"
}
