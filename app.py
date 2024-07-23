import pandas as pd
import streamlit as st
from database import get_user_by_key, get_user_by_public_key, add_user, init_db, get_events, add_event, get_candidates, add_candidate, add_vote, has_voted, get_votes
import hashlib
import secrets
import json
import time
from nostr_client import NostrClient, generate_private_key, get_public_key, sign_event
from PIL import Image
import io

# Initialize the database
init_db()

relay_url = "wss://relay.damus.io"
nostr_client = NostrClient(relay_url)

# Initialize session state variables
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'private_key' not in st.session_state:
    st.session_state.private_key = ""
if 'public_key' not in st.session_state:
    st.session_state.public_key = ""
if 'profile_image' not in st.session_state:
    st.session_state.profile_image = None
if 'page' not in st.session_state:
    st.session_state.page = 'Profile'

def login(private_key):
    user = get_user_by_key(private_key)
    if user:
        st.session_state.authenticated = True
        st.session_state.user_id = user[0]
        st.session_state.is_admin = (user[5] == 'admin')
        st.session_state.private_key = private_key
        st.session_state.public_key = user[3]
        st.session_state.username = user[1]
        st.session_state.profile_image = Image.open(io.BytesIO(user[4])) if user[4] else None
        st.toast(body="Login successful!", icon="✅")
        st.experimental_rerun()
    else:
        st.toast(body="Invalid private key", icon="❌")

def register(username, profile_image):
    private_key = generate_private_key()
    public_key = get_public_key(private_key)
    if get_user_by_public_key(public_key):
        st.toast(body="Public key already exists. Each user can only have one account.", icon="❌")
        return
    image_bytes = profile_image.read() if profile_image else None
    add_user(username, private_key, public_key, image_bytes, 'user')
    st.session_state.authenticated = True
    st.session_state.private_key = private_key
    st.session_state.public_key = public_key
    st.session_state.username = username
    st.session_state.profile_image = Image.open(io.BytesIO(image_bytes)) if image_bytes else None
    st.toast(body="Registration successful! Your private key and public key have been generated.", icon="✅")
    st.info(f"Your private key: {private_key}")
    st.info(f"Your public key: {public_key}")
    st.experimental_rerun()

def create_vote_event(candidate_id):
    event = {
        "kind": 1,
        "pubkey": st.session_state.public_key,
        "created_at": int(time.time()),
        "tags": [],
        "content": f"Vote for Candidate ID: {candidate_id}"
    }
    event["id"] = hashlib.sha256(json.dumps(event).encode()).hexdigest()
    event["sig"] = sign_event(event, st.session_state.private_key)
    return event

def publish_vote(candidate_id):
    event = create_vote_event(candidate_id)
    nostr_client.send_event(event)
    st.toast(body="Vote published!", icon="✅")
    st.experimental_rerun()

def upload_image():
    uploaded_file = st.file_uploader("Choose a profile image", type=["jpg", "png"])
    if uploaded_file is not None:
        return uploaded_file
    return None

def sidebar():
    st.sidebar.title("Navigation")
    st.sidebar.button("Profile", on_click=lambda: st.session_state.update({'page': 'Profile'}))
    st.sidebar.button("Events", on_click=lambda: st.session_state.update({'page': 'Events'}))
    if st.session_state.is_admin:
        st.sidebar.button("Admin Dashboard", on_click=lambda: st.session_state.update({'page': 'Admin Dashboard'}))
    st.sidebar.button("Logout", on_click=logout)

def logout():
    st.session_state.authenticated = False
    st.session_state.is_admin = False
    st.session_state.user_id = None
    st.session_state.private_key = None
    st.session_state.public_key = None
    st.session_state.username = None
    st.session_state.profile_image = None
    st.toast(body="Logged out successfully!", icon="ℹ️")
    st.experimental_rerun()

