def calculate_final_interview_score(emotion_score, speech_score, completeness_score):
    final_score = round(
        (emotion_score * 0.20) +
        (speech_score * 0.30) +
        (completeness_score * 0.50),
        2
    )

    if final_score >= 85:
        level = "Excellent"
    elif final_score >= 70:
        level = "Good"
    elif final_score >= 50:
        level = "Average"
    else:
        level = "Needs Improvement"

    return {
        "final_score": final_score,
        "level": level
    }