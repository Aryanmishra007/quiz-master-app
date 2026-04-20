from datetime import datetime
import io
import os
import random

from dateutil import tz
from flask import Flask, redirect, render_template, request, send_file, session, url_for
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

app = Flask(__name__)
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S %Z"
DEFAULT_STUDENT_NAME = os.getenv("STUDENT_NAME", "Quiz Participant")
PDF_TABLE_COLUMN_WIDTHS = [180, 110, 110, 70]


def get_secret_key():
    env_secret = os.getenv("SECRET_KEY")
    if env_secret:
        return env_secret

    os.makedirs(app.instance_path, exist_ok=True)
    key_path = os.path.join(app.instance_path, "secret_key")
    if os.path.exists(key_path):
        with open(key_path, "rb") as key_file:
            return key_file.read()

    generated_key = os.urandom(24)
    with open(key_path, "wb") as key_file:
        key_file.write(generated_key)
    return generated_key


app.secret_key = get_secret_key()

QUIZ_QUESTIONS = [
    {
        "id": 1,
        "question": "Which Python web framework is used in this project?",
        "options": ["Django", "Flask", "FastAPI", "Bottle"],
        "answer": "Flask",
    },
    {
        "id": 2,
        "question": "Which HTML tag is used for the largest heading?",
        "options": ["<h6>", "<heading>", "<h1>", "<head>"],
        "answer": "<h1>",
    },
    {
        "id": 3,
        "question": "What does CSS stand for?",
        "options": [
            "Computer Style Sheets",
            "Cascading Style Sheets",
            "Creative Style Syntax",
            "Colorful Style Sheets",
        ],
        "answer": "Cascading Style Sheets",
    },
    {
        "id": 4,
        "question": "Which HTTP method is commonly used to submit form data?",
        "options": ["GET", "POST", "PUT", "TRACE"],
        "answer": "POST",
    },
    {
        "id": 5,
        "question": "What is the output of 2 ** 3 in Python?",
        "options": ["6", "8", "9", "23"],
        "answer": "8",
    },
    {
        "id": 6,
        "question": "Which component is responsible for styling web pages?",
        "options": ["HTML", "Python", "CSS", "SQL"],
        "answer": "CSS",
    },
    {
        "id": 7,
        "question": "Which built-in Python type stores key-value pairs?",
        "options": ["list", "tuple", "dictionary", "set"],
        "answer": "dictionary",
    },
    {
        "id": 8,
        "question": "Where are Flask HTML templates stored by default?",
        "options": ["/static", "/templates", "/views", "/pages"],
        "answer": "/templates",
    },
]


def get_ordered_questions():
    question_ids = session.get("question_order")
    if not question_ids:
        return []
    questions_by_id = {question["id"]: question for question in QUIZ_QUESTIONS}
    return [questions_by_id[qid] for qid in question_ids if qid in questions_by_id]


def calculate_results(questions, answers):
    review = []
    score = 0
    total = len(questions)

    for question in questions:
        selected = answers.get(str(question["id"]))
        is_correct = selected == question["answer"]
        if is_correct:
            score += 1

        review.append(
            {
                "question": question["question"],
                "selected": selected or "Not Answered",
                "correct": question["answer"],
                "is_correct": is_correct,
            }
        )

    percentage = round((score / total) * 100, 2) if total else 0

    if percentage >= 85:
        feedback = "Excellent"
    elif percentage >= 70:
        feedback = "Good"
    elif percentage >= 50:
        feedback = "Average"
    else:
        feedback = "Poor"

    feedback_class = {
        "Excellent": "excellent",
        "Good": "good",
        "Average": "average",
        "Poor": "poor",
    }[feedback]

    return {
        "score": score,
        "total": total,
        "percentage": percentage,
        "feedback": feedback,
        "feedback_class": feedback_class,
        "review": review,
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/quiz")
def quiz():
    shuffled_questions = QUIZ_QUESTIONS[:]
    random.shuffle(shuffled_questions)
    session["question_order"] = [question["id"] for question in shuffled_questions]
    session.pop("answers", None)
    session.pop("result", None)
    return render_template("quiz.html", questions=shuffled_questions)


@app.route("/submit", methods=["POST"])
def submit():
    questions = get_ordered_questions()
    if not questions:
        return redirect(url_for("quiz"))

    answers = {}
    for question in questions:
        field_name = f"question_{question['id']}"
        answers[str(question["id"])] = request.form.get(field_name)

    session["answers"] = answers
    session["result"] = calculate_results(questions, answers)
    session["result_generated_at"] = datetime.now(tz.tzlocal()).strftime(TIMESTAMP_FORMAT)
    return redirect(url_for("results"))


@app.route("/results")
def results():
    result = session.get("result")
    if not result:
        return redirect(url_for("home"))

    return render_template(
        "result.html",
        result=result,
        generated_at=session.get("result_generated_at"),
    )


@app.route("/export_pdf")
def export_pdf():
    result = session.get("result")
    if not result:
        return redirect(url_for("home"))

    generated_at = session.get("result_generated_at") or datetime.now(tz.tzlocal()).strftime(TIMESTAMP_FORMAT)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title="Quiz Master Report")
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Quiz Master - Performance Report", styles["Title"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"Date: {generated_at}", styles["Normal"]))
    story.append(Paragraph(f"Student: {DEFAULT_STUDENT_NAME}", styles["Normal"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"Score: {result['score']} / {result['total']}", styles["Heading2"]))
    story.append(Paragraph(f"Percentage: {result['percentage']}%", styles["Heading3"]))
    story.append(Paragraph(f"Feedback: {result['feedback']}", styles["Heading3"]))
    story.append(Spacer(1, 12))

    table_data = [["Question", "Selected Answer", "Correct Answer", "Status"]]
    for index, item in enumerate(result["review"], start=1):
        table_data.append(
            [
                f"{index}. {item['question']}",
                item["selected"],
                item["correct"],
                "Correct" if item["is_correct"] else "Incorrect",
            ]
        )

    review_table = Table(table_data, colWidths=PDF_TABLE_COLUMN_WIDTHS, repeatRows=1)
    review_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4f8b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f9fc")]),
            ]
        )
    )
    story.append(review_table)

    doc.build(story)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="quiz_master_report.pdf",
        mimetype="application/pdf",
    )


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
