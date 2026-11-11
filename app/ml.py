"""
app/ml.py — ML-powered personalised insights for AssessMe
==========================================================

Provides four analysis functions, all operating solely on a user's own
AssessmentRecord history — no external data, no model files persisted
to disk, no network calls.

Public API
----------
run_ml_insights(records) -> dict
    Master function called by the progress route.  Passes records through
    all four analysis steps and returns a single dict ready for the template.

Internal steps
--------------
1. extract_features(records)       -> structured feature matrix + metadata
2. trend_prediction(feat)          -> per-assessment-type trajectory forecast
3. wellness_profile(feat)          -> KMeans cluster -> named wellness archetype
4. cross_assessment_correlation(feat) -> Pearson correlations between types
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

import numpy as np

# -- scikit-learn imports (lazy-safe: if sk-learn is somehow missing,
#    the module degrades gracefully rather than crashing at import time) --
try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import MinMaxScaler
    from sklearn.linear_model import LinearRegression
    _SK_AVAILABLE = True
except ImportError:
    _SK_AVAILABLE = False


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

# Human-readable names for the 7 assessment types
TYPE_LABELS: dict[str, str] = {
    "adhd":       "ADHD Screening",
    "anxiety":    "Anxiety Screening",
    "depression": "Depression Screening",
    "stress":     "Perceived Stress",
    "learning":   "Learning Style",
    "eq":         "Emotional Intelligence",
    "asd":        "ASD Support Screen",
}

# Wellness archetypes derived from KMeans clusters.
# Each archetype describes a recognisable combination of assessment patterns.
# Defined as (name, emoji, short_description, colour_class)
_ARCHETYPES: list[tuple[str, str, str, str]] = [
    (
        "Resilient Achiever",
        "",
        "Low stress and anxiety scores paired with solid emotional intelligence. "
        "You tend to manage pressure well and maintain perspective in difficult situations.",
        "success",
    ),
    (
        "Focused Thinker",
        "",
        "Strong attention to detail and structured thinking. You work best with clear goals "
        "and predictable environments, and you channel energy effectively into tasks.",
        "primary",
    ),
    (
        "Empathic Connector",
        "",
        "High emotional intelligence and social awareness. You are naturally attuned to others' "
        "feelings and excel in collaborative, people-centred settings.",
        "warning",
    ),
    (
        "Adaptive Learner",
        "",
        "A flexible, multimodal approach to taking in information. You shift strategies "
        "depending on the context and tend to learn best through variety.",
        "primary",
    ),
    (
        "Growth Explorer",
        "",
        "Some areas showing elevated scores worth monitoring. You are actively building "
        "self-awareness — recognising patterns is the first step toward change.",
        "warning",
    ),
    (
        "High-Energy Navigator",
        "",
        "High energy and drive can be a powerful asset. Channelling it with structure "
        "and regular self-check-ins helps sustain performance without burnout.",
        "danger",
    ),
]

# Minimum records required to attempt each analysis
_MIN_FOR_TREND       = 2   # need at least 2 records of the same type for a trend
_MIN_FOR_CLUSTER     = 2   # need records across at least 2 different types to cluster
_MIN_FOR_CORRELATION = 3   # need 3+ paired records to compute a meaningful correlation


# -----------------------------------------------------------------------------
# 1. Feature extraction
# -----------------------------------------------------------------------------

def extract_features(records: list) -> dict[str, Any]:
    """
    Convert AssessmentRecord ORM objects into a structured feature dict.

    Returns
    -------
    {
      "by_type": {
          "<type_key>": [
              {"pct": int, "raw": int, "band": str, "ts": float,
               "answers": dict, "personal_info": dict}
          ]  # sorted oldest-first
      },
      "all_pct": [int, ...],          # pct scores of all completed records
      "type_vector": {str: float},    # latest pct per type (0 if never taken)
      "all_types_taken": [str],       # unique types completed at least once
    }
    """
    by_type: dict[str, list] = defaultdict(list)

    for r in records:
        if r.status != "completed":
            continue
        by_type[r.assessment_type].append({
            "pct":          r.pct_score,
            "raw":          r.raw_score,
            "band":         r.band,
            "ts":           r.completed_at.timestamp(),
            "answers":      r.answers,
            "personal_info": r.personal_info,
        })

    # Sort each type oldest-first (ascending timestamp)
    for key in by_type:
        by_type[key].sort(key=lambda x: x["ts"])

    all_pct = [e["pct"] for entries in by_type.values() for e in entries]

    # Latest pct per type (0 when never taken)
    type_vector: dict[str, float] = {
        t: float(entries[-1]["pct"]) / 100.0
        for t, entries in by_type.items()
    }

    return {
        "by_type":        dict(by_type),
        "all_pct":        all_pct,
        "type_vector":    type_vector,
        "all_types_taken": list(by_type.keys()),
    }


# -----------------------------------------------------------------------------
# 2. Trend prediction  (per assessment type, Linear Regression on timestamps)
# -----------------------------------------------------------------------------

def trend_prediction(feat: dict[str, Any]) -> dict[str, Any]:
    """
    For each assessment type with ≥2 records, fit a linear regression of
    pct_score ~ time and predict the next likely score.

    Returns
    -------
    {
      "<type_key>": {
          "label":          str,
          "direction":      "improving" | "stable" | "worsening",
          "direction_icon": str (emoji),
          "slope":          float,          # pct points per day
          "predicted_next": int,            # clamped 0–100
          "confidence":     "low"|"medium"|"high",
          "history":        [int, ...],     # pct scores oldest-first
          "n":              int,
      }
    }
    """
    results: dict[str, Any] = {}
    by_type = feat["by_type"]

    for a_type, entries in by_type.items():
        n = len(entries)
        if n < _MIN_FOR_TREND:
            continue

        ts_arr  = np.array([e["ts"] for e in entries]).reshape(-1, 1)
        pct_arr = np.array([e["pct"] for e in entries], dtype=float)

        # Normalise timestamps to days-since-first to keep slope interpretable
        ts_days = (ts_arr - ts_arr[0]) / 86_400.0

        if _SK_AVAILABLE:
            reg = LinearRegression().fit(ts_days, pct_arr)
            slope_per_day = float(reg.coef_[0])
            # Predict at "now + 30 days" expressed relative to first record
            days_since_first_now = float((ts_arr[-1] - ts_arr[0]) / 86_400.0)
            next_days = days_since_first_now + 30.0
            predicted = float(reg.predict([[next_days]])[0])
        else:
            # Fallback: simple least-squares manually
            x = ts_days.flatten()
            y = pct_arr
            x_mean, y_mean = x.mean(), y.mean()
            denom = ((x - x_mean) ** 2).sum()
            slope_per_day = float(((x - x_mean) * (y - y_mean)).sum() / denom) if denom else 0.0
            days_now = x[-1]
            predicted = float(y_mean + slope_per_day * (days_now + 30.0 - x_mean))

        predicted = max(0, min(100, round(predicted)))

        # Direction: only call it improving/worsening if slope is meaningful
        # For clinical screening tools (adhd, anxiety, depression, stress, asd)
        # a *lower* score is better; for eq it's the reverse; learning is neutral.
        lower_is_better = a_type in {"adhd", "anxiety", "depression", "stress", "asd"}

        if abs(slope_per_day) < 0.15:           # < 0.15 pct pts / day ≈ ~4.5/month
            direction = "stable"
        elif lower_is_better:
            direction = "improving" if slope_per_day < 0 else "worsening"
        else:
            direction = "improving" if slope_per_day > 0 else "worsening"

        icons = {"improving": "" if lower_is_better else "",
                 "stable":    "->",
                 "worsening": "" if lower_is_better else ""}

        # Confidence based on sample size and R²
        if n >= 6:
            confidence = "high"
        elif n >= 3:
            confidence = "medium"
        else:
            confidence = "low"

        results[a_type] = {
            "label":          TYPE_LABELS.get(a_type, a_type),
            "direction":      direction,
            "direction_icon": icons[direction],
            "slope":          round(slope_per_day * 30, 1),   # pct pts / 30 days
            "predicted_next": predicted,
            "confidence":     confidence,
            "history":        [e["pct"] for e in entries],
            "n":              n,
            "lower_is_better": lower_is_better,
        }

    return results


# -----------------------------------------------------------------------------
# 3. Wellness profiling  (KMeans on cross-type score vector)
# -----------------------------------------------------------------------------

def wellness_profile(feat: dict[str, Any]) -> dict[str, Any] | None:
    """
    Build a feature vector from the user's latest score per assessment type
    and assign them to a named wellness archetype via KMeans (k=6).

    Because a single user is compared against synthetic reference points
    (not other users), we create a small reference population from the
    extremes and midpoints of the score space, then cluster everything
    together and return only the user's cluster assignment.

    Returns None if fewer than _MIN_FOR_CLUSTER assessment types are available.
    """
    type_vector = feat["type_vector"]
    if len(type_vector) < _MIN_FOR_CLUSTER:
        return None

    all_types = list(TYPE_LABELS.keys())  # fixed order
    # Build user feature vector (0 where type never taken)
    user_vec = np.array(
        [type_vector.get(t, 0.0) for t in all_types],
        dtype=float,
    ).reshape(1, -1)

    if not _SK_AVAILABLE:
        # Fallback: assign archetype by overall average score
        avg = float(user_vec.mean())
        if avg < 0.25:
            archetype_idx = 0   # Resilient Achiever
        elif avg < 0.45:
            archetype_idx = 1   # Focused Thinker
        elif avg < 0.60:
            archetype_idx = 3   # Adaptive Learner
        else:
            archetype_idx = 4   # Growth Explorer
    else:
        # Build synthetic reference population: 6 archetypes × their
        # characteristic score patterns (all in 0–1 space).
        # These are hand-crafted reference points that match the archetype
        # descriptions — they anchor the cluster centroids.
        #
        # Order: adhd, anxiety, depression, stress, learning, eq, asd
        refs = np.array([
            # 0 Resilient Achiever: low clinical, high eq, moderate learning
            [0.15, 0.15, 0.10, 0.20, 0.60, 0.80, 0.10],
            # 1 Focused Thinker: moderate adhd (attention detail), low anxiety, moderate eq
            [0.40, 0.20, 0.15, 0.25, 0.50, 0.55, 0.15],
            # 2 Empathic Connector: low clinical, very high eq, moderate everything
            [0.20, 0.25, 0.20, 0.30, 0.55, 0.90, 0.15],
            # 3 Adaptive Learner: balanced clinical, high learning variety
            [0.25, 0.30, 0.25, 0.35, 0.80, 0.65, 0.20],
            # 4 Growth Explorer: moderate-high clinical, growing eq
            [0.50, 0.50, 0.45, 0.55, 0.50, 0.50, 0.35],
            # 5 High-Energy Navigator: high adhd/stress, moderate others
            [0.70, 0.55, 0.40, 0.70, 0.45, 0.40, 0.25],
        ], dtype=float)

        # Combine user vector with references so KMeans has a full dataset
        X = np.vstack([refs, user_vec])           # shape (7, 7)

        scaler = MinMaxScaler()
        X_scaled = scaler.fit_transform(X)

        km = KMeans(n_clusters=6, n_init=20, random_state=42)
        labels = km.fit_predict(X_scaled)

        # The user is the last row
        user_cluster = int(labels[-1])

        # Map cluster to the closest reference archetype by centroid distance
        user_centroid = km.cluster_centers_[user_cluster]
        ref_scaled    = X_scaled[:6]              # first 6 rows are refs
        distances = np.linalg.norm(ref_scaled - user_centroid, axis=1)
        archetype_idx = int(np.argmin(distances))

    name, emoji, desc, colour = _ARCHETYPES[archetype_idx]

    # Compute per-type contribution for the radar-style breakdown
    taken_breakdown = [
        {
            "type":  t,
            "label": TYPE_LABELS[t],
            "pct":   round(type_vector[t] * 100),
            "icon":  _type_icon(t),
        }
        for t in all_types
        if t in type_vector
    ]

    return {
        "archetype_name":  name,
        "archetype_emoji": emoji,
        "archetype_desc":  desc,
        "archetype_colour": colour,
        "breakdown":       taken_breakdown,
        "types_taken":     len(type_vector),
        "types_total":     len(all_types),
    }


# -----------------------------------------------------------------------------
# 4. Cross-assessment correlation
# -----------------------------------------------------------------------------

def cross_assessment_correlation(feat: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Compute Pearson correlation between pairs of assessment types where the
    user has taken both ≥ _MIN_FOR_CORRELATION times.

    Because most users will have few records, this also does a simpler
    co-occurrence check (both types completed, latest scores compared)
    and returns readable insight strings.

    Returns a list of dicts:
    [
      {
        "type_a": str, "label_a": str,
        "type_b": str, "label_b": str,
        "r":      float,       # Pearson r, -1 to 1
        "n":      int,
        "insight": str,        # human-readable sentence
        "strength": "strong"|"moderate"|"weak",
        "direction": "positive"|"negative",
      }
    ]
    Returns [] if no pairs qualify.
    """
    by_type  = feat["by_type"]
    types    = list(by_type.keys())
    insights = []

    for i in range(len(types)):
        for j in range(i + 1, len(types)):
            ta, tb = types[i], types[j]
            entries_a = by_type[ta]
            entries_b = by_type[tb]

            # Align by shared session dates (within same calendar day)
            # If not enough shared dates, use positional alignment up to min length
            paired_a, paired_b = _align_records(entries_a, entries_b)
            n = len(paired_a)
            if n < _MIN_FOR_CORRELATION:
                continue

            arr_a = np.array(paired_a, dtype=float)
            arr_b = np.array(paired_b, dtype=float)

            # Pearson r
            if arr_a.std() == 0 or arr_b.std() == 0:
                continue
            r = float(np.corrcoef(arr_a, arr_b)[0, 1])
            if math.isnan(r):
                continue

            abs_r = abs(r)
            strength  = "strong" if abs_r >= 0.7 else "moderate" if abs_r >= 0.4 else "weak"
            direction = "positive" if r >= 0 else "negative"

            insight = _correlation_insight(ta, tb, r, strength)

            insights.append({
                "type_a":    ta,
                "label_a":   TYPE_LABELS.get(ta, ta),
                "type_b":    tb,
                "label_b":   TYPE_LABELS.get(tb, tb),
                "r":         round(r, 2),
                "n":         n,
                "insight":   insight,
                "strength":  strength,
                "direction": direction,
            })

    # Sort by absolute correlation descending
    insights.sort(key=lambda x: abs(x["r"]), reverse=True)
    return insights[:5]   # return top-5 most informative pairs


