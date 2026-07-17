from app.domain.tables import faction_color
from app.match.service import _map_size_for_factions, _units_per_faction_cap


def test_faction_colors_unique_for_many():
    colors = [faction_color(i) for i in range(48)]
    assert all(c.startswith("#") and len(c) == 7 for c in colors)
    # Most should be unique across a large set
    assert len(set(colors)) >= 40


def test_map_grows_with_factions():
    assert _map_size_for_factions(2) == [64, 64]
    assert _map_size_for_factions(10)[0] > 64
    assert _map_size_for_factions(100)[0] <= 160


def test_units_cap_scales_with_planets():
    cap = _units_per_faction_cap(
        planned_root_units=30,
        mixture_count=4,
        faction_count=2,
        explicit_max=None,
        peak_per_planet=3,
    )
    assert cap >= 30
    cap_small = _units_per_faction_cap(
        planned_root_units=5,
        mixture_count=0,
        faction_count=2,
        explicit_max=None,
        peak_per_planet=1,
    )
    assert cap_small >= 5
