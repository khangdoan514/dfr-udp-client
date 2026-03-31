import socket
import threading
from constants import *
from structures import Handshaker, HandshackerResponse, RTCarInfo, RTLap

class ACTelemetryClient:
    def __init__(self, ac_server_ip, port=AC_PORT):
        self.ac_server_ip = ac_server_ip
        self.ac_port = port
        self.socket = None
        self.running = False
        self.subscription_type = None
        self.receive_thread = None
        self.connected = False
        self.callbacks = {'telemetry': [], 'spot': [], 'error': [], 'connection': []}
    
    # Add callback for events
    def add_callback(self, event_type, callback):
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
    
    # Trigger callbacks
    def trigger(self, event_type, data):
        for callback in self.callbacks[event_type]:
            try:
                callback(data)
            except Exception as e:
                print(f"Callback error: {e}")
    
    # Connect to Assetto Corsa
    def connect(self):
        try:
            # Create socket if it doesn't exist
            if self.socket is None:
                print("Creating UDP socket...")
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFFER_SIZE)
                self.socket.settimeout(SOCKET_TIMEOUT)
                print("Socket created successfully")
            
            # Send handshake
            print("Sending handshake...")
            handshake = Handshaker(operationId=HANDSHAKE)
            self.socket.sendto(handshake.pack(), (self.ac_server_ip, self.ac_port))
            print("Handshake sent")
            
            # Receive response
            print("Waiting for response...")
            data, addr = self.socket.recvfrom(BUFFER_SIZE)
            print(f"Received {len(data)} bytes")
            
            response = HandshackerResponse(data)
            if not response.is_valid():
                raise Exception("Invalid handshake response")
            
            self.connected = True
            self.trigger('connection', response)
            return response
            
        except Exception as e:
            print(f"Connection error: {e}")
            if self.socket:
                self.socket.close()
                self.socket = None
            raise
    
    # Subscribe to telemetry
    def subscribe(self, subscription_type=SUBSCRIBE_UPDATE):
        if self.socket is None:
            raise Exception("Socket is None. Call connect() first.")
        if not self.connected:
            raise Exception("Not connected. Call connect() first.")
        
        self.subscription_type = subscription_type
        subscribe = Handshaker(operationId=subscription_type)
        self.socket.sendto(subscribe.pack(), (self.ac_server_ip, self.ac_port))
        print(f"Subscribed to {'UPDATE' if subscription_type == SUBSCRIBE_UPDATE else 'SPOT'}")
    
    # Start receiving data
    def start_receiving(self):
        if self.socket is None:
            raise Exception("Socket is None. Call connect() first.")
        if not self.subscription_type:
            raise Exception("Not subscribed. Call subscribe() first.")
        if self.running:
            print("Already receiving")
            return
        
        self.running = True
        self.receive_thread = threading.Thread(target=self.receive_loop, daemon=True)
        self.receive_thread.start()
        print("Started receiving data")
    
    # Main receive loop
    def receive_loop(self):
        print("Receive loop started")
        while self.running:
            try:
                if self.socket is None:
                    print("Socket is None, stopping receive loop")
                    break
    
                data, addr = self.socket.recvfrom(BUFFER_SIZE)
                if self.subscription_type == SUBSCRIBE_UPDATE:
                    telemetry = RTCarInfo(data)
                    self.trigger('telemetry', telemetry)
                elif self.subscription_type == SUBSCRIBE_SPOT:
                    spot = RTLap(data)
                    self.trigger('spot', spot)
            
            except socket.timeout:
                continue
            except OSError as e:
                if self.running:
                    print(f"Socket error: {e}")
                break
            except Exception as e:
                if self.running:
                    print(f"Receive error: {e}")
                break
        
        print("Receive loop ended")
    
    # Stop receiving data
    def stop_receiving(self):
        self.running = False
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=2.0)
        print("Stopped receiving")
    
    # Disconnect from AC
    def dismiss(self):
        print("Disconnecting...")
        self.stop_receiving()
        if self.socket is not None and self.connected:
            try:
                dismiss = Handshaker(operationId=DISMISS)
                self.socket.sendto(dismiss.pack(), (self.ac_server_ip, self.ac_port))
                print("Dismiss message sent")
            except Exception as e:
                print(f"Error sending dismiss: {e}")
            finally:
                try:
                    self.socket.close()
                    print("Socket closed")
                except:
                    pass
                self.socket = None
                self.connected = False
        
        print("Disconnected!")
    
    # Check if connected
    def is_connected(self):
        return self.socket is not None and self.connected