if not st.session_state.authenticated:
    st.header("Login or Register")
    action = st.radio("Choose an action", ["Login", "Register"])
    
    if action == "Login":
        private_key = st.text_input("Private Key", type="password")
        if st.button("Login"):
            login(private_key)
    else:
        username = st.text_input("Username")
        profile_image = upload_image()
        if st.button("Register"):
            register(username, profile_image)
else:
    sidebar()
    if st.session_state.page == 'Profile':
        st.header("Profile")
        st.write(f"Username: {st.session_state.username}")
        st.write(f"Public Key: {st.session_state.public_key}")
        st.write(f"Private Key: {st.session_state.private_key}")
        st.write(f"Role: {'Admin' if st.session_state.is_admin else 'User'}")
        if st.session_state.profile_image:
            st.image(st.session_state.profile_image, width=150)

    elif st.session_state.page == 'Events':
        st.header("Events")
        events = get_events()
        event_names = [event[1] for event in events]
        selected_event_name = st.selectbox("Select Event", event_names)
        selected_event_id = events[event_names.index(selected_event_name)][0] if selected_event_name else None

        if selected_event_id:
            candidates = get_candidates(selected_event_id)
            for candidate in candidates:
                st.image(Image.open(io.BytesIO(candidate[4])), width=150)
                st.write(f"Candidate: {candidate[2]}")
                st.write(f"Description: {candidate[3]}")
                if st.button(f"Vote for {candidate[2]}", key=candidate[0]):
                    candidate_id = candidate[0]
                    user_id = st.session_state['user_id']
                    if not has_voted(user_id, selected_event_id, candidate_id):
                        add_vote(user_id, selected_event_id, candidate_id, "vote")
                        publish_vote(candidate_id)
                        st.toast(body="Your vote has been submitted!", icon="✅")
                    else:
                        st.toast(body="You have already voted for this candidate.", icon="❌")

        if st.button("Load Votes"):
            if selected_event_id:
                votes = get_votes(selected_event_id)
                for vote in votes:
                    st.write(f"User ID: {vote[1]}, Candidate ID: {vote[3]}, Vote: {vote[4]}")

    elif st.session_state.page == 'Admin Dashboard':
        st.header("Admin Dashboard")

        # Create a new event
        event_name = st.text_input("Event Name")
        event_type = st.selectbox("Event Type", ["Presidential Election", "General Vote"])
        if st.button("Create Event"):
            add_event(event_name, event_type)
            st.toast(body="Event created successfully!", icon="✅")
            st.experimental_rerun()

        # Select event for adding candidates
        events = get_events()
        event_names = [event[1] for event in events]
        selected_event_name = st.selectbox("Select Event", event_names)
        selected_event_id = events[event_names.index(selected_event_name)][0] if selected_event_name else None

        # Add a new candidate
        candidate_name = st.text_input("Candidate Name")
        description = st.text_area("Description")
        candidate_image = upload_image()
        if st.button("Add Candidate"):
            image_bytes = candidate_image.read() if candidate_image else None
            add_candidate(selected_event_id, candidate_name, description, image_bytes)
            st.toast(body="Candidate added successfully!", icon="✅")
            st.experimental_rerun()

        # View all votes
        st.header("All Votes")
        if selected_event_id:
            votes = get_votes(selected_event_id)
            for vote in votes:
                st.write(f"User ID: {vote[1]}, Candidate ID: {vote[3]}, Vote: {vote[4]}")
import streamlit as st
from database import get_user_by_key, get_user_by_public_key, add_user, init_db, get_events, add_event, get_candidates, add_candidate, add_vote, has_voted, get_votes
import hashlib
import secrets
import json
import time
from nostr_client import NostrClient, generate_private_key, get_public_key, sign_event
from PIL import Image
import io
import altair as alt

# Initialize the database
init_db()

relay_url = "wss://relay.damus.io"
nostr_client = NostrClient(relay_url)

# Initialize session state variables
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'private_key' not in st.session_state:
    st.session_state.private_key = ""
if 'public_key' not in st.session_state:
    st.session_state.public_key = ""
