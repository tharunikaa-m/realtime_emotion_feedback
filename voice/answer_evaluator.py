import re

QUESTION_BLUEPRINTS = {
    "Tell me about yourself": {
    "must_have_groups": {
      "intro": ["name", "background", "experience", "education", "skills"],
      "personal": ["passion", "interest", "strength", "goal"],
      "relevance": ["role", "position", "company", "fit"]
    },
    "generic_bad_phrases": ["i am just here", "nothing special", "no experience"]
  },

  "What are your strengths?": {
    "must_have_groups": {
      "strength": ["strength", "skill", "ability", "quality", "expertise"],
      "example": ["achieved", "used", "demonstrated", "success"],
      "impact": ["result", "benefit", "helped", "improved"]
    },
    "generic_bad_phrases": ["i have no strengths", "not sure", "everything"]
  },

  "Explain your project": {
    "must_have_groups": {
      "project": ["project", "system", "app", "tool", "model"],
      "tech": ["python", "java", "flask", "django", "tensorflow", "react", "opencv"],
      "role": ["developed", "implemented", "designed", "led", "contributed"],
      "impact": ["result", "improved", "success", "achieved"]
    },
    "generic_bad_phrases": ["i cannot explain", "no idea", "not sure"]
  },

  "Why should we hire you?": {
    "must_have_groups": {
      "fit": ["skills", "experience", "knowledge", "strength", "ability"],
      "value": ["contribute", "help", "improve", "team", "company"],
      "confidence": ["ready", "motivated", "committed", "passionate"]
    },
    "generic_bad_phrases": ["i don't know", "everyone is same", "no reason"]
  },

  "Describe a challenge you overcame": {
    "must_have_groups": {
      "challenge": ["challenge", "problem", "difficulty", "issue", "obstacle"],
      "action": ["solved", "handled", "implemented", "worked on", "addressed"],
      "result": ["success", "learned", "improved", "achieved", "outcome"]
    },
    "generic_bad_phrases": ["no challenges", "everything was easy", "never faced problem"]
  },

  "Where do you see yourself in 5 years?": {
    "must_have_groups": {
      "career": ["career", "role", "position", "growth", "development"],
      "skills": ["learn", "improve", "enhance", "knowledge", "experience"],
      "company": ["company", "team", "organization", "contribute", "impact"]
    },
    "generic_bad_phrases": ["i don't know", "anywhere", "no plans"]
  },

  "Why did you choose this career path?": {
    "must_have_groups": {
      "motivation": ["interest", "passion", "inspired", "curious", "fascinated"],
      "background": ["education", "project", "experience", "learning"],
      "alignment": ["career", "skills", "future", "goal", "fit"]
    },
    "generic_bad_phrases": ["just happened", "random choice", "no reason"]
  },

  "How do you handle stress?": {
    "must_have_groups": {
      "strategy": ["organize", "plan", "prioritize", "focus", "meditation", "exercise"],
      "example": ["handled", "managed", "overcame", "worked under pressure"],
      "result": ["success", "completed", "achieved", "maintain", "efficient"]
    },
    "generic_bad_phrases": ["panic", "give up", "cannot handle", "stress kills me"]
  },

  "Describe a team project you led": {
    "must_have_groups": {
      "role": ["leader", "managed", "coordinated", "organized", "led"],
      "teamwork": ["team", "collaborated", "members", "group", "communication"],
      "result": ["success", "achieved", "delivered", "improved", "impact"]
    },
    "generic_bad_phrases": ["did everything alone", "no teamwork", "never led"]
  },

  "Any questions for us?": {
    "must_have_groups": {
      "company": ["team", "culture", "values", "projects", "growth"],
      "role": ["responsibilities", "expectation", "tasks", "future"],
      "learning": ["learning", "training", "opportunity", "mentorship"]
    },
    "generic_bad_phrases": ["nothing", "no questions", "everything clear"]
  }
}

def clean_text(text):
    return re.sub(r'[^a-zA-Z0-9\s]', '', text.lower())

def count_sentences(text):
    return len(re.findall(r'[.!?]', text)) or 1

def word_count(text):
    return len(text.split())

def contains_phrase(answer_clean, phrase_list):
    return any(p in answer_clean for p in phrase_list)

