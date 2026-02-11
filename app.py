from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "secret123"

# Database setup
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ---------------- MODELS ---------------- #

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


# Create database tables
with app.app_context():
    db.create_all()


# ---------------- ROUTES ---------------- #

@app.route("/")
def index():
    return redirect(url_for("login"))


# -------- Register -------- #
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "User already exists"

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")


# -------- Login -------- #
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))
        else:
            return "Invalid username or password"

    return render_template("login.html")


# -------- Dashboard (Add Note + Show Notes) -------- #
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        content = request.form["content"]

        new_note = Note(content=content, user_id=session["user_id"])
        db.session.add(new_note)
        db.session.commit()

    notes = Note.query.filter_by(user_id=session["user_id"]).all()
    return render_template("dashboard.html", notes=notes)


# -------- Edit Note -------- #
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    note = Note.query.get_or_404(id)

    # Security: user sirf apni note edit kare
    if note.user_id != session["user_id"]:
        return "Unauthorized"

    if request.method == "POST":
        note.content = request.form["content"]
        db.session.commit()
        return redirect(url_for("dashboard"))

    return render_template("edit.html", note=note)


# -------- Delete Note -------- #
@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    note = Note.query.get_or_404(id)

    # Security check
    if note.user_id != session["user_id"]:
        return "Unauthorized"

    db.session.delete(note)
    db.session.commit()
    return redirect(url_for("dashboard"))


# -------- Logout -------- #
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))


# -------- Run App -------- #
if __name__ == "__main__":
    app.run(debug=True)