if 'profile_image' not in st.session_state:
    st.session_state.profile_image = None
if 'page' not in st.session_state:
    st.session_state.page = 'Profile'

def login(private_key):
    user = get_user_by_key(private_key)
    if user:
        st.session_state.authenticated = True
        st.session_state.user_id = user[0]
        st.session_state.is_admin = (user[5] == 'admin')
        st.session_state.private_key = private_key
        st.session_state.public_key = user[3]
        st.session_state.username = user[1]
        st.session_state.profile_image = Image.open(io.BytesIO(user[4])) if user[4] else None
        st.toast(body="Login successful!", icon="✅")
        st.experimental_rerun()
    else:
        st.toast(body="Invalid private key", icon="❌")

def register(username, profile_image):
    private_key = generate_private_key()
    public_key = get_public_key(private_key)
    if get_user_by_public_key(public_key):
        st.toast(body="Public key already exists. Each user can only have one account.", icon="❌")
        return
    image_bytes = profile_image.read() if profile_image else None
    add_user(username, private_key, public_key, image_bytes, 'user')
    st.session_state.authenticated = True
    st.session_state.private_key = private_key
    st.session_state.public_key = public_key
    st.session_state.username = username
    st.session_state.profile_image = Image.open(io.BytesIO(image_bytes)) if image_bytes else None
    st.toast(body="Registration successful! Your private key and public key have been generated.", icon="✅")
    st.info(f"Your private key: {private_key}")
    st.info(f"Your public key: {public_key}")
    st.experimental_rerun()

def create_vote_event(candidate_id):
    event = {
        "kind": 1,
        "pubkey": st.session_state.public_key,
        "created_at": int(time.time()),
        "tags": [],
        "content": f"Vote for Candidate ID: {candidate_id}"
    }
    event["id"] = hashlib.sha256(json.dumps(event).encode()).hexdigest()
    event["sig"] = sign_event(event, st.session_state.private_key)
    return event

def publish_vote(candidate_id):
    event = create_vote_event(candidate_id)
    nostr_client.send_event(event)
    st.toast(body="Vote published!", icon="✅")
    st.experimental_rerun()

def upload_image():
    uploaded_file = st.file_uploader("Choose a profile image", type=["jpg", "png"])
    if uploaded_file is not None:
        return uploaded_file
    return None

def sidebar():
    st.sidebar.title("Navigation")
    if st.sidebar.button("Profile"):
        st.session_state.page = 'Profile'
    if st.sidebar.button("Events"):
        st.session_state.page = 'Events'
    if st.session_state.is_admin and st.sidebar.button("Admin Dashboard"):
        st.session_state.page = 'Admin Dashboard'
    if st.sidebar.button("Logout"):
        logout()

def logout():
    st.session_state.authenticated = False
    st.session_state.is_admin = False
    st.session_state.user_id = None
    st.session_state.private_key = None
    st.session_state.public_key = None
    st.session_state.username = None
    st.session_state.profile_image = None
    st.toast(body="Logged out successfully!", icon="ℹ️")
    st.experimental_rerun()

if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center; color: #2E86C1;'>Welcome to the Voting App</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #2874A6;'>Secure and Transparent Voting</h2>", unsafe_allow_html=True)
    action = st.radio("Choose an action", ["Login", "Register"], index=0, horizontal=True)
    
    col1, col2 = st.beta_columns(2)
    with col1:
        st.image("https://www.example.com/login_image.jpg", width=300)  # Replace with your own image
    with col2:
        if action == "Login":
            private_key = st.text_input("Private Key", type="password")
            if st.button("Login"):
                login(private_key)
        else:
            username = st.text_input("Username")
            profile_image = upload_image()
            if st.button("Register"):
                register(username, profile_image)
