import streamlit as st
from database import get_votes, get_events, get_candidates
import pandas as pd
import altair as alt

st.header("Admin Dashboard")

# Select event for viewing votes
events = get_events()
event_names = [event[1] for event in events]
selected_event_name = st.selectbox("Select Event", event_names)
selected_event_id = events[event_names.index(selected_event_name)][0] if selected_event_name else None

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
