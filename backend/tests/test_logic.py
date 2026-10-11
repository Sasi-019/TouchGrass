"""Pure-logic tests: configuration, planning heuristics and validation."""

from app.config import find_problems, load_settings, normalize_database_url
from app.agent_graph import (
    heuristic_plan,
    parse_available_minutes,
    validate_candidate,
)
from app.real_world_tools import summarize_weather


# ---------------------------------------------------------------- config

def _env(**overrides):
    base = {
        "DATABASE_URL": "postgresql://u:p@localhost/db",
        "JWT_SECRET": "a" * 48,
        "GROQ_API_KEY": "key",
    }
    base.update(overrides)
    return base


def test_valid_config_has_no_problems():
    assert find_problems(load_settings(_env())) == []


def test_missing_values_are_all_reported_at_once():
    problems = find_problems(load_settings({}))
    text = " ".join(problems)
    assert "DATABASE_URL" in text
    assert "JWT_SECRET" in text
    assert "GROQ_API_KEY" in text


def test_placeholder_secret_is_rejected():
    problems = find_problems(load_settings(_env(JWT_SECRET="change-me")))
    assert any("JWT_SECRET" in p for p in problems)


def test_production_requires_real_cors_and_long_secret():
    settings = load_settings(
        _env(APP_ENV="production", JWT_SECRET="short", CORS_ORIGINS="*")
    )
    problems = " ".join(find_problems(settings))
    assert "32 characters" in problems
    assert "CORS_ORIGINS" in problems


def test_postgres_scheme_is_normalised():
    assert normalize_database_url("postgres://a/b").startswith("postgresql://")


# ------------------------------------------------------------- planning

def test_parse_minutes():
    assert parse_available_minutes("I have 30 minutes") == 30
    assert parse_available_minutes("got 2 hours free") == 120
    assert parse_available_minutes("half an hour") == 30
    assert parse_available_minutes("I have an hour") == 60
    assert parse_available_minutes("give me something fun") is None


def test_heuristic_intents():
    assert heuristic_plan("hello", False)["intent"] == "chat"
    assert heuristic_plan("give me something else", False)["intent"] == "regenerate"
    assert heuristic_plan("find a park near me", True)["intent"] == "places"
    assert heuristic_plan("what do you know about me", False)["intent"] == "question"
    assert heuristic_plan("I'm tired", False)["intent"] == "adapt"
    assert heuristic_plan("surprise me", False)["intent"] == "activity"


def test_whole_word_matching():
    # "train" must not trigger rain/weather, "parkour" must not mean a park.
    assert heuristic_plan("I want to train", False)["tools"] == []
    assert heuristic_plan("teach me parkour", False)["intent"] != "places"


def test_places_without_location_asks_for_location():
    plan = heuristic_plan("find a cafe nearby", has_coordinates=False)
    assert plan["needs_location"] is True


def test_weather_summary_flags():
    stormy = summarize_weather(
        {"weather_code": 95, "temperature_2m": 20, "apparent_temperature": 20,
         "wind_speed_10m": 10, "precipitation": 3},
        {"precipitation_probability_max": [90]},
    )
    assert stormy["outdoor_ok"] is False and stormy["is_wet"] is True

    nice = summarize_weather(
        {"weather_code": 1, "temperature_2m": 24, "apparent_temperature": 24,
         "wind_speed_10m": 8, "precipitation": 0},
        {"precipitation_probability_max": [5]},
    )
    assert nice["outdoor_ok"] is True


# ----------------------------------------------------------- validation

def _validate(raw, **overrides):
    kwargs = dict(
        plan={"available_minutes": None, "energy": None, "setting": None},
        profile={"dislikes": []},
        history=[],
        environment={"part_of_day": "afternoon"},
        tool_results=[],
        rejected=[],
    )
    kwargs.update(overrides)
    return validate_candidate(raw, **kwargs)


GOOD = {
    "title": "Nature Texture Hunt",
    "description": "Walk slowly and look for five interesting natural textures.",
    "category": "outdoors", "duration_minutes": 30,
    "location_type": "outdoors", "screen_use": "low",
    "difficulty": "easy", "related_interests": ["photography"],
    "place": None, "reason": "You like photography.",
}


def test_good_activity_passes():
    cleaned, problems, _ = _validate(GOOD)
    assert problems == []
    assert cleaned["title"] == "Nature Texture Hunt"


def test_too_long_for_available_time_is_rejected():
    _, problems, _ = _validate(
        {**GOOD, "duration_minutes": 120},
        plan={"available_minutes": 25, "energy": None, "setting": None},
    )
    assert any("25" in p for p in problems)


def test_bad_weather_rejects_outdoor_ideas():
    _, problems, _ = _validate(
        GOOD,
        tool_results=[{"tool": "weather", "ok": True, "outdoor_ok": False,
                       "summary": "thunderstorm"}],
    )
    assert any("weather" in p.lower() for p in problems)


def test_repeated_activity_is_rejected():
    _, problems, _ = _validate(
        {**GOOD, "title": "Nature texture hunt!"},
        history=[{"title": "Nature Texture Hunt"}],
    )
    assert any("similar" in p for p in problems)


def test_dislikes_are_respected_but_negations_are_not_false_positives():
    profile = {"dislikes": ["crowded places"]}

    _, problems, _ = _validate(
        {**GOOD, "description": "Head to a crowded places market."}, profile=profile
    )
    assert problems

    _, problems, _ = _validate(
        {**GOOD, "description": "Stay away from crowded places and find a quiet bench."},
        profile=profile,
    )
    assert problems == []


def test_screen_heavy_activity_is_rejected():
    _, problems, _ = _validate(
        {**GOOD, "title": "Scroll challenge",
         "description": "Scroll social media for new ideas."}
    )
    assert problems


def test_low_energy_blocks_hard_activities():
    _, problems, _ = _validate(
        {**GOOD, "difficulty": "challenging"},
        plan={"available_minutes": None, "energy": "low", "setting": None},
    )
    assert problems


def test_invented_places_are_removed_real_ones_kept():
    results = [{"tool": "nearby_places", "ok": True,
                "places": [{"name": "Lakeside Park", "type": "park", "distance_m": 400}]}]

    cleaned, _, notes = _validate(
        {**GOOD, "place": {"name": "Imaginary Garden"}}, tool_results=results
    )
    assert cleaned["place"] is None and notes

    cleaned, _, _ = _validate(
        {**GOOD, "place": {"name": "lakeside park"}}, tool_results=results
    )
    assert cleaned["place"]["name"] == "Lakeside Park"


def test_legacy_categories_are_mapped():
    cleaned, _, _ = _validate({**GOOD, "category": "explore"})
    assert cleaned["category"] == "exploration"
