import re

HEDGING_WORDS = ['maybe', 'probably', 'i think', 'possibly', 'perhaps', 'i guess', 'could be']
ASSERTIVE_WORDS = ['definitely', 'confident', 'successfully', 'implemented', 'achieved', 'led', 'developed']

def word_count(text):
    return len(text.split())

def count_sentences(text):
    return len(re.findall(r'[.!?]', text)) or 1

def hedging_score(text):
    text = text.lower()
    count = sum(text.count(w) for w in HEDGING_WORDS)
    return max(0, 100 - count * 15)

def assertiveness_score(text):
    text = text.lower()
    count = sum(text.count(w) for w in ASSERTIVE_WORDS)
    return min(100, 40 + count * 12)

def structure_score(text):
    wc = word_count(text)
    sc = count_sentences(text)

    score = 0

    if wc >= 40:
        score += 50
    elif wc >= 25:
        score += 35
    elif wc >= 10:
        score += 20
    else:
        score += 10

    if sc >= 3:
        score += 50
    elif sc >= 2:
        score += 35
    else:
        score += 15

    return min(score, 100)

def calculate_speech_confidence(text):
    if not text.strip():
        return {
            "score": 0,
            "level": "Low",
            "feedback": ["No spoken answer detected."]
        }

    hedge = hedging_score(text)
    assertive = assertiveness_score(text)
    structure = structure_score(text)

    final_score = round((hedge * 0.3) + (assertive * 0.35) + (structure * 0.35), 2)

    if final_score >= 80:
        level = "High"
    elif final_score >= 60:
        level = "Moderate"
    else:
        level = "Low"

    feedback = []
    if hedge < 60:
        feedback.append("Avoid too many uncertain words like 'maybe' or 'I think'.")
    if assertive < 60:
        feedback.append("Use more confident and action-oriented wording.")
    if structure < 60:
        feedback.append("Speak in a more complete and structured way.")
    if final_score >= 80:
        feedback.append("Your speaking style appears confident.")

    return {
        "score": final_score,
        "level": level,
        "feedback": feedback
    }