# -----------------------------------------------------------------------------
# Master entry point
# -----------------------------------------------------------------------------

def run_ml_insights(
    records: list,
    *,
    date_from: "datetime | None" = None,
    date_to:   "datetime | None" = None,
    types_include: "list[str] | None" = None,
    mode: str = "all",
) -> dict[str, Any]:
    """
    Run all ML analyses on a list of AssessmentRecord ORM objects.
    Always returns a valid dict — all sub-analyses degrade gracefully.

    Parameters
    ----------
    records        : all AssessmentRecord ORM objects for the user
    date_from      : only include records completed on/after this date (optional)
    date_to        : only include records completed on/before this date (optional)
    types_include  : whitelist of assessment_type keys; None = all types
    mode           : "all"    – use every completed record (default)
                     "recent" – keep only the most-recent N per type (N=5)
                     "trend"  – keep only types with ≥2 records (focus on trends)

    Returns
    -------
    {
      "available":     bool,
      "min_records":   int,
      "trends":        dict | {},
      "profile":       dict | None,
      "correlations":  list,
      "summary_stats": dict,
      "status":        dict,
      "filter":        dict,   # echoes the active filter so the template can display it
    }
    """
    from datetime import datetime

    # -- 1. Start from all completed records ------------------------------
    completed = [r for r in records if r.status == "completed"]

    # -- 2. Apply date window ---------------------------------------------
    if date_from:
        completed = [r for r in completed if r.completed_at >= date_from]
    if date_to:
        # include the full end day
        from datetime import timedelta
        end = date_to.replace(hour=23, minute=59, second=59)
        completed = [r for r in completed if r.completed_at <= end]

    # -- 3. Apply type whitelist ------------------------------------------
    if types_include:
        completed = [r for r in completed if r.assessment_type in types_include]

    # -- 4. Apply training mode -------------------------------------------
    _RECENT_N = 5
    if mode == "recent":
        # Keep only the N most-recent records per type
        from collections import defaultdict
        by_type_tmp: dict[str, list] = defaultdict(list)
        for r in sorted(completed, key=lambda x: x.completed_at, reverse=True):
            by_type_tmp[r.assessment_type].append(r)
        completed = [r for entries in by_type_tmp.values() for r in entries[:_RECENT_N]]
    elif mode == "trend":
        # Keep only types that have ≥2 records (makes trend analysis the focus)
        from collections import Counter
        type_counts = Counter(r.assessment_type for r in completed)
        completed = [r for r in completed if type_counts[r.assessment_type] >= _MIN_FOR_TREND]

    # -- 5. Build the filter summary to pass back to the template ---------
    filter_info = {
        "date_from":      date_from.strftime("%Y-%m-%d") if date_from else None,
        "date_to":        date_to.strftime("%Y-%m-%d")   if date_to   else None,
        "types_include":  types_include or [],
        "mode":           mode,
        "is_active":      bool(date_from or date_to or types_include or mode != "all"),
        "n_after_filter": len(completed),
    }

    # -- 6. Guard: no data after filtering --------------------------------
    if not completed:
        return {
            "available":   False,
            "min_records": _MIN_FOR_TREND,
            "trends":      {},
            "profile":     None,
            "correlations": [],
            "summary_stats": {},
            "status": _build_status(trends={}, profile=None, correlations=[]),
            "filter": filter_info,
            "trained_predictions": {},
        }

    feat = extract_features(completed)

    trends        = trend_prediction(feat)
    profile       = wellness_profile(feat)
    correlations  = cross_assessment_correlation(feat)

    # Summary stats for the ML panel header
    all_pct  = feat["all_pct"]
    avg_score = round(sum(all_pct) / len(all_pct)) if all_pct else 0

    # Overall wellness score: weighted average favouring eq/learning (higher=better)
    # and inverting clinical screens (lower=better)
    wellness_score = _compute_wellness_score(feat["type_vector"])

    return {
        "available":    True,
        "min_records":  _MIN_FOR_TREND,
        "trends":       trends,
        "profile":      profile,
        "correlations": correlations,
        "summary_stats": {
            "avg_score":      avg_score,
            "wellness_score": wellness_score,
            "n_completed":    len(completed),
            "n_types":        len(feat["all_types_taken"]),
        },
        "status": _build_status(trends=trends, profile=profile, correlations=correlations),
        "filter": filter_info,
        "trained_predictions": {},   # populated by progress route after load_and_predict()
    }


