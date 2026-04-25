import os
import sqlite3
import cv2
import numpy as np
import base64
from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS

# IMPORT YOUR MODULES
from emotion.emotion_module import predict_emotion_from_frame
from voice.interview_questions import QUESTIONS
from voice.answer_evaluator import evaluate_answer_completeness
from voice.nlp_evaluator import evaluate_nlp_answer
from voice.speech_confidence import calculate_speech_confidence
from interview.scoring_engine import calculate_final_interview_score

# =========================
# APP SETUP
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "../frontend/templates"),
    static_folder=os.path.join(BASE_DIR, "../frontend/static")
)
CORS(app)

app.secret_key = "supersecretkey"

# =========================
# DATABASE PATH
# =========================
DB_PATH = os.path.join(BASE_DIR, "database/interviews.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# =========================
# GLOBAL EMOTION COUNTER
# =========================
EMOTION_KEYS = ["happy", "neutral", "sad", "surprise", "fear", "angry"]

# =========================
# DATABASE INIT
# =========================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interview_answers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        question TEXT,
        answer TEXT,
        emotion_score REAL,
        speech_score REAL,
        answer_score REAL,
        final_score REAL,
        level TEXT,
        feedback TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(name, question)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interview_emotions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        happy INTEGER,
        neutral INTEGER,
        sad INTEGER,
        surprise INTEGER,
        fear INTEGER,
        angry INTEGER,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # NEW TABLE: stores each interview session total score
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interview_sessions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        overall_score REAL,
        emotion_score REAL,
        speech_score REAL,
        answer_score REAL,
        questions_answered INTEGER,
        questions_skipped INTEGER,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

init_db()

# =========================
# IMAGE DECODER
# =========================
def decode_image(data):
    if "," in data:
        data = data.split(",")[1]
    img_bytes = base64.b64decode(data)
    np_arr = np.frombuffer(img_bytes, np.uint8)
    return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

# =========================
# CLEAN FEEDBACK
# =========================
def clean_feedback(speech_feedback, answer_feedback, nlp_feedback):
    all_feedback = []

    for item in (speech_feedback + answer_feedback + nlp_feedback):
        if item and item not in all_feedback:
            all_feedback.append(item)

    final_feedback = []
    text_blob = " ".join(all_feedback).lower()

    if any(word in text_blob for word in [
        "confident", "assertive", "stronger wording", "action-oriented"
    ]):
        final_feedback.append("Try to speak more confidently and use stronger professional wording.")

    if any(word in text_blob for word in [
        "complete", "short", "detail", "specific", "structured", "sentence"
    ]):
        final_feedback.append("Make your answer more complete by adding relevant details and better structure.")

    if any(word in text_blob for word in [
        "relevant", "not fully relevant", "expected interview response"
    ]):
        final_feedback.append("Focus more directly on the question and include more relevant points.")

    if any(word in text_blob for word in [
        "weak words", "maybe", "i think", "probably", "guess", "perhaps"
    ]):
        final_feedback.append("Avoid uncertain words and answer in a more professional and direct manner.")

    if not final_feedback:
        final_feedback.append("Good response. Keep improving your clarity, confidence, and structure.")

    return final_feedback[:3]

# =========================
# ROUTES
# =========================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/interview")
def interview():
    # Reset session for a fresh interview
    session["current_session_answers"] = {}
    session["emotion_counts"] = {k: 0 for k in EMOTION_KEYS}
    session["user_name"] = ""
    session.modified = True

    return render_template("interview.html", questions=QUESTIONS)

@app.route("/analytics")
def analytics():
    return render_template("analytics.html")

@app.route("/result")
def result():
    user_name = session.get("user_name", "Candidate")
    return render_template("result.html", user_name=user_name)

@app.route("/interview/questions")
def get_questions():
    return jsonify({"questions": QUESTIONS})

# =========================
# EMOTION PREDICTION
# =========================
@app.route("/interview/predict", methods=["POST"])
def predict():
    frame = decode_image(request.json["image"])
    result = predict_emotion_from_frame(frame)
    emotion = result["emotion"]

    emotion_counts = session.get("emotion_counts", {k: 0 for k in EMOTION_KEYS})
    if emotion in emotion_counts:
        emotion_counts[emotion] += 1

    session["emotion_counts"] = emotion_counts
    session.modified = True

    return jsonify(result)

# =========================
# EVALUATE ANSWER
# =========================
@app.route("/evaluate_answer", methods=["POST"])
def evaluate_answer():
    data = request.json
    name = data.get("name", "Candidate").strip().lower()
    question = data.get("question", "").strip()
    answer = data.get("answer", "").strip()
    emotion_score = float(data.get("emotion_score", 0))

    # Save user name in session
    session["user_name"] = name

    current_session_answers = session.get("current_session_answers", {})

    # =========================
    # HANDLE SKIPPED ANSWER
    # =========================
    if not answer:
        skipped_feedback = ["Question skipped. Try answering every question to improve your interview performance."]

        current_session_answers[question] = {
            "question": question,
            "answer": "",
            "emotion_score": emotion_score,
            "speech_score": 0,
            "answer_score": 0,
            "final_score": 0,
            "level": "Skipped",
            "skipped": True,
            "feedback": skipped_feedback
        }

        session["current_session_answers"] = current_session_answers
        session.modified = True

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO interview_answers
        (name, question, answer, emotion_score, speech_score, answer_score, final_score, level, feedback)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            question,
            "",
            emotion_score,
            0,
            0,
            0,
            "Skipped",
            str({"final_feedback": skipped_feedback})
        ))
        conn.commit()
        conn.close()

        return jsonify({
            "final_score": 0,
            "speech_confidence_score": 0,
            "answer_completeness_score": 0,
            "overall_level": "Skipped",
            "feedback": {
                "final_feedback": skipped_feedback
            }
        })

    # =========================
    # NORMAL EVALUATION
    # =========================
    completeness = evaluate_answer_completeness(question, answer)
    speech = calculate_speech_confidence(answer)
    nlp = evaluate_nlp_answer(question, answer)

    answer_score = round((completeness["score"] * 0.4 + nlp["final_nlp_score"] * 0.6), 2)

    final = calculate_final_interview_score(
        emotion_score,
        speech["score"],
        answer_score
    )

    cleaned_feedback = clean_feedback(
        speech["feedback"],
        completeness["feedback"],
        nlp["feedback"]
    )

    # Store full data in session
    current_session_answers[question] = {
        "question": question,
        "answer": answer,
        "emotion_score": emotion_score,
        "speech_score": speech["score"],
        "answer_score": answer_score,
        "final_score": final["final_score"],
        "level": final["level"],
        "skipped": False,
        "feedback": cleaned_feedback
    }

    session["current_session_answers"] = current_session_answers
    session.modified = True

    # Save to DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO interview_answers
    (name, question, answer, emotion_score, speech_score, answer_score, final_score, level, feedback)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        question,
        answer,
        emotion_score,
        speech["score"],
        answer_score,
        final["final_score"],
        final["level"],
        str({
            "final_feedback": cleaned_feedback
        })
    ))
    conn.commit()
    conn.close()

    return jsonify({
        "final_score": final["final_score"],
        "speech_confidence_score": speech["score"],
        "answer_completeness_score": answer_score,
        "overall_level": final["level"],
        "feedback": {
            "final_feedback": cleaned_feedback
        }
    })

