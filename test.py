import tensorflow as tf
import mediapipe as mp

print(tf.__version__)   # should be 2.10
print(hasattr(mp, "solutions"))  # should be True

mp_face = mp.solutions.face_detection
print("All working ✅")