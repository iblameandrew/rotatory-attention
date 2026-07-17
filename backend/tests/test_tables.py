from app.domain.tables import link_for_aspect, role_for_point, style_for_sign


def test_role_sun():
    r = role_for_point("Sun")
    assert r["role"] == "drive"
    assert r["weight"] >= 1.5


def test_style_capricorn():
    s = style_for_sign("Cap")
    assert s["style"] == "structure"
    assert s["element"] == "earth"


def test_style_pisces():
    s = style_for_sign("Pisces")
    assert s["style"] == "absorb"


def test_sextile_harmony():
    m = link_for_aspect("sextile")
    assert m["link"] == "harmony"
    assert m["polarity"] > 0
