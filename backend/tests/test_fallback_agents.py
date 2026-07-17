from app.agents.fallback import expand_mixture_fallback, expand_root_fallback
from app.domain.models import MixtureFeature, RootFeature


def test_root_has_children():
    root = RootFeature(
        id="c:root:Sun",
        chart_id="c",
        point_name="Sun",
        role="drive",
        role_label="Drive",
        style="structure",
        style_label="Structure",
        element="earth",
        quality="cardinal",
        weight=2.0,
    )
    agent = expand_root_fallback(root)
    assert agent.tier == "captain"
    assert len(agent.children) >= 1
    assert agent.attributes.hp > 0


def test_mixture_hybrid():
    mix = MixtureFeature(
        id="c:mix",
        chart_id="c",
        parent_ids=["a", "b"],
        parent_roles=["drive", "dream"],
        parent_styles=["structure", "absorb"],
        link="harmony",
        strength=0.85,
        aspect="sextile",
        weight=1.2,
    )
    agent = expand_mixture_fallback(mix)
    assert agent.tier == "hybrid"
    assert "structure" in agent.name.lower() or "Hybrid" in agent.name or "Harmony" in agent.name
