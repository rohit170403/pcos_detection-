from flask import Flask, render_template, request, redirect, url_for, flash, session , make_response
import sqlite3
from sqlite3 import IntegrityError
import pickle

# Load the trained model
model = pickle.load(open('model.pkl', 'rb'))
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize the database



# Middleware for requiring login
def login_required(func):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash("You need to log in to access this page.", "error")
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

#admin ascess decorator 
def admin_only(func):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash("You need to log in to access this page.", "error")
            return redirect(url_for("login"))

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        conn.close()

        if not user or user[0] != 1:  # Check if the user is an admin
            flash("You do not have permission to access this page.", "error")
            return redirect(url_for("dashboard"))

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
        # Retrieve form data
        mobile_no = request.form.get("mobile_no")
        password = request.form.get("password")

        # Validate input
        if not mobile_no or not password:
            flash("Please enter both mobile number and password.", "error")
            return render_template("login.html")

        # Database interaction
        try:
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()

            # Fetch the user by mobile number and password
            cursor.execute(
                'SELECT id, is_admin FROM users WHERE mobile_no = ? AND password = ?',
                (mobile_no, password)
            )
            user = cursor.fetchone()
        except sqlite3.Error as e:
            flash(f"An error occurred: {str(e)}", "error")
            return render_template("login.html")
        finally:
            conn.close()

        # Check if user exists
        if user:
            user_id, is_admin = user
            session['user_id'] = user_id  # Store user ID in session
            flash("Login successful!", "success")
            
            # Redirect based on admin status
            if is_admin == 1:
                return redirect(url_for("history"))
            else:
                return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials. Please try again.", "error")
    
    # Render login page for GET request or after invalid POST attempt
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

            return render_template('result.html', result=result)
        except Exception as e:
            flash(f"An error occurred while processing your input: {str(e)}", "error")

    return render_template("dashboard.html", result=None)




@app.route("/history")
@admin_only
def history():
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('''
        SELECT u.full_name, u.mobile_no, r.answers, r.prediction, r.timestamp
        FROM user_responses r
        JOIN users u ON r.user_id = u.id
        ORDER BY r.timestamp DESC
        ''')
        records = cursor.fetchall()
        conn.close()
        return render_template("history.html", records=records)
    except Exception as e:
        flash(f"An error occurred while fetching history: {str(e)}", "error")
        return redirect(url_for("dashboard"))

@app.route("/download_responses", methods=["GET"])
@admin_only
def download_responses():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.full_name, u.mobile_no, r.answers, r.prediction, r.timestamp
        FROM user_responses r
        JOIN users u ON r.user_id = u.id
        ORDER BY r.timestamp DESC
    ''')
    data = cursor.fetchall()
    conn.close()

    # Create a CSV response
    csv_output = "Name,Mobile No,Responses,Prediction,Timestamp\n"
    for row in data:
        csv_output += ",".join(map(str, row)) + "\n"

    response = make_response(csv_output)
    response.headers["Content-Disposition"] = "attachment; filename=user_responses.csv"
    response.headers["Content-Type"] = "text/csv"
    return response

@app.route("/logout")
def logout():
    session.pop('user_id', None)
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
