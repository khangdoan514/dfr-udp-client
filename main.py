from confluent_kafka import Producer
from client import ACTelemetryClient
from constants import SUBSCRIBE_UPDATE
import json
import time
import traceback

# Kafka configuration
KAFKA_CONFIG = {
    'bootstrap.servers': '100.84.194.114:9092',
}

KAFKA_TOPIC = 'ic26-decoded-can'

def main():
    # Kafka producer
    kafka_producer = Producer(KAFKA_CONFIG)
    
    # Asessto Corsa client
    client = ACTelemetryClient("127.0.0.1")
    
    def send_to_kafka(telemetry_data):
        try:
            data_json = json.dumps(telemetry_data)
            kafka_producer.produce(
                KAFKA_TOPIC,
                data_json.encode('utf-8'),
            )
            kafka_producer.poll(0)
        except Exception as e:
            print(f"Error sending to Kafka: {e}")
    
    def parse_telemetry_dict(telemetry):
        return {
            'speed_Kmh': telemetry.speed_Kmh,
            'speed_Mph': telemetry.speed_Mph,
            'speed_Ms': telemetry.speed_Ms,
            'timestamp': time.time(),
            'source': 'Assetto Corsa',
            'isAbsEnabled': telemetry.isAbsEnabled,
            'isAbsInAction': telemetry.isAbsInAction,
            'isTcInAction': telemetry.isTcInAction,
            'isTcEnabled': telemetry.isTcEnabled,
            'isInPit': telemetry.isInPit,
            'isEngineLimiterOn': telemetry.isEngineLimiterOn,
            'accG_vertical': telemetry.accG_vertical,
            'accG_horizontal': telemetry.accG_horizontal,
            'accG_frontal': telemetry.accG_frontal,
            'lapTime': telemetry.lapTime,
            'lastLap': telemetry.lastLap,
            'bestLap': telemetry.bestLap,
            'lapCount': telemetry.lapCount,
            'gas': telemetry.gas,
            'brake': telemetry.brake,
            'clutch': telemetry.clutch,
            'engineRPM': telemetry.engineRPM,
            'steer': telemetry.steer,
            'gear': telemetry.gear,
            'gear_display': telemetry.gear_text(),
            'cgHeight': telemetry.cgHeight,
            'wheelAngularSpeed': telemetry.wheelAngularSpeed,
            'slipAngle': telemetry.slipAngle,
            'slipRatio': telemetry.slipRatio,
            'load': telemetry.load,
            'suspensionHeight': telemetry.suspensionHeight,
            'carPositionNormalized': telemetry.carPositionNormalized,
            'carSlope': telemetry.carSlope,
            'carCoordinates': telemetry.carCoordinates
        }
    
    try:
        print(f"Connecting to Assetto Corsa...")
        response = client.connect()
        
        print(f"\nConnected to Assetto Corsa")
        print(f"Car: {response.carName}")
        print(f"Driver: {response.driverName}")
        print(f"Track: {response.trackName}")
        print(f"Kafka Broker: {KAFKA_CONFIG['bootstrap.servers']}")
        print(f"Kafka Topic: {KAFKA_TOPIC}")
        
        print("\nSubscribing to telemetry...")
        client.subscribe(SUBSCRIBE_UPDATE)
        
        # Send session start to Kafka
        init_data = {
            'event_type': 'session_start',
            'car': response.carName,
            'driver': response.driverName,
            'track': response.trackName,
            'timestamp': time.time()
        }
        send_to_kafka(init_data)
        
        # Show data
        def on_telemetry(telemetry):
            gear = telemetry.gear_text()
            
            # Send to Kafka
            data = parse_telemetry_dict(telemetry)
            data['event_type'] = 'telemetry'
            send_to_kafka(data)
            
            # Print
            print(f"\rSpeed: {telemetry.speed_Kmh:6.1f} km/h | "
                  f"RPM: {telemetry.engineRPM:6.0f} | "
                  f"Gear: {gear:>2} | "
                  f"Gas: {telemetry.gas:3.0%} | "
                  f"Lap: {telemetry.lapTime/1000:6.2f}s", end='')
        
        client.add_callback('telemetry', on_telemetry)
        
        print("\nReceiving data...")
        client.start_receiving()
        
        # Keep running
        while True:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\nStopping...")
        
        # Send session end to Kafka
        end_data = {
            'event_type': 'session_end',
            'timestamp': time.time()
        }
        send_to_kafka(end_data)
        kafka_producer.flush()
        print(f"Flushed messages to Kafka topic: {KAFKA_TOPIC}")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        traceback.print_exc()
        
    finally:
        client.dismiss()

if __name__ == "__main__":
    main()