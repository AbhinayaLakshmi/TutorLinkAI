"""
Scoring algorithms for TutorLinkAI matching engine:
- Location scoring (Haversine distance decay)
- Fee scoring (Budget range with tolerance decay)
- Time scoring (Availability interval overlap ratio)
- Composite scoring & MinMaxScaler normalization
"""
import math
import re
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from .config import (
    DEFAULT_WEIGHT_LEARNING_NEED,
    DEFAULT_WEIGHT_SUBJECT,
    DEFAULT_WEIGHT_LOCATION,
    DEFAULT_WEIGHT_FEE,
    DEFAULT_WEIGHT_TIME,
    DEFAULT_MAX_RADIUS_KM,
    DEFAULT_FEE_TOLERANCE_RATIO,
    EARTH_RADIUS_KM,
)


def calculate_topic_overlap(
    student_topics: List[str],
    tutor_topics: List[str],
) -> Tuple[float, List[str]]:
    """
    Deterministic topic overlap computation.
    Evaluates:
    1. Exact string matches (case-insensitive)
    2. Substring containment
    3. Token-level overlap (e.g. 'rotational motion' vs 'rotational mechanics')

    Returns:
    - topic_score: float in [0.0, 1.0] representing coverage ratio
    - matched_topics: List of student topic names that matched tutor topics
    """
    if not student_topics:
        return 0.0, []
    if not tutor_topics:
        return 0.0, []

    matched_topics: List[str] = []
    total_match_score: float = 0.0

    # Clean tutor topics and extract token sets
    cleaned_tutor_topics = []
    for t in tutor_topics:
        t_str = str(t).strip().lower()
        if t_str:
            tokens = set(re.findall(r'\b[a-zA-Z0-9]+\b', t_str))
            cleaned_tutor_topics.append((t_str, tokens))

    if not cleaned_tutor_topics:
        return 0.0, []

    for s_topic in student_topics:
        s_raw = str(s_topic).strip()
        s_clean = s_raw.lower()
        if not s_clean:
            continue

        s_tokens = set(re.findall(r'\b[a-zA-Z0-9]+\b', s_clean))
        best_match_for_topic = 0.0

        for t_clean, t_tokens in cleaned_tutor_topics:
            # 1. Exact match (case-insensitive)
            if s_clean == t_clean:
                best_match_for_topic = max(best_match_for_topic, 1.0)
                break
            # 2. Substring containment
            elif s_clean in t_clean or t_clean in s_clean:
                best_match_for_topic = max(best_match_for_topic, 0.90)
            # 3. Token-level overlap
            elif s_tokens and t_tokens:
                common = s_tokens.intersection(t_tokens)
                if common:
                    overlap_ratio = len(common) / max(len(s_tokens), 1)
                    token_score = 0.85 * overlap_ratio
                    best_match_for_topic = max(best_match_for_topic, token_score)

        if best_match_for_topic >= 0.35:
            matched_topics.append(s_raw)
            total_match_score += best_match_for_topic

    topic_score = total_match_score / max(len(student_topics), 1)
    return float(np.clip(topic_score, 0.0, 1.0)), matched_topics


def calculate_learning_need_score(
    semantic_score: float,
    topic_score: float,
    has_topics: bool = True,
) -> float:
    """
    Computes learning need compatibility score combining dense semantic compatibility
    and deterministic topic overlap.

    Note: The weights (0.60 semantic, 0.40 topic) are heuristic research-prototype weights
    and are NOT learned/trained weights.

    If the student did not specify any topics, the system gracefully relies 100% on semantic compatibility.
    """
    if has_topics:
        score = (0.60 * semantic_score) + (0.40 * topic_score)
    else:
        score = semantic_score

    return float(np.clip(score, 0.0, 1.0))


