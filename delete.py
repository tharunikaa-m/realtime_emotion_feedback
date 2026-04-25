import sqlite3
import os

# Path to your database
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database/interviews.db")

# Connect to the database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ============================
# DELETE ENTRIES
# ============================

# 1️⃣ Delete all entries from interview_answers
cursor.execute("DELETE FROM interview_answers")
print("All entries from 'interview_answers' deleted.")

# 2️⃣ Delete all entries from interview_emotions
cursor.execute("DELETE FROM interview_emotions")
print("All entries from 'interview_emotions' deleted.")

# Commit changes
conn.commit()

# Close connection
conn.close()

print("Database cleanup complete!")