# =========================
# GET LIVE ANALYTICS + PREVIOUS SCORE
# =========================
@app.route("/get_analytics/<name>")
def get_analytics(name):
    name = name.strip().lower()
    current_session_answers = session.get("current_session_answers", {})
    emotion_counts = session.get("emotion_counts", {k: 0 for k in EMOTION_KEYS})

    total_questions = len(QUESTIONS)

    if not current_session_answers:
        return jsonify({
            "overall_score": 0,
            "emotion_score": 0,
            "speech_score": 0,
            "answer_score": 0,
            "questions_answered": 0,
            "questions_skipped": total_questions,
            "emotions": emotion_counts,
            "summary": "No interview data found.",
            "prev_score": 0,
            "history": [0]
        })

    all_values = list(current_session_answers.values())
    answered_values = [v for v in all_values if not v.get("skipped", False)]
    skipped_values = [v for v in all_values if v.get("skipped", False)]

    emotion_scores = [v.get("emotion_score", 0) for v in answered_values]
    speech_scores = [v.get("speech_score", 0) for v in answered_values]
    answer_scores = [v.get("answer_score", 0) for v in answered_values]
    final_scores = [v.get("final_score", 0) for v in answered_values]

    overall_score = int(sum(final_scores) / len(final_scores)) if final_scores else 0
    emotion_score = int(sum(emotion_scores) / len(emotion_scores)) if emotion_scores else 0
    speech_score = int(sum(speech_scores) / len(speech_scores)) if speech_scores else 0
    answer_score = int(sum(answer_scores) / len(answer_scores)) if answer_scores else 0

    questions_answered = len(answered_values)
    questions_skipped = len(skipped_values)

    summary = (
        f"You answered {questions_answered} question(s) and skipped "
        f"{questions_skipped} question(s)."
    )

    # FETCH PREVIOUS SCORES FROM DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT overall_score
        FROM interview_sessions
        WHERE name = ?
        ORDER BY id DESC
    """, (name,))
    rows = cursor.fetchall()
    conn.close()

    history = [int(row[0]) for row in rows] if rows else []
    prev_score = history[-1] if history else 0

    # Add current score to chart history
    full_history = history + [overall_score]

    return jsonify({
        "overall_score": overall_score,
        "emotion_score": emotion_score,
        "speech_score": speech_score,
        "answer_score": answer_score,
        "questions_answered": questions_answered,
        "questions_skipped": questions_skipped,
        "emotions": emotion_counts,
        "summary": summary,
        "prev_score": prev_score,
        "history": full_history
    })

# =========================
# SAVE INTERVIEW SESSION
# =========================
@app.route("/save_interview_session", methods=["POST"])
def save_interview_session():
    data = request.json
    name = data.get("name", "Candidate").strip().lower()

    emotion_counts = session.get("emotion_counts", {k: 0 for k in EMOTION_KEYS})
    current_session_answers = session.get("current_session_answers", {})

    all_values = list(current_session_answers.values())
    answered_values = [v for v in all_values if not v.get("skipped", False)]
    skipped_values = [v for v in all_values if v.get("skipped", False)]

    emotion_scores = [v.get("emotion_score", 0) for v in answered_values]
    speech_scores = [v.get("speech_score", 0) for v in answered_values]
    answer_scores = [v.get("answer_score", 0) for v in answered_values]
    final_scores = [v.get("final_score", 0) for v in answered_values]

    overall_score = int(sum(final_scores) / len(final_scores)) if final_scores else 0
    emotion_score = int(sum(emotion_scores) / len(emotion_scores)) if emotion_scores else 0
    speech_score = int(sum(speech_scores) / len(speech_scores)) if speech_scores else 0
    answer_score = int(sum(answer_scores) / len(answer_scores)) if answer_scores else 0

    questions_answered = len(answered_values)
    questions_skipped = len(skipped_values)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Save emotion counts
    cursor.execute("""
    INSERT INTO interview_emotions
    (name, happy, neutral, sad, surprise, fear, angry)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        emotion_counts.get("happy", 0),
        emotion_counts.get("neutral", 0),
        emotion_counts.get("sad", 0),
        emotion_counts.get("surprise", 0),
        emotion_counts.get("fear", 0),
        emotion_counts.get("angry", 0),
    ))

    # Save full interview session score
    cursor.execute("""
    INSERT INTO interview_sessions
    (name, overall_score, emotion_score, speech_score, answer_score, questions_answered, questions_skipped)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        overall_score,
        emotion_score,
        speech_score,
        answer_score,
        questions_answered,
        questions_skipped
    ))

    conn.commit()
    conn.close()

    return jsonify({"message": "Interview session saved successfully"})

# =========================
# PERFORMANCE DASHBOARD
# =========================
@app.route("/performance_dashboard")
def performance_dashboard():
    current_session_answers = session.get("current_session_answers", {})
    if not current_session_answers:
        return "<h2>No interview data found in current session.</h2>"

    user_name = session.get("user_name", "Candidate")
    questions_data = []

    for idx, question in enumerate(QUESTIONS, start=1):
        data = current_session_answers.get(question, {
            "answer": "",
            "emotion_score": 0,
            "speech_score": 0,
            "answer_score": 0,
            "final_score": 0,
            "level": "Not Answered",
            "skipped": True,
            "feedback": []
        })

        questions_data.append({
            "q_id": idx,
            "question": question,
            "answer": data.get("answer", ""),
            "emotion_score": data.get("emotion_score", 0),
            "speech_score": data.get("speech_score", 0),
            "answer_score": data.get("answer_score", 0),
            "final_score": data.get("final_score", 0),
            "level": data.get("level", "Not Answered"),
            "feedback": data.get("feedback", []),
            "skipped": data.get("skipped", False)
        })

    return render_template(
        "performance_dashboard.html",
        questions=questions_data,
        user_name=user_name
    )

# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)