def evaluate_answer_completeness(question, answer):
    answer_clean = clean_text(answer)

    if not answer.strip():
        return {
            "score": 0,
            "level": "Poor",
            "matched_groups": [],
            "missing_groups": [],
            "feedback": ["No answer detected."]
        }

    if question not in QUESTION_BLUEPRINTS:
        return basic_fallback_evaluation(answer)

    blueprint = QUESTION_BLUEPRINTS[question]
    must_have_groups = blueprint["must_have_groups"]
    generic_bad_phrases = blueprint["generic_bad_phrases"]

    matched_groups = []
    missing_groups = []

    group_score = 0
    per_group_score = 50 / len(must_have_groups)

    for group_name, phrases in must_have_groups.items():
        if contains_phrase(answer_clean, phrases):
            matched_groups.append(group_name)
            group_score += per_group_score
        else:
            missing_groups.append(group_name)

    wc = word_count(answer)
    sc = count_sentences(answer)

    structure_score = 0
    if wc >= 50:
        structure_score += 10
    elif wc >= 30:
        structure_score += 7
    elif wc >= 15:
        structure_score += 4
    else:
        structure_score += 1

    if sc >= 3:
        structure_score += 10
    elif sc >= 2:
        structure_score += 6
    else:
        structure_score += 2

    specificity_words = [
        "for example", "during", "in my project", "i used", "i worked on",
        "i developed", "i built", "i implemented", "i learned", "i improved"
    ]

    specificity_hits = sum(1 for phrase in specificity_words if phrase in answer_clean)

    if specificity_hits >= 3:
        specificity_score = 15
    elif specificity_hits == 2:
        specificity_score = 10
    elif specificity_hits == 1:
        specificity_score = 6
    else:
        specificity_score = 2

    professional_words = [
        "responsible", "dedicated", "teamwork", "leadership", "adaptable",
        "problem solving", "technical", "communication", "efficient",
        "organized", "confident", "professional", "goal-oriented"
    ]

    professional_hits = sum(1 for word in professional_words if word in answer_clean)

    if professional_hits >= 5:
        professional_score = 15
    elif professional_hits >= 3:
        professional_score = 10
    elif professional_hits >= 1:
        professional_score = 6
    else:
        professional_score = 2

    penalty = 0
    if contains_phrase(answer_clean, generic_bad_phrases):
        penalty += 10

    if wc < 10:
        penalty += 10

    final_score = round(group_score + structure_score + specificity_score + professional_score - penalty, 2)
    final_score = max(0, min(final_score, 100))

    if final_score >= 85:
        level = "Excellent"
    elif final_score >= 70:
        level = "Good"
    elif final_score >= 50:
        level = "Average"
    else:
        level = "Needs Improvement"

    feedback = []

    if wc < 20:
        feedback.append("Your answer is too short. Add more explanation.")
    if sc < 2:
        feedback.append("Try answering in full, structured sentences.")
    if missing_groups:
        feedback.append(f"Missing important parts: {', '.join(missing_groups)}.")
    if specificity_hits == 0:
        feedback.append("Add specific examples or details to strengthen your answer.")
    if professional_hits < 2:
        feedback.append("Use more professional and interview-appropriate wording.")
    if contains_phrase(answer_clean, generic_bad_phrases):
        feedback.append("Avoid overly generic or weak phrases.")
    if final_score >= 85:
        feedback.append("This is a strong and well-structured answer.")

    return {
        "score": final_score,
        "level": level,
        "matched_groups": matched_groups,
        "missing_groups": missing_groups,
        "feedback": feedback
    }

def basic_fallback_evaluation(answer):
    answer_clean = clean_text(answer)
    wc = word_count(answer)
    sc = count_sentences(answer)

    score = 0

    if wc >= 40:
        score += 40
    elif wc >= 20:
        score += 25
    elif wc >= 10:
        score += 15
    else:
        score += 5

    if sc >= 3:
        score += 25
    elif sc >= 2:
        score += 15
    else:
        score += 8

    detail_words = [
        "because", "for example", "during", "used", "developed", "worked", "learned", "improved"
    ]
    detail_hits = sum(1 for word in detail_words if word in answer_clean)
    score += min(detail_hits * 5, 35)

    score = min(score, 100)

    if score >= 85:
        level = "Excellent"
    elif score >= 70:
        level = "Good"
    elif score >= 50:
        level = "Average"
    else:
        level = "Needs Improvement"

    feedback = []
    if wc < 20:
        feedback.append("Answer is too short.")
    if sc < 2:
        feedback.append("Use more complete sentences.")
    if detail_hits == 0:
        feedback.append("Add more specific details.")

    return {
        "score": score,
        "level": level,
        "matched_groups": [],
        "missing_groups": [],
        "feedback": feedback
    }