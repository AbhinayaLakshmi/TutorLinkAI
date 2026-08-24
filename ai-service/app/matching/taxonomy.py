"""
Subject Taxonomy & Alias Gate for TutorLinkAI:
Provides deterministic Stage 1 subject eligibility gating with alias mappings,
preventing cross-subject contamination (e.g. Physics != Chemistry != Biology).
"""
import re
from typing import List, Set, Tuple, Optional, Dict

# Canonical subject clusters and recognized domain aliases
SUBJECT_TAXONOMY: Dict[str, List[str]] = {
    "chemistry": [
        "chemistry", "chem", "organic chemistry", "inorganic chemistry",
        "physical chemistry", "biochemistry", "chemical", "iit jee chemistry",
        "neet chemistry", "cbse chemistry", "class 11 chemistry",
        "class 12 chemistry", "ap chemistry", "igcse chemistry", "icse chemistry"
    ],
    "physics": [
        "physics", "phy", "mechanics", "electromagnetism", "thermodynamics",
        "optics", "quantum physics", "iit jee physics", "neet physics",
        "cbse physics", "class 11 physics", "class 12 physics", "ap physics",
        "igcse physics", "icse physics", "applied physics"
    ],
    "mathematics": [
        "mathematics", "math", "maths", "algebra", "calculus", "geometry",
        "trigonometry", "statistics", "stats", "arithmetic", "linear algebra",
        "applied mathematics", "discrete mathematics", "iit jee maths",
        "iit jee mathematics", "cbse math", "cbse maths", "class 10 cbse mathematics",
        "class 10 math", "class 10 maths", "class 11 math", "class 11 mathematics",
        "class 12 math", "class 12 mathematics", "ap calculus", "igcse math",
        "icse math", "pre-calculus", "differential equations"
    ],
    "biology": [
        "biology", "bio", "botany", "zoology", "genetics", "microbiology",
        "anatomy", "physiology", "neet biology", "cbse biology",
        "class 11 biology", "class 12 biology", "ap biology", "igcse biology",
        "icse biology", "life sciences", "molecular biology"
    ],
    "computer_science": [
        "computer science", "cs", "python", "python programming", "java",
        "c++", "c programming", "data science", "machine learning", "ai",
        "artificial intelligence", "web development", "javascript", "deep learning",
        "sql", "algorithms", "dsa", "data structures", "html", "css", "react",
        "programming", "software engineering", "coding"
    ],
    "french": [
        "french", "french language", "delf", "delf a1", "delf a2", "delf b1",
        "delf b2", "dalf", "fle", "spoken french", "french grammar"
    ],
    "spanish": [
        "spanish", "spanish language", "dele", "spoken spanish", "espanol",
        "spanish grammar"
    ],
    "german": [
        "german", "german language", "goethe", "deutsch", "spoken german"
    ],
    "english": [
        "english", "english literature", "spoken english", "grammar", "ielts",
        "toefl", "creative writing", "english language", "business english",
        "cbse english", "icse english"
    ],
    "commerce_economics": [
        "economics", "econ", "accountancy", "accounts", "commerce",
        "business studies", "finance", "microeconomics", "macroeconomics",
        "financial accounting", "cost accounting", "corporate finance"
    ],
    "music_arts": [
        "music", "carnatic music", "carnatic vocal", "western vocal", "guitar",
        "keyboard", "piano", "violin", "hindustani music", "classical music"
    ],
    "social_studies": [
        "history", "geography", "civics", "social studies", "social science",
        "political science", "sociology", "psychology"
    ],
}

# Individual token alias direct dictionary
EXACT_ALIAS_MAP: Dict[str, str] = {
    "chem": "chemistry",
    "phy": "physics",
    "phys": "physics",
    "math": "mathematics",
    "maths": "mathematics",
    "algebra": "mathematics",
    "calculus": "mathematics",
    "geometry": "mathematics",
    "trig": "mathematics",
    "trigonometry": "mathematics",
    "stats": "mathematics",
    "statistics": "mathematics",
    "bio": "biology",
    "botany": "biology",
    "zoology": "biology",
    "cs": "computer science",
    "prog": "computer science",
    "econ": "economics",
    "acc": "accountancy",
    "accounts": "accountancy",
}


def normalize_text(text: str) -> str:
    """Normalize subject string: lowercased, stripped punctuation, normalized whitespace."""
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s\+]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def get_canonical_domains(subject_text: str) -> Set[str]:
    """
    Finds matching canonical taxonomy domain(s) for a given subject string.
    e.g. "Class 10 CBSE Mathematics" -> {"mathematics"}
    """
    norm = normalize_text(subject_text)
    if not norm:
        return set()

    tokens = norm.split()
    matched_domains = set()

    # Check whole string and individual words/phrases against taxonomy
    for domain, terms in SUBJECT_TAXONOMY.items():
        for term in terms:
            norm_term = normalize_text(term)
            if norm_term == norm:
                matched_domains.add(domain)
                break
            # Word-level boundary match for multi-word or single word
            if f" {norm_term} " in f" {norm} ":
                matched_domains.add(domain)
                break

    # Check direct word alias map
    for t in tokens:
        if t in EXACT_ALIAS_MAP:
            target = EXACT_ALIAS_MAP[t]
            for domain, terms in SUBJECT_TAXONOMY.items():
                if target in terms:
                    matched_domains.add(domain)

    return matched_domains


def evaluate_subject_gate(
    requested_subject: str,
    tutor_subjects: List[str],
    embedding_service=None,
    similarity_threshold: float = 0.75,
) -> Tuple[bool, float]:
    """
    Stage 1: Subject Eligibility Gate (Pass / Fail).

    Returns:
      (is_eligible: bool, subject_score: float)

    Rules:
      1. Primary Check: Exact match, taxonomy match, or alias match on tutor subject tags.
      2. Secondary Check: Embedding similarity STRICTLY on tutor subject tags (NOT bio text)
         with a high threshold (>= 0.75) to prevent adjacent subject leakage.
      3. Bio text is never used to pass the subject gate.
    """
    req_norm = normalize_text(requested_subject)
    if not req_norm:
        return False, 0.0

    if not tutor_subjects:
        return False, 0.0

    clean_tutor_tags = [normalize_text(str(s)) for s in tutor_subjects if str(s).strip()]
    if not clean_tutor_tags:
        return False, 0.0

    # 1. Primary Check: Exact string or taxonomy/alias match
    # A. Check exact tag match
    for tag in clean_tutor_tags:
        if tag == req_norm:
            return True, 1.0
        # Substring / phrase match with word boundaries
        if len(req_norm) >= 3 and (f" {req_norm} " in f" {tag} " or f" {tag} " in f" {req_norm} "):
            return True, 1.0

    # B. Taxonomy domain intersection check
    req_domains = get_canonical_domains(requested_subject)
    if req_domains:
        for tag in clean_tutor_tags:
            tag_domains = get_canonical_domains(tag)
            # If there is a domain overlap, tutor qualifies with high confidence
            if req_domains.intersection(tag_domains):
                return True, 1.0

    # 2. Secondary Fallback Check: Sentence Transformer similarity ONLY on subject tags
    if embedding_service is not None:
        try:
            # Embed each tutor subject tag individually
            tag_scores = embedding_service.compute_subject_score(
                requested_subject, clean_tutor_tags
            )
            max_tag_score = max(tag_scores) if tag_scores else 0.0
            if max_tag_score >= similarity_threshold:
                return True, float(max_tag_score)
        except Exception:
            pass

    # If neither primary taxonomy nor tag embedding cleared threshold, FAIL gate
    return False, 0.0
