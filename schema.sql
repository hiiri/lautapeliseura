CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT
);

CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    title TEXT,
    description TEXT,
    date TEXT,
    num_players INTEGER,
    user_id INTEGER REFERENCES users
);

CREATE TABLE registrations (
    id INTEGER PRIMARY KEY,
    content TEXT,
    sent_at TEXT,
    user_id INTEGER REFERENCES users,
    event_id INTEGER REFERENCES events
);