import sqlite3

def init_db():
    conn = sqlite3.connect('voting_app.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            private_key TEXT,
            public_key TEXT,
            profile_image BLOB,
            role TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY,
            event_name TEXT,
            event_type TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY,
            event_id INTEGER,
            candidate_name TEXT,
            description TEXT,
            image BLOB,
            FOREIGN KEY (event_id) REFERENCES events (id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            event_id INTEGER,
            candidate_id INTEGER,
            vote TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (event_id) REFERENCES events (id),
            FOREIGN KEY (candidate_id) REFERENCES candidates (id)
        )
    ''')
    conn.commit()
    conn.close()

def add_user(username, private_key, public_key, profile_image, role):
    conn = sqlite3.connect('voting_app.db')
    c = conn.cursor()
    c.execute('INSERT INTO users (username, private_key, public_key, profile_image, role) VALUES (?, ?, ?, ?, ?)', (username, private_key, public_key, profile_image, role))
    conn.commit()
    conn.close()

def get_user_by_key(private_key):
    conn = sqlite3.connect('voting_app.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE private_key = ?', (private_key,))
    user = c.fetchone()
    conn.close()
    return user

def get_user_by_public_key(public_key):
    conn = sqlite3.connect('voting_app.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE public_key = ?', (public_key,))
    user = c.fetchone()
    conn.close()
    return user

def add_event(event_name, event_type):
    conn = sqlite3.connect('voting_app.db')
    c = conn.cursor()
    c.execute('INSERT INTO events (event_name, event_type) VALUES (?, ?)', (event_name, event_type))
    conn.commit()
    conn.close()

def get_events():
    conn = sqlite3.connect('voting_app.db')
    c = conn.cursor()
    c.execute('SELECT * FROM events')
    events = c.fetchall()
    conn.close()
    return events

def add_candidate(event_id, candidate_name, description, image):
    conn = sqlite3.connect('voting_app.db')
    c = conn.cursor()
    c.execute('INSERT INTO candidates (event_id, candidate_name, description, image) VALUES (?, ?, ?, ?)', (event_id, candidate_name, description, image))
    conn.commit()
    conn.close()

def get_candidates(event_id):
    conn = sqlite3.connect('voting_app.db')
    c = conn.cursor()
    c.execute('SELECT * FROM candidates WHERE event_id = ?', (event_id,))
    candidates = c.fetchall()
    conn.close()
    return candidates

def add_vote(user_id, event_id, candidate_id, vote):
    conn = sqlite3.connect('voting_app.db')
    c = conn.cursor()
    c.execute('INSERT INTO votes (user_id, event_id, candidate_id, vote) VALUES (?, ?, ?, ?)', (user_id, event_id, candidate_id, vote))
    conn.commit()
    conn.close()

def get_votes(event_id):
    conn = sqlite3.connect('voting_app.db')
    c = conn.cursor()
    c.execute('SELECT * FROM votes WHERE event_id = ?', (event_id,))
    votes = c.fetchall()
    conn.close()
    return votes

def has_voted(user_id, event_id, candidate_id):
    conn = sqlite3.connect('voting_app.db')
    c = conn.cursor()
    c.execute('SELECT * FROM votes WHERE user_id = ? AND event_id = ? AND candidate_id = ?', (user_id, event_id, candidate_id))
    vote = c.fetchone()
    conn.close()
    return vote is not None


def initialize_users():
    add_user("admin", "b02d5e9c1cb155b6ebf6b7fd8f93c63001f1895699331697673a17a728a9cf1b", "admin_public_key", None, "admin")
    add_user("user", "1def1db5109e5bff45946798db3eff01e99b442c2493e05115ec6bc36587ad8a", "user_public_key", None, "user")

init_db()
initialize_users()
