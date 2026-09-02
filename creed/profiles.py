"""Creed definitions and deterministic managed-block rendering."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Profile:
    """A named AI-dependency creed."""

    name: str
    summary: str
    directives: tuple[str, ...]
    configuration: dict[str, bool]


AI_NATIVE = Profile(
    name="ai-native",
    summary="AI is the product's foundation in build and runtime.",
    directives=(
        "AI is the foundation of this product. Use it freely in build and runtime.",
        "The product's core value comes from model capabilities.",
        "No crystallization requirement. AI dependency is expected and desired.",
    ),
    configuration={
        "ai_allowed_in_build": True,
        "ai_allowed_in_runtime": True,
        "crystallization_required": False,
        "labeled_gaps_required": False,
        "deterministic_fallback_required": False,
        "ai_may_establish_truth": True,
    },
)

AI_AUGMENTED = Profile(
    name="ai-augmented",
    summary="AI assists the build; the shipped product is deterministic.",
    directives=(
        "AI may be used to build this product, but the shipped product is deterministic.",
        "The runtime must not depend on AI for core functionality.",
        "AI-generated code must pass human or deterministic review before landing.",
        "No AI in the production dependency chain.",
    ),
    configuration={
        "ai_allowed_in_build": True,
        "ai_allowed_in_runtime": False,
        "crystallization_required": False,
        "labeled_gaps_required": False,
        "deterministic_fallback_required": False,
        "ai_may_establish_truth": False,
    },
)

AI_ESCAPE_HATCH = Profile(
    name="ai-escape-hatch",
    summary="Determinism is the default and AI is an explicit fallback.",
    directives=(
        "The product is deterministic by default. AI is an escape hatch, not a foundation.",
        "AI is invoked only when deterministic paths cannot handle a situation.",
        "AI may explain deterministic decisions but must never establish truth.",
        "Where determinism cannot reach, surface an explicit labeled gap — never guess.",
    ),
    configuration={
        "ai_allowed_in_build": True,
        "ai_allowed_in_runtime": True,
        "crystallization_required": False,
        "labeled_gaps_required": True,
        "deterministic_fallback_required": False,
        "ai_may_establish_truth": False,
    },
)

AI_SELF_WEANING = Profile(
    name="ai-self-weaning",
    summary="AI use is captured and converted into durable deterministic rules over time.",
    directives=(
        "The product is deterministic by default. AI is an escape hatch, not a foundation.",
        "AI may explain deterministic decisions but must never establish truth.",
        "Every AI intervention must be captured and crystallized into a deterministic rule, pattern, or cached decision.",
        "The system's goal is to need AI less over time. Each AI invocation is a gap to be permanently closed.",
        "Deterministic fallbacks must exist for every AI-invoked path.",
        "Where determinism cannot reach, surface an explicit labeled gap — never guess.",
    ),
    configuration={
        "ai_allowed_in_build": True,
        "ai_allowed_in_runtime": True,
        "crystallization_required": True,
        "labeled_gaps_required": True,
        "deterministic_fallback_required": True,
        "ai_may_establish_truth": False,
    },
)

AI_FREE = Profile(
    name="ai-free",
    summary="No AI is used in build or runtime.",
    directives=(
        "No AI anywhere — not in build, not in runtime.",
        "All logic is deterministic, human-authored, and verifiable.",
        "If a problem cannot be solved deterministically, it is a labeled gap, not an AI task.",
    ),
    configuration={
        "ai_allowed_in_build": False,
        "ai_allowed_in_runtime": False,
        "crystallization_required": False,
        "labeled_gaps_required": True,
        "deterministic_fallback_required": False,
        "ai_may_establish_truth": False,
    },
)


PROFILES: dict[str, Profile] = {
    profile.name: profile
    for profile in (AI_NATIVE, AI_AUGMENTED, AI_ESCAPE_HATCH, AI_SELF_WEANING, AI_FREE)
}

CONFIGURATION_FIELDS = (
    "ai_allowed_in_build",
    "ai_allowed_in_runtime",
    "crystallization_required",
    "labeled_gaps_required",
    "deterministic_fallback_required",
    "ai_may_establish_truth",
)


def render_block(name: str) -> str:
    """Render the complete managed block for a named creed."""

    try:
        profile = PROFILES[name]
    except KeyError as error:
        known_names = ", ".join(PROFILES)
        raise ValueError(f"Unknown creed: {name}. Available creeds: {known_names}.") from error

    lines = [
        "<!-- creed:managed:start -->",
        "## AI-Dependency Creed (Managed)",
        "",
        f"- This repository follows the `{profile.name}` creed.",
        *[f"- {directive}" for directive in profile.directives],
        f"- `{profile.name}` was applied with `creed apply`; do not edit this block by hand.",
        "<!-- creed:managed:end -->",
    ]
    return "\n".join(lines) + "\n"
