import cv2
import numpy as np
import os
from collections import Counter
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.mobilenet import preprocess_input

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "raf_emotion_model.keras")
FACE_FOLDER = os.path.join(BASE_DIR, "faces")

emotion_labels = [
    "Surprise",
    "Fear",
    "Disgust",
    "Happy",
    "Sad",
    "Angry",
    "Neutral"
]

model = load_model(MODEL_PATH)

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

state_window = []
state_summary = {"Nervous": 0, "Calm": 0, "Confident": 0}

def map_interview_state(emotion):
    if emotion in ["Sad", "Fear", "Disgust"]:
        return "Nervous"
    elif emotion in ["Happy", "Surprise"]:
        return "Confident"
    else:
        return "Calm"

def recognize_user(face_img):
    try:
        face_img = cv2.resize(face_img, (100, 100))
        best_match = None
        min_diff = float("inf")

        for file in os.listdir(FACE_FOLDER):
            path = os.path.join(FACE_FOLDER, file)
            saved = cv2.imread(path)

            if saved is None:
                continue

            saved = cv2.resize(saved, (100, 100))
            diff = np.sum((saved.astype("float") - face_img.astype("float")) ** 2)

            if diff < min_diff:
                min_diff = diff
                best_match = file.split(".")[0]

        if min_diff < 20000000:
            return best_match

        return None
    except:
        return None

def predict_emotion_from_frame(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    face_count = len(faces)

    if face_count == 0:
        face_status = "No face detected"
    elif face_count == 1:
        face_status = "Single user detected"
    else:
        face_status = "Multiple users detected"

    emotion = "Neutral"
    confidence = 0
    interview_state = "Calm"
    user_name = None
    emotion_score = 50

    if len(faces) > 0:
        x, y, w, h = faces[0]
        face = frame[y:y+h, x:x+w]

        user_name = recognize_user(face)

        face_resized = cv2.resize(face, (224, 224))
        face_resized = cv2.cvtColor(face_resized, cv2.COLOR_BGR2RGB)
        face_resized = face_resized.astype("float32")
        face_resized = preprocess_input(face_resized)
        face_resized = np.expand_dims(face_resized, axis=0)

        preds = model.predict(face_resized, verbose=0)

        emotion = emotion_labels[np.argmax(preds)]
        confidence = float(np.max(preds))
        interview_state = map_interview_state(emotion)

        if interview_state == "Confident":
            emotion_score = 90
        elif interview_state == "Calm":
            emotion_score = 75
        else:
            emotion_score = 45

        state_window.append(interview_state)

        if len(state_window) >= 15:
            final_state = Counter(state_window).most_common(1)[0][0]
            state_summary[final_state] += 1
            state_window.clear()

    return {
        "user": user_name,
        "emotion": emotion.lower(),
        "state": interview_state,
        "confidence": round(confidence * 100, 2),
        "face_status": face_status,
        "face_count": face_count,
        "emotion_score": emotion_score
    }