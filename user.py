import streamlit as st
from database import get_posts, add_vote, has_voted
from nostr_client import nostr_client

st.title("User Dashboard")

# Voting
if 'user_id' in st.session_state:
    st.header("Vote")
    posts = get_posts()
    post_titles = [post[1] for post in posts]
    post_id = st.selectbox("Select a post to vote on", post_titles)
    vote = st.selectbox("Vote", ["Candidate A", "Candidate B"])
    if st.button("Submit Vote"):
        post_index = post_titles.index(post_id)
        post_id = posts[post_index][0]
        user_id = st.session_state['user_id']
        if not has_voted(user_id, post_id):
            add_vote(user_id, post_id, vote)
            nostr_client.send_vote(st.session_state.private_key, vote)
            st.toast(body="Your vote has been submitted!", icon="✅")
        else:
            st.toast(body="You have already voted on this post.", icon="❌")
