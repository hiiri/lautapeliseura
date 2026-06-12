import db

def get_events():
    sql = """SELECT e.id, e.title, e.date, COUNT(e.id) total
             FROM events e
             GROUP BY e.id
             ORDER BY e.id DESC"""
    return db.query(sql)

def add_event(title, date, num_players, description, user_id):
    sql = """INSERT INTO events (title, date, num_players, description, user_id)
            VALUES (?, ?, ?, ?, ?)"""
    db.execute(sql, [title, date, num_players, description, user_id])
    event_id = db.last_insert_id()
    return event_id

def get_event(event_id):
    sql = """SELECT e.id, e.title, e.description, e.date, e.num_players, e.user_id
             FROM events e
             WHERE e.id = ?"""
    result = db.query(sql, [event_id])
    return result[0] if result else None

def update_event(event_id, title, date, num_players, description):
    sql = """UPDATE events
            SET title = ?, date = ?, num_players = ?, description = ? 
            WHERE id = ?"""
    db.execute(sql, [title, date, num_players, description, event_id])

def remove_event(event_id):
    sql = "DELETE FROM registrations WHERE event_id = ?"
    db.execute(sql, [event_id])
    sql = "DELETE FROM events WHERE id = ?"
    db.execute(sql, [event_id])

def search_events(query):
    sql = """SELECT e.id, e.title, e.date
             FROM events e
             WHERE e.title LIKE ? OR e.description LIKE ?
             ORDER BY e.date DESC"""
    return db.query(sql, ["%" + query + "%", "%" + query + "%"])

def join_event(user_id, event_id):
    sql = """SELECT COUNT(*) FROM registrations WHERE user_id = ? AND event_id = ?"""
    result = db.query(sql, [user_id, event_id])
    if result[0][0] > 0:
        return False
    sql = """INSERT INTO registrations (user_id, event_id) VALUES (?, ?)"""
    db.execute(sql, [user_id, event_id])
    return True

def get_registrations(event_id):
    sql = """
        SELECT u.id, u.username
        FROM registrations r
        JOIN users u ON r.user_id = u.id
        WHERE r.event_id = ?
        ORDER BY u.username
    """
    return db.query(sql, [event_id])

def get_user_events(user_id):
    sql = """
        SELECT e.id, e.title, e.date, COUNT(e.id) total
        FROM events e
        WHERE e.user_id = ?
        GROUP BY e.id
        ORDER BY e.date DESC
    """
    return db.query(sql, [user_id])