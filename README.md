# Quiz Master Application

A complete Flask-based Quiz Master app with randomized questions, score analysis, answer review, and PDF report export.

## Project Structure

```text
quiz-master-app/
├── app.py
├── templates/
│   ├── index.html
│   ├── quiz.html
│   └── result.html
├── static/
│   └── style.css
├── requirements.txt
└── README.md
```

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the app:

```bash
python app.py
```

3. Open in your browser:

```text
http://127.0.0.1:5000/
```

## Features

- Home, quiz, submit, results, and PDF export routes
- 8-question quiz bank with random order on each attempt
- Session-based answer tracking
- Score, percentage, feedback, and question-by-question review
- PDF report download with timestamp and detailed breakdown
- Restart functionality and responsive UI