# -----------------------------------------------------------------------------
# Private helpers
# -----------------------------------------------------------------------------

# The three sub-analyses reported in the status block, in display order.
# (key, human label)
_STATUS_CHECKS: list[tuple[str, str]] = [
    ("trends",       "Trend Predictions"),
    ("profile",      "Wellness Archetype"),
    ("correlations", "Cross-Assessment Patterns"),
]


def _build_status(
    trends: dict[str, Any] | None,
    profile: dict[str, Any] | None,
    correlations: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """
    Summarise which ML sub-analyses produced output.

    Returns
    -------
    {
      "state":        "live" | "partial" | "locked",
      "label":        str,            # short human label for the badge
      "badge_class":  str,            # success | warning | secondary
      "active_count": int,            # how many sub-analyses unlocked
      "total_count":  int,            # always 3
      "checks":       [ {key, label, unlocked: bool}, ... ]
    }
    """
    unlocked = {
        "trends":       bool(trends),
        "profile":      profile is not None,
        "correlations": bool(correlations),
    }
    active_count = sum(1 for v in unlocked.values() if v)
    total_count   = len(_STATUS_CHECKS)

    if active_count == total_count:
        state, label, badge = "live", "Live", "success"
    elif active_count == 0:
        state, label, badge = "locked", "Locked", "gray"
    else:
        state, label, badge = "partial", "Partial", "warning"

    checks = [
        {"key": k, "label": lbl, "unlocked": unlocked[k]}
        for k, lbl in _STATUS_CHECKS
    ]

    return {
        "state":        state,
        "label":        label,
        "badge_class":  badge,
        "active_count": active_count,
        "total_count":  total_count,
        "checks":       checks,
    }


def _align_records(entries_a: list, entries_b: list) -> tuple[list, list]:
    """
    Align two entry lists for correlation.
    Strategy: try date-based alignment (same calendar day); fall back to
    positional alignment (zip up to min length).
    """
    from datetime import datetime, timezone

    def day_key(ts: float) -> str:
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")

    map_a = {day_key(e["ts"]): e["pct"] for e in entries_a}
    map_b = {day_key(e["ts"]): e["pct"] for e in entries_b}
    shared = sorted(set(map_a) & set(map_b))

    if len(shared) >= _MIN_FOR_CORRELATION:
        return [map_a[d] for d in shared], [map_b[d] for d in shared]

    # Fallback: positional
    min_n = min(len(entries_a), len(entries_b))
    return (
        [entries_a[i]["pct"] for i in range(min_n)],
        [entries_b[i]["pct"] for i in range(min_n)],
    )


def _correlation_insight(ta: str, tb: str, r: float, strength: str) -> str:
    """Generate a plain-English insight sentence for a correlation pair."""
    la = TYPE_LABELS.get(ta, ta)
    lb = TYPE_LABELS.get(tb, tb)

    if r > 0:
        if strength == "strong":
            return (f"Your {la} and {lb} scores tend to rise and fall together — "
                    "improving one often coincides with improvement in the other.")
        elif strength == "moderate":
            return (f"There is a moderate link between your {la} and {lb} scores. "
                    "They often move in the same direction across sessions.")
        else:
            return f"A weak positive trend exists between your {la} and {lb} scores."
    else:
        if strength == "strong":
            return (f"Your {la} and {lb} scores move in opposite directions — "
                    "when one is high the other tends to be low.")
        elif strength == "moderate":
            return (f"There is a moderate inverse link between {la} and {lb}: "
                    "higher scores in one tend to accompany lower scores in the other.")
        else:
            return f"A weak inverse trend exists between your {la} and {lb} scores."


def _compute_wellness_score(type_vector: dict[str, float]) -> int:
    """
    Compute a composite wellness score 0–100.
    Clinical screens (lower = healthier): invert the contribution.
    Positive screens (higher = better): use directly.
    """
    if not type_vector:
        return 0

    lower_is_better = {"adhd", "anxiety", "depression", "stress", "asd"}
    contributions = []
    for t, v in type_vector.items():
        if t in lower_is_better:
            contributions.append(1.0 - v)   # invert: 0 score -> 1.0 wellness
        else:
            contributions.append(v)          # eq, learning: higher = better
    return round((sum(contributions) / len(contributions)) * 100)


def _type_icon(a_type: str) -> str:
    return {
        "adhd":       "",
        "anxiety":    "",
        "depression": "",
        "stress":     "",
        "learning":   "",
        "eq":         "",
        "asd":        "",
    }.get(a_type, "")


# -----------------------------------------------------------------------------
# TRADITIONAL ML ENGINE
# -----------------------------------------------------------------------------
#
# Design
# ------
# Target variable : band class (ordinal)
#                   0 = low / minimal / developing
#                   1 = moderate / requires attention
#                   2 = high / severe / strong
#
# Feature vector  : (per record)
#   [q1_score, q2_score, … qN_score,   <- numeric option scores from answers_json
#    days_since_first,                  <- time-series position
#    session_number]                    <- ordinal session index
#
#   For CSV-imported records (answers_json == "{}") we synthesise per-question
#   scores by distributing pct_score evenly across questions.
#
# Algorithm selection (auto, per type):
#   n ≥ 20  ->  GradientBoostingClassifier  (best accuracy)
#   n ≥  8  ->  RandomForestClassifier      (robust with medium data)
#   n ≥  4  ->  LogisticRegression          (simple but needs few samples)
#   n <  4  ->  no model trained (use heuristic fallback)
#
# Persistence: joblib.dump to  <instance_path>/ml_models/<uid>/<type>.pkl
#
# -----------------------------------------------------------------------------

import os
import joblib

try:
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.linear_model  import LogisticRegression
    from sklearn.model_selection import cross_val_score, StratifiedKFold
    from sklearn.preprocessing  import StandardScaler
    from sklearn.pipeline       import Pipeline
    _SK_FULL = True
except ImportError:
    _SK_FULL = False

# Max questions per assessment type (used for feature-vector length)
_TYPE_N_QUESTIONS: dict[str, int] = {
    "adhd":       10,
    "anxiety":    10,
    "depression": 10,
    "stress":     10,
    "learning":   10,
    "eq":         10,
    "asd":        20,
}

# Option score lookup tables (label -> int) per question type key
# Covers all freq4, freq5, rate5 and yn patterns used in the questionnaires
_OPTION_SCORES: dict[str, dict[str, int]] = {
    "freq4": {
        "not at all": 0, "several days": 1,
        "more than half the days": 2, "nearly every day": 3,
    },
    "freq5": {
        "never": 0, "rarely": 1, "sometimes": 2, "often": 3, "very often": 4,
    },
    "rate5": {
        "strongly disagree": 0, "disagree": 1, "neutral": 2,
        "agree": 3, "strongly agree": 4,
    },
    "yn": {"no": 0, "yes": 1},
}

# Band ordinal mapping — lower label strings -> int class
_BAND_TO_CLASS: dict[str, int] = {
    # clinical (lower = better)
    "low": 0,       "minimal": 0,  "developing": 0,
    "moderate": 1,  "requires attention": 1,
    "high": 2,      "severe": 2,   "strong": 2,
    "higher indication": 2,
    "lower indication": 0,
    # defaults
    "mild": 0,
}


def _band_class(band: str) -> int | None:
    """Convert a band string to ordinal class 0/1/2.  Returns None if unknown."""
    return _BAND_TO_CLASS.get(band.lower().strip())


def _model_dir(instance_path: str, user_id: int) -> str:
    d = os.path.join(instance_path, "ml_models", str(user_id))
    os.makedirs(d, exist_ok=True)
    return d


def _model_path(instance_path: str, user_id: int, a_type: str) -> str:
    return os.path.join(_model_dir(instance_path, user_id), f"{a_type}.pkl")


# -----------------------------------------------------------------------------
# Feature matrix builder
# -----------------------------------------------------------------------------

def build_feature_matrix(
    records: list,
    a_type: str,
    question_meta: "list[dict] | None" = None,
) -> "tuple[list[list[float]], list[int]] | tuple[None, None]":
    """
    Build (X, y) for supervised training from a user's completed records
    of a single assessment type.

    Parameters
    ----------
    records       : all AssessmentRecord ORM objects (any status)
    a_type        : assessment type key e.g. "anxiety"
    question_meta : list of question dicts from ASSESSMENT_TYPES[a_type]["questions"]
                    — used to look up option scores by label.
                    Pass None to skip per-question features (uses pct only).

    Returns
    -------
    (X, y) where
        X : list of float vectors
        y : list of int class labels (0 / 1 / 2)
    Returns (None, None) if fewer than 4 usable rows.
    """
    subset = sorted(
        [r for r in records if r.status == "completed"
         and r.assessment_type == a_type],
        key=lambda r: r.completed_at,
    )
    if len(subset) < 4:
        return None, None

    n_q = _TYPE_N_QUESTIONS.get(a_type, 10)

    # Build option->score lookup from question_meta if provided
    option_lookup: list[dict[str, int]] = []
    if question_meta:
        for q in question_meta:
            q_type = q.get("type", "freq5")
            # Build label->score from the question's own options list
            opts = {lbl.lower(): sc for lbl, sc in q.get("options", [])}
            if not opts:
                # fall back to generic mapping
                opts = _OPTION_SCORES.get(q_type, {})
            option_lookup.append(opts)

    X, y = [], []
    first_ts = subset[0].completed_at.timestamp()

    for idx, rec in enumerate(subset):
        # -- Band target --------------------------------------------------
        cls = _band_class(rec.band)
        if cls is None:
            # Derive class from pct_score when band label is unrecognised
            if rec.pct_score < 34:
                cls = 0
            elif rec.pct_score < 67:
                cls = 1
            else:
                cls = 2

        # -- Per-question features ----------------------------------------
        answers = rec.answers   # dict {"q1": "Often", "q2": "Never", …}
        q_feats: list[float] = []

        if answers and option_lookup:
            for qi in range(n_q):
                ans_label = answers.get(f"q{qi + 1}", "").lower().strip()
                score = option_lookup[qi].get(ans_label) if qi < len(option_lookup) else None
                if score is None:
                    # Synthesise from pct when answer missing / CSV import
                    score = round(rec.pct_score / 100 * max(option_lookup[qi].values(), default=4)) \
                            if option_lookup and qi < len(option_lookup) \
                            else rec.pct_score / 25   # scale 0-4
                q_feats.append(float(score))
        else:
            # No per-question data (CSV import) — distribute pct evenly
            avg_q = rec.pct_score / 100.0 * 4.0   # map 0-100 -> 0-4 scale
            q_feats = [avg_q] * n_q

        # -- Temporal features --------------------------------------------
        days_since_first = (rec.completed_at.timestamp() - first_ts) / 86_400.0
        session_num      = float(idx)

        X.append(q_feats + [days_since_first, session_num])
        y.append(cls)

    return X, y


# -----------------------------------------------------------------------------
# Model training
# -----------------------------------------------------------------------------

def train_models(
    records: list,
    user_id: int,
    instance_path: str,
    assessment_types_meta: "dict | None" = None,
) -> "dict[str, dict]":
    """
    Train one sklearn Pipeline per assessment type, persist with joblib,
    and return a summary dict.

    Parameters
    ----------
    records              : all AssessmentRecord ORM objects for this user
    user_id              : used for the storage path
    instance_path        : Flask app.instance_path
    assessment_types_meta: ASSESSMENT_TYPES dict from routes.py
                           — used to build accurate feature matrices.
                           Pass None to skip per-question features.

    Returns
    -------
    {
      "<type_key>": {
          "trained": bool,
          "algorithm": str,
          "n_samples": int,
          "n_features": int,
          "accuracy": float | None,   # cross-validated accuracy
          "model_path": str,
          "error": str | None,
      }
    }
    """
    if not _SK_FULL:
        return {t: {"trained": False, "error": "scikit-learn not available"}
                for t in _TYPE_N_QUESTIONS}

    results: dict[str, dict] = {}

    for a_type in _TYPE_N_QUESTIONS:
        q_meta = None
        if assessment_types_meta and a_type in assessment_types_meta:
            q_meta = assessment_types_meta[a_type].get("questions")

        X_raw, y_raw = build_feature_matrix(records, a_type, q_meta)

        if X_raw is None:
            results[a_type] = {
                "trained":    False,
                "algorithm":  "—",
                "n_samples":  sum(1 for r in records
                                  if r.status == "completed"
                                  and r.assessment_type == a_type),
                "n_features": 0,
                "accuracy":   None,
                "model_path": "",
                "error":      "Need at least 4 completed records of this type",
            }
            continue

        import numpy as np
        X = np.array(X_raw, dtype=float)
        y = np.array(y_raw, dtype=int)
        n_samples, n_features = X.shape

        # -- Algorithm selection ------------------------------------------
        if n_samples >= 20:
            clf  = GradientBoostingClassifier(
                n_estimators=100, max_depth=3, learning_rate=0.1,
                random_state=42)
            algo = "GradientBoosting"
        elif n_samples >= 8:
            clf  = RandomForestClassifier(
                n_estimators=100, max_depth=None,
                random_state=42)
            algo = "RandomForest"
        else:
            clf  = LogisticRegression(max_iter=500, random_state=42)
            algo = "LogisticRegression"

        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("clf",    clf),
        ])

        # -- Cross-validated accuracy -------------------------------------
        cv_acc: float | None = None
        try:
            n_classes = len(set(y))
            if n_classes >= 2:
                n_splits = min(5, n_samples // n_classes)
                if n_splits >= 2:
                    cv = StratifiedKFold(n_splits=n_splits, shuffle=True,
                                         random_state=42)
                    scores = cross_val_score(pipeline, X, y, cv=cv,
                                             scoring="accuracy")
                    cv_acc = float(scores.mean())
        except Exception:
            cv_acc = None

        # -- Train on full dataset ----------------------------------------
        try:
            pipeline.fit(X, y)
        except Exception as e:
            results[a_type] = {
                "trained": False, "error": str(e),
                "algorithm": algo, "n_samples": n_samples,
                "n_features": n_features, "accuracy": None,
                "model_path": "",
            }
            continue

        # -- Persist ------------------------------------------------------
        path = _model_path(instance_path, user_id, a_type)
        try:
            joblib.dump({"pipeline": pipeline, "a_type": a_type,
                         "algo": algo, "n_samples": n_samples,
                         "n_features": n_features}, path)
        except Exception as e:
            results[a_type] = {
                "trained": False, "error": f"Could not save model: {e}",
                "algorithm": algo, "n_samples": n_samples,
                "n_features": n_features, "accuracy": cv_acc,
                "model_path": "",
            }
            continue

        results[a_type] = {
            "trained":    True,
            "algorithm":  algo,
            "n_samples":  n_samples,
            "n_features": n_features,
            "accuracy":   cv_acc,
            "model_path": path,
            "error":      None,
        }

    return results


# -----------------------------------------------------------------------------
# Inference — load persisted model and predict next band
# -----------------------------------------------------------------------------

def load_and_predict(
    records: list,
    user_id: int,
    instance_path: str,
    assessment_types_meta: "dict | None" = None,
) -> "dict[str, dict]":
    """
    For each assessment type that has a saved model, build a feature vector
    from the user's latest record and predict the likely next band.

    Returns
    -------
    {
      "<type_key>": {
          "predicted_band":       str,    # e.g. "Moderate"
          "predicted_band_class": int,    # 0 / 1 / 2
          "confidence_pct":       int,    # max class probability × 100
          "probabilities":        [float, float, float],  # P(low), P(mod), P(high)
          "algorithm":            str,
          "n_samples":            int,
      }
    }
    """
    _CLASS_TO_BAND = {0: "Low / Minimal", 1: "Moderate", 2: "High / Severe"}

    out: dict[str, dict] = {}

    for a_type in _TYPE_N_QUESTIONS:
        path = _model_path(instance_path, user_id, a_type)
        if not os.path.exists(path):
            continue

        try:
            saved = joblib.load(path)
        except Exception:
            continue

        pipeline  = saved["pipeline"]
        n_samples = saved.get("n_samples", 0)
        algo      = saved.get("algo", "?")

        q_meta = None
        if assessment_types_meta and a_type in assessment_types_meta:
            q_meta = assessment_types_meta[a_type].get("questions")

        X_raw, _ = build_feature_matrix(records, a_type, q_meta)
        if X_raw is None:
            continue

        import numpy as np
        X = np.array(X_raw, dtype=float)

        # Use the full history as context; predict using the last row
        # (the most recent session's features)
        try:
            proba = pipeline.predict_proba(X[-1:])  # shape (1, n_classes)
            proba_list = proba[0].tolist()
            # Pad to 3 classes if model only saw 2
            while len(proba_list) < 3:
                proba_list.append(0.0)
            pred_cls  = int(np.argmax(proba_list))
            conf_pct  = int(round(max(proba_list) * 100))
        except Exception:
            continue

        out[a_type] = {
            "predicted_band":       _CLASS_TO_BAND[pred_cls],
            "predicted_band_class": pred_cls,
            "confidence_pct":       conf_pct,
            "probabilities":        [round(p, 3) for p in proba_list[:3]],
            "algorithm":            algo,
            "n_samples":            n_samples,
        }

    return out


# -----------------------------------------------------------------------------
# Model status (what's currently on disk for this user)
# -----------------------------------------------------------------------------

def get_model_status(
    user_id: int,
    instance_path: str,
) -> "dict[str, dict]":
    """
    Return a summary of which model files exist on disk for this user,
    combined with metadata stored in the MLModel DB table.

    Returns
    -------
    {
      "<type_key>": {
          "has_model": bool,
          "algorithm": str,
          "n_samples": int,
          "accuracy_pct": str,
          "trained_at": str | None,
          "trained_ago": str | None,
          "label": str,
      }
    }
    """
    status: dict[str, dict] = {}
    for a_type, label in TYPE_LABELS.items():
        path  = _model_path(instance_path, user_id, a_type)
        exists = os.path.exists(path)
        status[a_type] = {
            "has_model":   exists,
            "algorithm":   "—",
            "n_samples":   0,
            "accuracy_pct": "—",
            "trained_at":  None,
            "trained_ago": None,
            "label":       label,
        }
        if exists:
            try:
                saved = joblib.load(path)
                status[a_type]["algorithm"] = saved.get("algo", "?")
                status[a_type]["n_samples"] = saved.get("n_samples", 0)
            except Exception:
                pass

    return status
