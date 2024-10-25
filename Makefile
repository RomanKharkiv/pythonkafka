producer_pb: protobuf/urpd_product.proto
	protoc -I=. --python_out=. protobuf/urpd_product.proto
	python3 protobuf_producer.py

consumer_pb: protobuf/urpd_product.proto
	protoc -I=. --python_out=. protobuf/urpd_product.proto
	python3 protobuf_consumer.py



