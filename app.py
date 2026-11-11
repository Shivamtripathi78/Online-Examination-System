from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from pathlib import Path
from datetime import datetime
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

DATABASE = Path(__file__).parent / "exam.db"

EXAM_DURATION = 10  # Minutes


# ---------------- DATABASE ----------------

def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                option_a TEXT NOT NULL,
                option_b TEXT NOT NULL,
                option_c TEXT NOT NULL,
                option_d TEXT NOT NULL,
                correct_answer TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL,
                percentage REAL NOT NULL,
                exam_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        count = connection.execute(
            "SELECT COUNT(*) FROM questions"
        ).fetchone()[0]

        if count == 0:
            questions = [
                (
                    "Which language is primarily used for web page structure?",
                    "Python", "HTML", "Java", "C++", "B"
                ),
                (
                    "What does CPU stand for?",
                    "Central Processing Unit",
                    "Computer Personal Unit",
                    "Central Program Utility",
                    "Control Processing Unit", "A"
                ),
                (
                    "Which data structure follows FIFO?",
                    "Stack", "Queue", "Tree", "Graph", "B"
                ),
                (
                    "Which SQL command retrieves data?",
                    "INSERT", "UPDATE", "SELECT", "DELETE", "C"
                ),
                (
                    "Which language is known for object-oriented programming?",
                    "HTML", "CSS", "Java", "XML", "C"
                ),
                (
                    "What does HTTP stand for?",
                    "HyperText Transfer Protocol",
                    "High Transfer Text Process",
                    "Hyper Transfer Technology Program",
                    "Home Tool Transfer Protocol", "A"
                ),
                (
                    "Which symbol is used for comments in Python?",
                    "//", "#", "/*", "<!--", "B"
                ),
                (
                    "Which of these is a JavaScript framework?",
                    "React", "MySQL", "Flask", "MongoDB", "A"
                ),
                (
                    "What is the time complexity of binary search?",
                    "O(n)", "O(n²)", "O(log n)", "O(1)", "C"
                ),
                (
                    "Which protocol is commonly used for secure web browsing?",
                    "HTTP", "FTP", "HTTPS", "SMTP", "C"
                )
            ]

            connection.executemany("""
                INSERT INTO questions
                (question, option_a, option_b, option_c, option_d, correct_answer)
                VALUES (?, ?, ?, ?, ?, ?)
            """, questions)


# ---------------- HOME ----------------

@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":
        student_name = request.form.get("student_name", "").strip()

        if not student_name:
            flash("Please enter your name.", "error")
            return redirect(url_for("home"))

        session["student_name"] = student_name
        return redirect(url_for("start_exam"))

    return render_template("index.html")


# ---------------- START EXAM ----------------

@app.route("/start-exam")
def start_exam():

    if not session.get("student_name"):
        flash("Please enter your name first.", "error")
        return redirect(url_for("home"))

    with get_connection() as connection:
        questions = connection.execute("""
            SELECT id, question, option_a, option_b, option_c, option_d
            FROM questions
            ORDER BY id
        """).fetchall()

    if not questions:
        flash("No questions available.", "error")
        return redirect(url_for("home"))

    session["exam_start"] = datetime.now().timestamp()
    session["exam_token"] = secrets.token_hex(16)

    return render_template(
        "exam.html",
        questions=questions,
        duration=EXAM_DURATION
    )


# ---------------- SUBMIT EXAM ----------------

@app.route("/submit-exam", methods=["POST"])
def submit_exam():

    if not session.get("student_name") or not session.get("exam_token"):
        flash("No active examination found.", "error")
        return redirect(url_for("home"))

    start_time = session.get("exam_start")

    if not start_time:
        return redirect(url_for("home"))

    elapsed = datetime.now().timestamp() - start_time
    time_expired = elapsed > EXAM_DURATION * 60

    with get_connection() as connection:

        questions = connection.execute(
            "SELECT * FROM questions ORDER BY id"
        ).fetchall()

        score = 0
        answers = []

        for question in questions:
            selected = request.form.get(str(question["id"]), "")

            if selected not in ["A", "B", "C", "D"]:
                selected = ""

            correct = question["correct_answer"]
            is_correct = selected == correct

            if is_correct:
                score += 1

            answers.append({
                "question": question["question"],
                "selected": selected,
                "correct": correct,
                "is_correct": is_correct
            })

        total = len(questions)
        percentage = round((score / total) * 100, 2) if total else 0

        connection.execute("""
            INSERT INTO results
            (student_name, score, total, percentage)
            VALUES (?, ?, ?, ?)
        """, (
            session["student_name"],
            score,
            total,
            percentage
        ))

    session["last_result"] = {
        "student_name": session["student_name"],
        "score": score,
        "total": total,
        "percentage": percentage,
        "answers": answers,
        "time_expired": time_expired
    }

    session.pop("exam_start", None)
    session.pop("exam_token", None)

    return redirect(url_for("result"))


# ---------------- RESULT ----------------

@app.route("/result")
def result():

    result_data = session.get("last_result")

    if not result_data:
        flash("No examination result found.", "error")
        return redirect(url_for("home"))

    return render_template("result.html", result=result_data)


# ---------------- HISTORY ----------------

@app.route("/history")
def history():

    with get_connection() as connection:
        results = connection.execute("""
            SELECT * FROM results
            ORDER BY exam_date DESC
        """).fetchall()

    return render_template("history.html", results=results)


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True, port=5000)