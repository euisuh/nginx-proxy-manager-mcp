from copy import deepcopy

import pytest

from nginx_proxy_manager_mcp.tools.filters import filter_items


def test_defaults_preserve_original_list():
    items = [{"id": 1, "extra": {"nested": True}}, {}]
    assert filter_items(items) is items


@pytest.mark.parametrize("items", [[], [{"id": 1}], [{"domain_names": []}]])
def test_domain_without_matching_names(items):
    assert filter_items(items, domain="example") == []


def test_domain_matches_any_name_case_insensitively():
    items = [{"domain_names": ["other.org", "App.Example.com"]}, {"domain_names": ["b.org"]}]
    assert filter_items(items, domain="EXAMPLE") == items[:1]
    assert filter_items(items, domain="") == items


@pytest.mark.parametrize("enabled, expected_ids", [(True, [1, 3]), (False, [2, 4])])
def test_enabled_uses_boolean_value(enabled, expected_ids):
    items = [{"id": i, "enabled": value} for i, value in enumerate((1, 0, True, False), 1)]
    assert [item["id"] for item in filter_items(items, enabled=enabled)] == expected_ids


def test_filters_combine_before_compaction_without_mutation():
    items = [
        {"enabled": 1, "domain_names": ["App.Example.com"], "id": 1, "extra": {"nested": True}},
        {"enabled": 0, "domain_names": ["example.com"], "id": 2},
        {"enabled": 1, "domain_names": ["b.org"], "id": 3},
    ]
    original = deepcopy(items)
    result = filter_items(
        items,
        domain="example",
        enabled=True,
        compact=True,
        compact_keys=("id", "missing", "domain_names"),
    )
    assert result == [{"id": 1, "domain_names": ["App.Example.com"]}]
    assert list(result[0]) == ["id", "domain_names"]
    assert items == original


def test_compact_skips_absent_keys():
    assert filter_items([{}, {"extra": 1}], compact=True, compact_keys=("id",)) == [{}, {}]
