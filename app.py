from flask import Flask, render_template, request, redirect, session, Response
import mysql.connector
import hashlib
import csv
import io

app = Flask(__name__)
app.secret_key = "expense_secret_key"

# ---------- DATABASE CONNECTION ----------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Sun@803213",
    database="expense_tracker"
)
cursor = db.cursor(dictionary=True)

# ---------- PASSWORD HASH ----------
def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

# ---------- LOGIN ----------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = hash_password(request.form["password"])

        cursor.execute(
            "SELECT user_id FROM users WHERE email=%s AND password=%s",
            (email, password)
        )
        user = cursor.fetchone()

        if user:
            session["user_id"] = user["user_id"]
            return redirect("/dashboard")

    return render_template("login.html")

# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            cursor.execute(
                "INSERT INTO users (name, email, password) VALUES (%s,%s,%s)",
                (
                    request.form["name"],
                    request.form["email"],
                    hash_password(request.form["password"])
                )
            )
            db.commit()
            return redirect("/")
        except:
            return "Email already exists"

    return render_template("register.html")

# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    cursor.execute("""
        SELECT c.category_name, SUM(e.amount) AS total
        FROM expenses e
        JOIN categories c ON e.category_id = c.category_id
        WHERE e.user_id = %s
        GROUP BY c.category_name
    """, (session["user_id"],))

    data = cursor.fetchall()
    return render_template("dashboard.html", data=data)

# ---------- ADD EXPENSE ----------
@app.route("/add", methods=["GET", "POST"])
def add_expense():
    if "user_id" not in session:
        return redirect("/")

    cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()

    if request.method == "POST":
        cursor.execute("""
            INSERT INTO expenses (user_id, category_id, amount, date, description)
            VALUES (%s,%s,%s,%s,%s)
        """, (
            session["user_id"],
            request.form["category"],
            request.form["amount"],
            request.form["date"],
            request.form["description"]
        ))
        db.commit()
        return redirect("/dashboard")

    return render_template("add_expense.html", categories=categories)

# ---------- EXPORT CSV ----------
@app.route("/export/csv")
def export_csv():
    if "user_id" not in session:
        return redirect("/")

    cursor.execute("""
        SELECT e.date, c.category_name, e.amount, e.description
        FROM expenses e
        JOIN categories c ON e.category_id = c.category_id
        WHERE e.user_id = %s
    """, (session["user_id"],))

    rows = cursor.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Category", "Amount", "Description"])

    for r in rows:
        writer.writerow([r["date"], r["category_name"], r["amount"], r["description"]])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=expenses.csv"}
    )

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)