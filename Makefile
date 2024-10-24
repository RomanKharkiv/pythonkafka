proto: protobuf/urpd_product.proto
	protoc -I=. --python_out=. protobuf/urpd_product.proto
	python3 protobuf_producer.py


clean:
	rm -f $(TARGET_DIR)/protobuf/*_pb2.py
