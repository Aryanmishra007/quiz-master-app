from __future__ import annotations

import os
import random
import secrets
from typing import Any

from flask import Flask, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))

QUESTIONS: list[dict[str, Any]] = [
    {
        "question": "Which HTML tag is used to create a hyperlink?",
        "options": ["<a>", "<link>", "<href>", "<url>"],
        "answer": "<a>",
        "difficulty": "Easy",
    },
    {
        "question": "Which Python data type is immutable?",
        "options": ["list", "dict", "set", "tuple"],
        "answer": "tuple",
        "difficulty": "Easy",
    },
    {
        "question": "What does Flask use for URL routing in view functions?",
        "options": ["@app.route", "@route.url", "@flask.path", "@url.map"],
        "answer": "@app.route",
        "difficulty": "Medium",
    },
    {
        "question": "Which CSS property is used to make a layout responsive with flexible wrapping?",
        "options": ["display: block", "position: fixed", "flex-wrap", "overflow-x"],
        "answer": "flex-wrap",
        "difficulty": "Medium",
    },
    {
        "question": "Who is known as the father of Python programming language?",
        "options": ["Dennis Ritchie", "James Gosling", "Guido van Rossum", "Bjarne Stroustrup"],
        "answer": "Guido van Rossum",
        "difficulty": "Easy",
    },
    {
        "question": "What is the output of: len({'a': 1, 'b': 2, 'c': 3}) ?",
        "options": ["2", "3", "1", "Error"],
        "answer": "3",
        "difficulty": "Hard",
    },
]


def performance_feedback(percentage: float) -> str:
    if percentage >= 85:
        return "Excellent"
    if percentage >= 70:
        return "Good"
    if percentage >= 50:
        return "Average"
    return "Needs Improvement"


@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start_quiz() -> Any:
    order = list(range(len(QUESTIONS)))
    random.shuffle(order)
    session["question_order"] = order
    session["current_index"] = 0
    session["score"] = 0
    session["responses"] = []
    return redirect(url_for("quiz"))


@app.route("/quiz", methods=["GET", "POST"])
def quiz() -> Any:
    if "question_order" not in session:
        return redirect(url_for("index"))

    order = session["question_order"]
    current_index = session["current_index"]

    if request.method == "POST":
        selected = request.form.get("answer", "")
        question_data = QUESTIONS[order[current_index]]
        is_correct = selected == question_data["answer"]

        responses = session.get("responses", [])
        responses.append(
            {
                "question": question_data["question"],
                "selected": selected or "No answer selected",
                "correct": question_data["answer"],
                "is_correct": is_correct,
            }
        )
        session["responses"] = responses

        if is_correct:
            session["score"] = session.get("score", 0) + 1

        session["current_index"] = current_index + 1

        if session["current_index"] >= len(order):
            return redirect(url_for("result"))

        current_index = session["current_index"]

    question_data = QUESTIONS[order[current_index]]
    progress_percent = ((current_index + 1) / len(order)) * 100
    return render_template(
        "quiz.html",
        question=question_data,
        current=current_index + 1,
        total=len(order),
        progress_percent=progress_percent,
    )


@app.route("/result")
def result() -> Any:
    if "question_order" not in session:
        return redirect(url_for("index"))

    total = len(session.get("question_order", []))
    score = session.get("score", 0)
    percentage = round((score / total) * 100, 2) if total else 0

    return render_template(
        "result.html",
        score=score,
        total=total,
        percentage=percentage,
        feedback=performance_feedback(percentage),
        responses=session.get("responses", []),
    )


@app.route("/restart", methods=["POST"])
def restart() -> Any:
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    debug_requested = os.environ.get("FLASK_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}
    is_dev_env = os.environ.get("FLASK_ENV", "").strip().lower() in {"development", "dev"}
    debug_mode = debug_requested and is_dev_env
    app.run(debug=debug_mode)
