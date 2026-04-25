import numpy as np
from sentence_transformers import SentenceTransformer, util

# ==========================================
# LOAD NLP MODEL
# ==========================================
print("Loading NLP model...")
model = SentenceTransformer("all-MiniLM-L6-v2")
print("NLP model loaded successfully.")

# ==========================================
# IDEAL SAMPLE ANSWERS FOR QUESTIONS
# ==========================================
IDEAL_ANSWERS = {
    "Tell me about yourself": """
    I am a motivated and dedicated student with strong interest in technology,
    problem solving, and software development. I enjoy learning new skills and
    working on real-world projects that improve my technical and communication abilities.
    """,

    "What are your strengths?": """
    My strengths include communication, teamwork, problem solving, adaptability,
    and the ability to learn quickly. I am also responsible, organized, and confident
    while handling tasks and deadlines.
    """,

    "Explain your project": """
    My project is an AI-based interview trainer that analyzes candidate performance
    using face emotion detection, speech confidence analysis, NLP-based answer evaluation,
    and interview scoring to help improve interview preparation.
    """,

    "Why should we hire you?": """
    You should hire me because I am a quick learner, hardworking, responsible,
    and committed to giving my best. I can adapt to new challenges and contribute
    effectively through both technical skills and teamwork.
    """
}

# ==========================================
# ASSERTIVE / PROFESSIONAL SENTENCES
# ==========================================
ASSERTIVE_REFERENCE = [
    "I led the project successfully",
    "I managed responsibilities confidently",
    "I solved problems effectively",
    "I communicated clearly and professionally",
    "I completed the task efficiently",
    "I am confident in my abilities",
    "I worked with dedication and responsibility",
    "I handled challenges successfully"
]

assertive_embeddings = model.encode(ASSERTIVE_REFERENCE, convert_to_tensor=True)

# ==========================================
# BASIC TEXT CLEANER
# ==========================================
def clean_text(text):
    if not text:
        return ""
    return " ".join(text.strip().split())

# ==========================================
# SEMANTIC SIMILARITY SCORE
# ==========================================
def semantic_similarity(text1, text2):
    text1 = clean_text(text1)
    text2 = clean_text(text2)

    if not text1 or not text2:
        return 0.0

    emb1 = model.encode(text1, convert_to_tensor=True)
    emb2 = model.encode(text2, convert_to_tensor=True)

    score = util.cos_sim(emb1, emb2).item()
    return float(score)

# ==========================================
# RELEVANCE SCORE (Question vs Answer)
# ==========================================
def get_relevance_score(question, answer):
    score = semantic_similarity(question, answer)

    # Convert to 100
    score_100 = max(0, min(100, round(score * 100, 2)))
    return score_100

# ==========================================
# COMPLETENESS SCORE
# ==========================================
def get_completeness_score(answer):
    answer = clean_text(answer)
    word_count = len(answer.split())

    if word_count >= 40:
        return 95
    elif word_count >= 30:
        return 85
    elif word_count >= 20:
        return 70
    elif word_count >= 10:
        return 55
    elif word_count >= 5:
        return 35
    else:
        return 15

# ==========================================
# IDEAL ANSWER MATCH SCORE
# ==========================================
def get_ideal_match_score(question, answer):
    ideal_answer = IDEAL_ANSWERS.get(question, "")

    if not ideal_answer:
        return 50

    score = semantic_similarity(answer, ideal_answer)
    score_100 = max(0, min(100, round(score * 100, 2)))
    return score_100

# ==========================================
# ASSERTIVENESS SCORE
# ==========================================
def get_assertiveness_score(answer):
    answer = clean_text(answer)

    if not answer:
        return 0

    answer_embedding = model.encode(answer, convert_to_tensor=True)
    similarity = util.cos_sim(answer_embedding, assertive_embeddings).max().item()

    score_100 = max(0, min(100, round(similarity * 100, 2)))
    return score_100

# ==========================================
# HEDGING / WEAK LANGUAGE PENALTY
# ==========================================
HEDGING_WORDS = [
    "maybe", "probably", "i think", "i guess",
    "perhaps", "sort of", "kind of", "could be"
]

def get_hedging_penalty(answer):
    answer_lower = answer.lower()
    count = sum(answer_lower.count(word) for word in HEDGING_WORDS)

    penalty = min(count * 8, 30)  # max penalty 30
    return penalty

# ==========================================
# FEEDBACK GENERATOR
# ==========================================
def generate_nlp_feedback(relevance, completeness, ideal_match, assertiveness, hedging_penalty):
    feedback = []

    if relevance < 50:
        feedback.append("Your answer is not fully relevant to the question.")

    if completeness < 50:
        feedback.append("Your answer is too short. Add more explanation and detail.")

    if ideal_match < 50:
        feedback.append("Your answer could be improved by matching the expected interview response more closely.")

    if assertiveness < 50:
        feedback.append("Use stronger and more confident wording in your response.")

    if hedging_penalty >= 10:
        feedback.append("Avoid weak words like 'maybe', 'I think', or 'probably'.")

    if not feedback:
        feedback.append("Good answer. It is relevant, reasonably complete, and professionally expressed.")

    return feedback

# ==========================================
# MAIN NLP EVALUATION FUNCTION
# ==========================================
def evaluate_nlp_answer(question, answer):
    question = clean_text(question)
    answer = clean_text(answer)

    if not answer:
        return {
            "relevance_score": 0,
            "completeness_score": 0,
            "ideal_match_score": 0,
            "assertiveness_score": 0,
            "hedging_penalty": 0,
            "final_nlp_score": 0,
            "feedback": ["No answer provided."]
        }

    relevance = get_relevance_score(question, answer)
    completeness = get_completeness_score(answer)
    ideal_match = get_ideal_match_score(question, answer)
    assertiveness = get_assertiveness_score(answer)
    hedging_penalty = get_hedging_penalty(answer)

    final_score = (
    relevance * 0.40 +
    completeness * 0.25 +
    ideal_match * 0.15 +
    assertiveness * 0.20
) - hedging_penalty
    
    final_score = max(0, min(100, round(final_score, 2)))

    feedback = generate_nlp_feedback(
        relevance, completeness, ideal_match, assertiveness, hedging_penalty
    )

    return {
        "relevance_score": round(relevance, 2),
        "completeness_score": round(completeness, 2),
        "ideal_match_score": round(ideal_match, 2),
        "assertiveness_score": round(assertiveness, 2),
        "hedging_penalty": round(hedging_penalty, 2),
        "final_nlp_score": round(final_score, 2),
        "feedback": feedback
    }