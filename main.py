from client import ACTelemetryClient
from constants import SUBSCRIBE_UPDATE
import time


def main():
    client = ACTelemetryClient("127.0.0.1")
    
    try:
        print(f"[1] Connecting to Assetto Corsa...")
        response = client.connect()
        
        print(f"\nConnected to Assetto Corsa!")
        print(f"Car: {response.carName}")
        print(f"Driver: {response.driverName}")
        print(f"Track: {response.trackName}")
        
        print("\n[2] Subscribing to telemetry...")
        client.subscribe(SUBSCRIBE_UPDATE)
        
        # Show telemetry data
        def on_telemetry(telemetry):
            gear = telemetry.gear_text()
            
            print(f"\rSpeed: {telemetry.speed_Kmh:6.1f} km/h | "
                  f"RPM: {telemetry.engineRPM:6.0f} | "
                  f"Gear: {gear:>2} | "
                  f"Gas: {telemetry.gas:3.0%} | "
                  f"Lap: {telemetry.lapTime/1000:6.2f}s", end='')
        
        client.add_callback('telemetry', on_telemetry)
        
        print("\n[3] Receiving telemetry... Press Ctrl + C to stop\n")
        client.start_receiving()
        
        # Keep running
        while True:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\nStopping...")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n[4] Disconnecting...")
        client.dismiss()

if __name__ == "__main__":
    main()