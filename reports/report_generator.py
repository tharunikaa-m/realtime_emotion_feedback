def generate_interview_report(name, question, answer, emotion_score, speech_result, completeness_result, final_result):
    return {
        "candidate_name": name,
        "question": question,
        "answer": answer,
        "emotion_score": emotion_score,
        "speech_confidence_score": speech_result["score"],
        "speech_level": speech_result["level"],
        "answer_completeness_score": completeness_result["score"],
        "answer_level": completeness_result["level"],
        "final_score": final_result["final_score"],
        "overall_level": final_result["level"],
        "feedback": {
            "speech_feedback": speech_result["feedback"],
            "answer_feedback": completeness_result["feedback"]
        }
    }