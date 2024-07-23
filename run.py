import streamlit as st
import ecdsa
import hashlib
import time
import json
import websocket

# Function to generate a private key
def generate_private_key():
    return ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)

# Function to get a public key from a private key
def get_public_key(private_key):
    return private_key.get_verifying_key()

# Function to sign an event
def sign_event(event, private_key):
    event_data = json.dumps(event, sort_keys=True)
    event_hash = hashlib.sha256(event_data.encode('utf-8')).hexdigest()
    signature = private_key.sign(event_hash.encode('utf-8')).hex()
    return signature

# Function to connect to a relay
def connect_relay(url):
    ws = websocket.WebSocket()
    ws.connect(url)
    return ws

# Function to publish an event
def publish_event(ws, event):
    ws.send(json.dumps(event))
    response = ws.recv()
    return json.loads(response)

# Streamlit app
st.title("Nostr Voting App")

if 'private_key' not in st.session_state:
    st.session_state.private_key = None
    st.session_state.public_key = None
    st.session_state.is_authenticated = False
    st.session_state.votes = {'optionA': 0, 'optionB': 0}

if st.session_state.is_authenticated:
    st.write(f"Private key: {st.session_state.private_key.to_string().hex()}")
    st.write(f"Public key: {st.session_state.public_key.to_string().hex()}")
    
    relay_url = "wss://relay.damus.io"
    ws = connect_relay(relay_url)
    st.write(f"Connected to {relay_url}")

    vote_option = st.selectbox("Vote for:", ["Option A", "Option B"])
    if st.button("Submit Vote"):
        event = {
            "kind": 1,
            "pubkey": st.session_state.public_key.to_string().hex(),
            "created_at": int(time.time()),
            "tags": [],
            "content": f"Vote: {vote_option}",
        }
        event['id'] = hashlib.sha256(json.dumps(event, sort_keys=True).encode('utf-8')).hexdigest()
        event['sig'] = sign_event(event, st.session_state.private_key)
        response = publish_event(ws, event)
        if response.get('ok'):
            st.success("Vote published")
        else:
            st.error(f"Failed to publish vote: {response.get('reason')}")
    
    if st.button("Load Votes"):
        request = json.dumps({"kinds": [1]})
        ws.send(request)
        response = ws.recv()
        events = json.loads(response)
        vote_counts = {'optionA': 0, 'optionB': 0}
        for event in events:
            if event['content'] == "Vote: optionA":
                vote_counts['optionA'] += 1
            elif event['content'] == "Vote: optionB":
                vote_counts['optionB'] += 1
        st.session_state.votes = vote_counts
    
    st.write(f"Option A Votes: {st.session_state.votes['optionA']}")
    st.write(f"Option B Votes: {st.session_state.votes['optionB']}")

else:
    st.write("Login or Sign Up with your Nostr Private Key")

    if st.button("Generate Private Key"):
        private_key = generate_private_key()
        public_key = get_public_key(private_key)
        st.session_state.private_key = private_key
        st.session_state.public_key = public_key
        st.session_state.is_authenticated = True
        st.success("Private key generated and logged in")

    private_key_input = st.text_input("Enter your private key", type="password")
    if st.button("Login"):
        try:
            private_key = ecdsa.SigningKey.from_string(bytes.fromhex(private_key_input), curve=ecdsa.SECP256k1)
            public_key = get_public_key(private_key)
            st.session_state.private_key = private_key
            st.session_state.public_key = public_key
            st.session_state.is_authenticated = True
            st.success("Logged in successfully")
        except Exception as e:
            st.error(f"Invalid private key: {e}")