else:
    sidebar()
    if st.session_state.page == 'Profile':
        st.header("Profile")
        st.write(f"**Username:** {st.session_state.username}")
        st.write(f"**Public Key:** {st.session_state.public_key}")
        st.write(f"**Private Key:** {st.session_state.private_key}")
        st.write(f"**Role:** {'Admin' if st.session_state.is_admin else 'User'}")
        if st.session_state.profile_image:
            st.image(st.session_state.profile_image, width=150)

    elif st.session_state.page == 'Events':
        st.header("Events")
        events = get_events()
        event_names = [event[1] for event in events]
        selected_event_name = st.selectbox("Select Event", event_names)
        selected_event_id = events[event_names.index(selected_event_name)][0] if selected_event_name else None

        if selected_event_id:
            candidates = get_candidates(selected_event_id)
            st.markdown("### Candidates")
            for candidate in candidates:
                col1, col2, col3 = st.beta_columns([1, 2, 1])
                with col1:
                    st.image(Image.open(io.BytesIO(candidate[4])), width=100)
                with col2:
                    st.write(f"**{candidate[2]}**")
                    st.write(f"{candidate[3]}")
                with col3:
                    if st.button(f"Vote for {candidate[2]}", key=candidate[0]):
                        candidate_id = candidate[0]
                        user_id = st.session_state['user_id']
                        if not has_voted(user_id, selected_event_id, candidate_id):
                            add_vote(user_id, selected_event_id, candidate_id, "vote")
                            publish_vote(candidate_id)
                            st.toast(body="Your vote has been submitted!", icon="✅")
                        else:
                            st.toast(body="You have already voted for this candidate.", icon="❌")

        if st.button("Load Votes"):
            if selected_event_id:
                votes = get_votes(selected_event_id)
                st.markdown("### Votes")
                for vote in votes:
                    st.write(f"User ID: {vote[1]}, Candidate ID: {vote[3]}, Vote: {vote[4]}")

    elif st.session_state.page == 'Admin Dashboard':
        st.header("Admin Dashboard")

        # Create a new event
        event_name = st.text_input("Event Name")
        event_type = st.selectbox("Event Type", ["Presidential Election", "General Vote"])
        if st.button("Create Event"):
            add_event(event_name, event_type)
            st.toast(body="Event created successfully!", icon="✅")
            st.experimental_rerun()

        # Select event for adding candidates
        events = get_events()
        event_names = [event[1] for event in events]
        selected_event_name = st.selectbox("Select Event", event_names)
        selected_event_id = events[event_names.index(selected_event_name)][0] if selected_event_name else None

        # Add a new candidate
        candidate_name = st.text_input("Candidate Name")
        description = st.text_area("Description")
        candidate_image = upload_image()
        if st.button("Add Candidate"):
            image_bytes = candidate_image.read() if candidate_image else None
            add_candidate(selected_event_id, candidate_name, description, image_bytes)
            st.toast(body="Candidate added successfully!", icon="✅")
            st.experimental_rerun()

        # View all votes
        st.header("All Votes")
        if selected_event_id:
            votes = get_votes(selected_event_id)

            vote_data = []
            for vote in votes:
                vote_data.append({
                    'User ID': vote[1],
                    'Candidate ID': vote[3],
                    'Vote': vote[4]
                })

            df = pd.DataFrame(vote_data)

            if not df.empty:
                st.write(df)
                vote_counts = df.groupby('Candidate ID').count().reset_index()
                vote_counts.columns = ['Candidate ID', 'Vote Count']
                
                # Retrieve candidate names for better visualization
                candidates = get_candidates(selected_event_id)
                candidate_dict = {candidate[0]: candidate[2] for candidate in candidates}
                vote_counts['Candidate Name'] = vote_counts['Candidate ID'].map(candidate_dict)
                
                chart = alt.Chart(vote_counts).mark_bar().encode(
                    x=alt.X('Candidate Name', sort='-y'),
                    y='Vote Count',
                    color=alt.condition(
                        alt.datum['Vote Count'] > 0,
                        alt.value('#3498DB'),
                        alt.value('#D5DBDB')
                    )
                )
                st.altair_chart(chart, use_container_width=True)
            else:
                st.write("No votes yet.")
