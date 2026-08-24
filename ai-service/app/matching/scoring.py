"""
Scoring algorithms for TutorLinkAI matching engine:
- Location scoring (Haversine distance decay)
- Fee scoring (Budget range with tolerance decay)
- Time scoring (Availability interval overlap ratio)
- Composite scoring & MinMaxScaler normalization
"""
import math
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from .config import (
    DEFAULT_WEIGHT_SUBJECT,
    DEFAULT_WEIGHT_LOCATION,
    DEFAULT_WEIGHT_FEE,
    DEFAULT_WEIGHT_TIME,
    DEFAULT_MAX_RADIUS_KM,
    DEFAULT_FEE_TOLERANCE_RATIO,
    EARTH_RADIUS_KM,
)


def calculate_haversine_distance(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calculate the great-circle distance between two points on the Earth
    in kilometers using the Haversine formula.
    """
    # Convert latitude and longitude from degrees to radians
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
    # Ensure min <= max
    b_min = min(budget_min, budget_max)
    b_max = max(budget_min, budget_max)

    if b_min <= tutor_rate <= b_max:
        return 1.0

    if tutor_rate < b_min:
        # Lower than min budget: decay window
        tolerance_window = max(b_min * tolerance_ratio, 50.0)
        diff = b_min - tutor_rate
        if diff <= tolerance_window:
            score = 1.0 - (diff / tolerance_window)
        else:
            score = 0.0
        return float(np.clip(score, 0.0, 1.0))

    # tutor_rate > b_max
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
        # If student has no specific constraints, neutral match
        return 1.0
    if not tutor_slots:
        return 0.0

    total_requested_minutes = 0
    total_overlap_minutes = 0

    # Normalize day names to lowercase for comparison
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

            # Find maximum overlap for this requested slot across tutor's slots for that day
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

    # If all rows have identical values for a column, MinMaxScaler sets them to 0.
    # To maintain semantic absolute quality, we only scale if spread exists and range >= 0.05
    scaled = np.copy(sub_scores_matrix)
    for col in range(scaled.shape[1]):
        col_values = scaled[:, col]
        val_min = np.min(col_values)
        val_max = np.max(col_values)
        if val_max - val_min > 0.001:
            scaler = MinMaxScaler(feature_range=(0.0, 1.0))
            scaled[:, col] = scaler.fit_transform(col_values.reshape(-1, 1)).flatten()
        else:
            # Preserve original absolute scores if all identical
            scaled[:, col] = col_values

    return scaled


def calculate_composite_score(
    subject_score: float,
    location_score: float,
    fee_score: float,
    time_score: float,
    weight_subject: float = DEFAULT_WEIGHT_SUBJECT,
    weight_location: float = DEFAULT_WEIGHT_LOCATION,
    weight_fee: float = DEFAULT_WEIGHT_FEE,
    weight_time: float = DEFAULT_WEIGHT_TIME,
) -> float:
    """
    Compute final weighted composite score in range [0.0, 1.0].
    Weights are normalized so their sum equals 1.0.
    """
    total_weight = weight_subject + weight_location + weight_fee + weight_time
    if total_weight <= 0:
        total_weight = 1.0
        w_sub, w_loc, w_fee, w_time = 0.4, 0.2, 0.2, 0.2
    else:
        w_sub = weight_subject / total_weight
        w_loc = weight_location / total_weight
        w_fee = weight_fee / total_weight
        w_time = weight_time / total_weight

    composite = (
        (subject_score * w_sub)
        + (location_score * w_loc)
        + (fee_score * w_fee)
        + (time_score * w_time)
    )
    return float(np.clip(composite, 0.0, 1.0))
