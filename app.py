from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = "secret"   # session key

# DATABASE CONFIG
uri = os.getenv("DATABASE_URL")  # Gets DATABASE_URL from environment (Render or local)

# Fix SQLAlchemy URL prefix if needed
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

# Fallback to SQLite for local testing
app.config['SQLALCHEMY_DATABASE_URI'] = uri or "sqlite:///local.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)



# User table
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

# Task table
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.Text, nullable=False)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    duration = db.Column(db.Integer)   

with app.app_context():
    db.create_all()

# ---------- ROUTES ----------

@app.route("/", methods=["GET", "POST"])
def login():
    message = ""  # default empty
    if request.method == "POST":
        user = User.query.filter_by(
            username=request.form['username'],
            password=request.form['password']
        ).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for("dashboard"))
        else:
            message = "Incorrect password"  # set message

    return render_template("login.html", message=message)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        new_user = User(
            username=request.form['username'],
            password=request.form['password']
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("login"))  # <- important
    return render_template("signup.html")  # <- GET request

@app.route("/dashboard")
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for("login"))
    
    tasks = Task.query.filter_by(user_id=session['user_id']).all()
    return render_template("dashboard.html", tasks=tasks)
 
from datetime import datetime

@app.route("/api/tasks", methods=["GET", "POST"])
def tasks():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    if request.method == "POST":
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON received"}), 400

        # Convert strings to datetime
        try:
            start_time = datetime.fromisoformat(data['start_time'])
            end_time = datetime.fromisoformat(data['end_time'])
        except Exception as e:
            return jsonify({"error": f"Invalid date format: {str(e)}"}), 400

        # Calculate duration in minutes
        duration = int((end_time - start_time).total_seconds() / 60)

        # Create and save task
        new_task = Task(
            user_id=session['user_id'],
            title=data['title'],
            start_time=start_time,
            end_time=end_time,
            duration=duration
        )

        try:
            db.session.add(new_task)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"DB error: {str(e)}"}), 500

        return jsonify({
            "id": new_task.id,
            "title": new_task.title,
            "start_time": str(new_task.start_time),
            "end_time": str(new_task.end_time),
            "duration": new_task.duration
        })

    # GET tasks for current user
    tasks = Task.query.filter_by(user_id=session['user_id']).all()
    return jsonify([
        {
            "id": t.id,
            "title": t.title,
            "start_time": str(t.start_time),
            "end_time": str(t.end_time),
            "duration": t.duration
        } for t in tasks
    ])


@app.route("/api/tasks/<int:task_id>", methods=["PUT", "DELETE"])
def update_delete_task(task_id):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    task = Task.query.filter_by(id=task_id, user_id=session['user_id']).first()
    if not task:
        return jsonify({"error": "Task not found"}), 404

    if request.method == "PUT":
        data = request.get_json()
        try:
            start_time = datetime.fromisoformat(data['start_time'])
            end_time = datetime.fromisoformat(data['end_time'])
        except Exception as e:
            return jsonify({"error": f"Invalid date format: {str(e)}"}), 400

        task.title = data['title']
        task.start_time = start_time
        task.end_time = end_time
        task.duration = int((end_time - start_time).total_seconds() / 60)

        db.session.commit()
        return jsonify({
            "success": True,
            "id": task.id,
            "title": task.title,
            "start_time": str(task.start_time),
            "end_time": str(task.end_time),
            "duration": task.duration
        })

    if request.method == "DELETE":
        db.session.delete(task)
        db.session.commit()
        return jsonify({"success": True})


@app.route("/logout")
def logout():
    # Clear all session data
    session.clear()
    # Redirect to login page
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
