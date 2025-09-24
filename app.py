from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "secret"   # session key

# PostgreSQL connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:12345678@localhost:5432/taskdb'
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
    return render_template("dashboard.html")
 

# Fetch tasks for logged-in user
@app.route("/api/tasks", methods=["GET", "POST"])
def tasks():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    if request.method == "POST":
        data = request.get_json()
        new_task = Task(
            user_id=session['user_id'],
            title=data['title'],
            start_time=data['start_time'],
            end_time=data['end_time']
        )
        db.session.add(new_task)
        db.session.commit()
        return jsonify({
            "id": new_task.id,
            "title": new_task.title,
            "start_time": str(new_task.start_time),
            "end_time": str(new_task.end_time)
        })

    tasks = Task.query.filter_by(user_id=session['user_id']).all()
    return jsonify([
        {
            "id": t.id,
            "title": t.title,
            "start_time": str(t.start_time),
            "end_time": str(t.end_time)
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
        task.title = data['title']
        task.start_time = data['start_time']
        task.end_time = data['end_time']
        db.session.commit()
        return jsonify({"success": True})

    if request.method == "DELETE":
        db.session.delete(task)
        db.session.commit()
        return jsonify({"success": True})


if __name__ == "__main__":
    app.run(debug=True)
