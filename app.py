from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from sqlite3 import IntegrityError
import pickle

# Load the trained model
model = pickle.load(open('model.pkl', 'rb'))
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize the database
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            mobile_no TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            answers TEXT NOT NULL,
            prediction TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()


# Middleware for requiring login
def login_required(func):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash("You need to log in to access this page.", "error")
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# Routes
@app.route("/", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        full_name = request.form.get("full_name")
        mobile_no = request.form.get("mobile_no")
        password = request.form.get("password")

        try:
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (full_name, mobile_no, password) VALUES (?, ?, ?)',
                           (full_name, mobile_no, password))
            conn.commit()
            conn.close()
            flash("Sign-up successful! Please log in.", "success")
            return redirect(url_for("login"))
        except IntegrityError:
            flash("Mobile number already registered. Try logging in.", "error")
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        mobile_no = request.form.get("mobile_no")
        password = request.form.get("password")

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE mobile_no = ? AND password = ?', (mobile_no, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials. Please try again.", "error")
    return render_template("login.html")

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    if request.method == 'POST':
        try:
            # Collect form data
            features = [
                float(request.form.get('Period Length')),
                float(request.form.get('Cycle Length')),
                int(request.form.get('Age')),
                int(request.form.get('Overweight')),
                int(request.form.get('loss weight gain / weight loss')),
                int(request.form.get('irregular or missed periods')),
                int(request.form.get('Difficulty in conceiving')),
                int(request.form.get('Hair growth on Chin')),
                int(request.form.get('Hair growth on Cheeks')),
                int(request.form.get('Hair growth Between breasts')),
                int(request.form.get('Hair growth  on Upper lips')),
                int(request.form.get('Hair growth in Arms')),
                int(request.form.get('Hair growth on Inner thighs')),
                int(request.form.get('Acne or skin tags')),
                int(request.form.get('Hair thinning or hair loss')),
                int(request.form.get('Dark patches')),
                int(request.form.get('always tired')),
                int(request.form.get('more Mood Swings')),
                int(request.form.get('Hours Exercise Per Week')),
                int(request.form.get('Eat Outside')),
                int(request.form.get('Canned Food Consumption'))
            ]

            # Serialize answers for storage
            answers = str(features)

            # Make a prediction using the model
            prediction = model.predict([features])
            result = "PCOS Detected" if prediction[0] == 1 else "No PCOS Detected"

            # Save the user's responses and prediction to the database
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_responses (user_id, answers, prediction)
                VALUES (?, ?, ?)
            ''', (session['user_id'], answers, result))
            conn.commit()
            conn.close()

            return render_template('dashboard.html', result=result)
        except Exception as e:
            flash(f"An error occurred while processing your input: {str(e)}", "error")

    return render_template("dashboard.html", result=None)

@app.route("/history")
@login_required
def history():
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT answers, prediction, timestamp
            FROM user_responses
            WHERE user_id = ?
            ORDER BY timestamp DESC
        ''', (session['user_id'],))
        records = cursor.fetchall()
        conn.close()
        return render_template("history.html", records=records)
    except Exception as e:
        flash(f"An error occurred while fetching history: {str(e)}", "error")
        return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.pop('user_id', None)
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

if __name__ == "__main__":
    init_db()
    app.run(debug=False,host='0.0.0.0')
