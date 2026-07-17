from app.domain.models import RootFeature
from app.match.planet_allocation import allocate_units_per_root, hierarchy_weight


def _r(name: str, abs_pos: float | None = None, weight: float = 1.0) -> RootFeature:
    return RootFeature(
        id=f"c:root:{name}",
        chart_id="c",
        point_name=name,
        role="x",
        role_label="X",
        style="y",
        style_label="Y",
        weight=weight,
        abs_pos=abs_pos,
    )


def test_flat_all_equal():
    roots = [_r("Sun", 10), _r("Mars", 100), _r("Pluto", 200)]
    alloc = allocate_units_per_root(roots, 10, mode="flat")
    assert alloc["c:root:Sun"] == 10
    assert alloc["c:root:Mars"] == 10
    assert alloc["c:root:Pluto"] == 10


def test_hierarchical_sun_asc_peak():
    roots = [
        _r("Sun", 0),
        _r("Ascendant", 90),
        _r("Mercury", 5),  # near sun
        _r("Pluto", 180),  # far
    ]
    peak = 20
    alloc = allocate_units_per_root(roots, peak, mode="hierarchical")
    assert alloc["c:root:Sun"] == peak
    assert alloc["c:root:Ascendant"] == peak
    assert alloc["c:root:Mercury"] >= alloc["c:root:Pluto"]
    assert alloc["c:root:Pluto"] >= 1
    assert alloc["c:root:Mercury"] < peak or alloc["c:root:Mercury"] == peak


def test_max_100():
    roots = [_r("Sun", 0)]
    alloc = allocate_units_per_root(roots, 100, mode="flat")
    assert alloc["c:root:Sun"] == 100


def test_hierarchy_weight_sun_top():
    sun = _r("Sun", 0)
    pluto = _r("Pluto", 180)
    assert hierarchy_weight(sun, 0) >= hierarchy_weight(pluto, 0)
