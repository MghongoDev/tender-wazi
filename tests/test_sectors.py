import re

import yaml

from tender_wazi.sectors import classify, load_rules

RULES_PATH = "config/sector_rules.yaml"


def test_load_rules_reads_the_version_and_compiles_the_terms():
    version, rules = load_rules(RULES_PATH)

    assert version == "2026-11-a"
    assert "ict_data_tech" in rules
    include, exclude = rules["ict_data_tech"]
    assert include and all(isinstance(rx, re.Pattern) for rx in include)
    assert all(isinstance(rx, re.Pattern) for rx in exclude)


def test_the_rules_file_is_well_formed():
    cfg = yaml.safe_load(open(RULES_PATH, encoding="utf-8"))

    assert isinstance(cfg["version"], str) and cfg["version"]
    for sector, spec in cfg["sectors"].items():
        assert isinstance(spec["any"], list), sector
        assert all(isinstance(term, str) and term for term in spec["any"]), sector


def test_classify_matches_a_tech_title():
    _, rules = load_rules(RULES_PATH)

    sectors, matched = classify("Supply of laptops and software licences", rules)

    assert sectors == ["ict_data_tech"]
    assert any("laptop" in term.lower() for term in matched)


def test_classify_matches_several_sectors():
    _, rules = load_rules(RULES_PATH)

    sectors, _ = classify("Supply of laptops for school education", rules)

    assert "ict_data_tech" in sectors
    assert "education_training" in sectors


def test_classify_falls_back_to_other():
    _, rules = load_rules(RULES_PATH)

    sectors, matched = classify("A thing with no sector terms", rules)

    assert sectors == ["other"]
    assert matched == []


def test_classify_matches_on_whole_words_only():
    _, rules = load_rules(RULES_PATH)

    sectors, _ = classify("A powerful engine and a healthy outcome", rules)

    assert "energy_utilities" not in sectors
    assert "health_medical" not in sectors


def test_classify_is_case_insensitive():
    _, rules = load_rules(RULES_PATH)

    sectors, _ = classify("SUPPLY OF LAPTOPS", rules)

    assert sectors == ["ict_data_tech"]


def test_an_excluding_term_blocks_a_match():
    rules = {
        "ict_data_tech": (
            [re.compile(r"\b(?:ICT)\b", re.I)],
            [re.compile(r"\b(?:ICT security)\b", re.I)],
        )
    }

    sectors, _ = classify("ICT security briefing", rules)

    assert sectors == ["other"]
