import sqlite3

# Connect to SQLite database (creates it if it doesn't exist)
connection = sqlite3.connect('database.db')

# Load schema from file and execute it
with open('schema.sql', 'r') as f:
    connection.executescript(f.read())

cur = connection.cursor()

# Seed: Insert default list titles
cur.execute("INSERT INTO lists (title) VALUES (?)", ('Work',))
cur.execute("INSERT INTO lists (title) VALUES (?)", ('Home',))
cur.execute("INSERT INTO lists (title) VALUES (?)", ('Study',))

# Seed: Insert some default tasks
cur.execute("INSERT INTO items (list_id, content) VALUES (?, ?)", (1, 'Morning meeting'))
cur.execute("INSERT INTO items (list_id, content) VALUES (?, ?)", (2, 'Buy fruit'))
cur.execute("INSERT INTO items (list_id, content) VALUES (?, ?)", (2, 'Cook dinner'))
cur.execute("INSERT INTO items (list_id, content) VALUES (?, ?)", (3, 'Learn Flask'))
cur.execute("INSERT INTO items (list_id, content) VALUES (?, ?)", (3, 'Learn SQLite'))

# Save and close
connection.commit()
connection.close()

print("✅ Database initialized successfully.")
