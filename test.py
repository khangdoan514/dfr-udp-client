from kafka import KafkaProducer
import socket

# Tailscale IP
broker = "100.84.194.114:9092"

try:
    producer = KafkaProducer(bootstrap_servers=[broker], request_timeout_ms=5000)
    print(f"Successfully connected to {broker}")
except Exception as e:
    print(f"Failed to connect: {e}")