# Run this to test if topic exists
from confluent_kafka import Producer
import json

producer = Producer({'bootstrap.servers': '100.84.194.114:9092'})

try:
    producer.produce('ac-telemetry', b'test')
    producer.flush()
    print("Topic exists or auto-creation is enabled")
except Exception as e:
    print(f"Error: {e}")