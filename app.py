from flask import Flask, render_template, request, redirect, url_for, session
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

with app.app_context():
    db.create_all()

# ---------- ROUTES ----------

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form['username'],
                                    password=request.form['password']).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for("dashboard"))
    return render_template("login.html")

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

if __name__ == "__main__":
    app.run(debug=True)
