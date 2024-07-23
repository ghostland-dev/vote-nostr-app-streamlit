import json
import websocket
import threading
import time
import hashlib
import secrets
from ecdsa import SigningKey, SECP256k1
from binascii import hexlify, unhexlify

class NostrClient:
    def __init__(self, relay_url):
        self.relay_url = relay_url
        self.ws = None
        self.connect()

    def on_message(self, ws, message):
        print("Received message:", message)

    def on_error(self, ws, error):
        print("Error:", error)
        self.connect()  # Reconnect on error

    def on_close(self, ws, close_status_code, close_msg):
        print("Connection closed")
        self.connect()  # Reconnect on close

    def on_open(self, ws):
        print("Connection opened")

    def connect(self):
        self.ws = websocket.WebSocketApp(
            self.relay_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        self.thread = threading.Thread(target=self.ws.run_forever)
        self.thread.start()

    def send_event(self, event):
        if not self.ws or not self.ws.sock or not self.ws.sock.connected:
            self.connect()
            time.sleep(1)  # Wait for connection to be established
        self.ws.send(json.dumps(event))

def generate_private_key():
    sk = SigningKey.generate(curve=SECP256k1)
    return hexlify(sk.to_string()).decode()

def get_public_key(private_key):
    sk = SigningKey.from_string(unhexlify(private_key), curve=SECP256k1)
    vk = sk.get_verifying_key()
    return hexlify(vk.to_string()).decode()

def sign_event(event, private_key):
    sk = SigningKey.from_string(unhexlify(private_key), curve=SECP256k1)
    event_id = hashlib.sha256(json.dumps(event).encode()).hexdigest()
    signature = sk.sign(event_id.encode())
    return hexlify(signature).decode()

relay_url = "wss://relay.damus.io"
nostr_client = NostrClient(relay_url)
