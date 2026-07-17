from app.match.relations import score_pair_from_aspects


def test_conflict_from_hard_aspects():
    aspects = [
        {"p1_name": "Sun", "p2_name": "Mars", "aspect": "square", "orbit": 1.0},
        {"p1_name": "Moon", "p2_name": "Saturn", "aspect": "opposition", "orbit": 2.0},
    ]
    rel = score_pair_from_aspects(aspects, "A", "B", "a", "b")
    assert rel.stance == "conflict"
    assert rel.score < 0


def test_affiliation_from_soft_aspects():
    aspects = [
        {"p1_name": "Sun", "p2_name": "Jupiter", "aspect": "trine", "orbit": 1.0},
        {"p1_name": "Venus", "p2_name": "Moon", "aspect": "sextile", "orbit": 1.5},
    ]
    rel = score_pair_from_aspects(aspects, "A", "B", "a", "b")
    assert rel.stance == "affiliation"
    assert rel.score > 0
