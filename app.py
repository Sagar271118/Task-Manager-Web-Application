from itertools import groupby
import sqlite3
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# --- Flask Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'this should be a secret random string'

# --- Login Manager Setup ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- DB Connection ---
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- User Class ---
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        return User(id=user['id'], username=user['username'], password=user['password'])
    return None

# --- Home Route ---
@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    todos = conn.execute('''
        SELECT i.id, i.content, i.due_date, l.title 
        FROM items i 
        JOIN lists l ON i.list_id = l.id 
        WHERE i.user_id = ?
        ORDER BY l.title;
    ''', (current_user.id,)).fetchall()

    lists = {}
    for k, g in groupby(todos, key=lambda t: t['title']):
        lists[k] = list(g)

    conn.close()
    return render_template('index.html', lists=lists)

# --- Create Task ---
@app.route('/create/', methods=('GET', 'POST'))
@login_required
def create():
    conn = get_db_connection()

    if request.method == 'POST':
        content = request.form['content']
        due_date = request.form['due_date']
        list_title = request.form['list']

        if not content:
            flash('Content is required!')
            return redirect(url_for('index'))

        list_id = conn.execute('SELECT id FROM lists WHERE title = (?);', (list_title,)).fetchone()['id']
        conn.execute('INSERT INTO items (content, list_id, user_id, due_date) VALUES (?, ?, ?, ?)',
                     (content, list_id, current_user.id, due_date))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    lists = conn.execute('SELECT title FROM lists;').fetchall()
    conn.close()
    return render_template('create.html', lists=lists)

# --- Delete Task ---
@app.route('/delete/<int:task_id>')
@login_required
def delete(task_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM items WHERE id = ? AND user_id = ?', (task_id, current_user.id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# --- Edit Task ---
@app.route('/edit/<int:task_id>', methods=('GET', 'POST'))
@login_required
def edit(task_id):
    conn = get_db_connection()
    task = conn.execute('SELECT * FROM items WHERE id = ? AND user_id = ?', (task_id, current_user.id)).fetchone()

    if not task:
        flash("Task not found or not authorized.")
        return redirect(url_for('index'))

    if request.method == 'POST':
        new_content = request.form['content']
        conn.execute('UPDATE items SET content = ? WHERE id = ?', (new_content, task_id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    conn.close()
    return render_template('edit.html', task=task)

# --- Register ---
@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        conn = get_db_connection()
        existing = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if existing:
            flash('Username already exists!')
            return redirect(url_for('register'))

        conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()
        flash('Registered successfully. Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

# --- Login ---
@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            login_user(User(id=user['id'], username=user['username'], password=user['password']))
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.')

    return render_template('login.html')

# --- Logout ---
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- Run ---
if __name__ == '__main__':
    app.run(debug=True)