def calculate_haversine_distance(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calculate the great-circle distance between two points on the Earth
    in kilometers using the Haversine formula.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    distance_km = EARTH_RADIUS_KM * c
    return float(distance_km)


def calculate_location_score(
    student_lat: float,
    student_lon: float,
    tutor_lat: float,
    tutor_lon: float,
    max_radius_km: float = DEFAULT_MAX_RADIUS_KM,
) -> Tuple[float, float]:
    """
    Calculate location proximity score based on Haversine distance.
    Returns (location_score [0.0 - 1.0], distance_km).
    - If distance == 0, score is 1.0.
    - If distance >= max_radius_km, score is 0.0.
    - Linear decay within radius: 1.0 - (distance / max_radius_km).
    """
    distance_km = calculate_haversine_distance(
        student_lat, student_lon, tutor_lat, tutor_lon
    )
    if distance_km <= 0.0:
        score = 1.0
    elif distance_km >= max_radius_km:
        score = 0.0
    else:
        score = 1.0 - (distance_km / max_radius_km)

    return float(np.clip(score, 0.0, 1.0)), float(round(distance_km, 2))


def calculate_fee_score(
    tutor_rate: float,
    budget_min: float,
    budget_max: float,
    tolerance_ratio: float = DEFAULT_FEE_TOLERANCE_RATIO,
) -> float:
    """
    Calculate fee score based on student budget range:
    - 1.0 if tutor_rate is within [budget_min, budget_max].
    - Linear decay outside [budget_min, budget_max] up to tolerance band.
    - 0.0 beyond tolerance band.
    """
    b_min = min(budget_min, budget_max)
    b_max = max(budget_min, budget_max)

    if b_min <= tutor_rate <= b_max:
        return 1.0

    if tutor_rate < b_min:
        tolerance_window = max(b_min * tolerance_ratio, 50.0)
        diff = b_min - tutor_rate
        if diff <= tolerance_window:
            score = 1.0 - (diff / tolerance_window)
        else:
            score = 0.0
        return float(np.clip(score, 0.0, 1.0))

    tolerance_window = max(b_max * tolerance_ratio, 50.0)
    diff = tutor_rate - b_max
    if diff <= tolerance_window:
        score = 1.0 - (diff / tolerance_window)
    else:
        score = 0.0
    return float(np.clip(score, 0.0, 1.0))


def _parse_time_to_minutes(time_str: str) -> int:
    """Parse 'HH:MM' string to minutes from midnight."""
    parts = time_str.strip().split(":")
    hours = int(parts[0])
    minutes = int(parts[1]) if len(parts) > 1 else 0
    return hours * 60 + minutes


def calculate_time_score(
    requested_slots: List[Dict[str, Any]],
    tutor_slots: List[Dict[str, Any]],
) -> float:
    """
    Calculate availability score as the ratio of overlapping time between
    student requested slots and tutor available slots.
    Each slot format: {'day': 'Monday', 'start_time': '16:00', 'end_time': '18:00'}
    """
    if not requested_slots:
        return 1.0
    if not tutor_slots:
        return 0.0

    total_requested_minutes = 0
    total_overlap_minutes = 0

    normalized_tutor_slots = []
    for slot in tutor_slots:
        try:
            day = slot.get("day", "").strip().lower()
            start = _parse_time_to_minutes(slot.get("start_time", "00:00"))
            end = _parse_time_to_minutes(slot.get("end_time", "00:00"))
            if end > start:
                normalized_tutor_slots.append((day, start, end))
        except (ValueError, KeyError, AttributeError):
            continue

    for req_slot in requested_slots:
        try:
            req_day = req_slot.get("day", "").strip().lower()
            req_start = _parse_time_to_minutes(req_slot.get("start_time", "00:00"))
            req_end = _parse_time_to_minutes(req_slot.get("end_time", "00:00"))
            slot_duration = max(0, req_end - req_start)
            if slot_duration == 0:
                continue

            total_requested_minutes += slot_duration

            slot_overlap = 0
            for t_day, t_start, t_end in normalized_tutor_slots:
                if t_day == req_day:
                    overlap_start = max(req_start, t_start)
                    overlap_end = min(req_end, t_end)
                    overlap = max(0, overlap_end - overlap_start)
                    slot_overlap = max(slot_overlap, overlap)

            total_overlap_minutes += slot_overlap

        except (ValueError, KeyError, AttributeError):
            continue

    if total_requested_minutes == 0:
        return 1.0

    score = total_overlap_minutes / float(total_requested_minutes)
    return float(np.clip(score, 0.0, 1.0))


def normalize_scores_minmax(
    sub_scores_matrix: np.ndarray,
) -> np.ndarray:
    """
    Normalizes candidate sub-scores using Scikit-Learn's MinMaxScaler.
    If only one candidate or constant column, sub-scores are retained as [0, 1].
    """
    if sub_scores_matrix.size == 0:
        return sub_scores_matrix

    scaled = np.copy(sub_scores_matrix)
    for col in range(scaled.shape[1]):
        col_values = scaled[:, col]
        val_min = np.min(col_values)
        val_max = np.max(col_values)
        if val_max - val_min > 0.001:
            scaler = MinMaxScaler(feature_range=(0.0, 1.0))
            scaled[:, col] = scaler.fit_transform(col_values.reshape(-1, 1)).flatten()
        else:
            scaled[:, col] = col_values

    return scaled


def calculate_composite_score(
    learning_need_score: Optional[float] = None,
    location_score: float = 0.0,
    fee_score: float = 0.0,
    time_score: float = 0.0,
    weight_learning_need: float = DEFAULT_WEIGHT_LEARNING_NEED,
    weight_location: float = DEFAULT_WEIGHT_LOCATION,
    weight_fee: float = DEFAULT_WEIGHT_FEE,
    weight_time: float = DEFAULT_WEIGHT_TIME,
    # Backward compatibility parameter aliases
    subject_score: Optional[float] = None,
    weight_subject: Optional[float] = None,
) -> float:
    """
    Compute final weighted composite score in range [0.0, 1.0].
    Note: The weights (0.45 learning need, 0.20 location, 0.20 fee, 0.15 time) are
    heuristic research-prototype weights and are NOT learned/trained weights.
    Weights are normalized so their sum equals 1.0.
    """
    if learning_need_score is None and subject_score is not None:
        actual_ln_score = subject_score
    elif learning_need_score is not None:
        actual_ln_score = learning_need_score
    else:
        actual_ln_score = 0.0

    if weight_subject is not None and weight_learning_need == DEFAULT_WEIGHT_LEARNING_NEED:
        actual_w_ln = weight_subject
    else:
        actual_w_ln = weight_learning_need

    total_weight = actual_w_ln + weight_location + weight_fee + weight_time
    if total_weight <= 0:
        total_weight = 1.0
        w_ln, w_loc, w_fee, w_time = 0.45, 0.20, 0.20, 0.15
    else:
        w_ln = actual_w_ln / total_weight
        w_loc = weight_location / total_weight
        w_fee = weight_fee / total_weight
        w_time = weight_time / total_weight

    composite = (
        (actual_ln_score * w_ln)
        + (location_score * w_loc)
        + (fee_score * w_fee)
        + (time_score * w_time)
    )
    return float(np.clip(composite, 0.0, 1.0))

