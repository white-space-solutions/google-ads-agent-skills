import os

import pytest

from gads import WriteBlocked, blocks, guard_write, norm, role_of


def test_phrase_blocks_words_in_order_only():
    assert blocks("for rent", "PHRASE", "houses for rent near me")
    assert not blocks("for rent", "PHRASE", "rent for house")
    assert not blocks("rent", "PHRASE", "rental property")          # no close variants


def test_exact_and_broad():
    assert blocks("sell", "EXACT", "Sell")
    assert not blocks("sell", "EXACT", "sell house")
    assert blocks("house worth", "BROAD", "what is my house worth")
    assert blocks("worth house", "BROAD", "what is my house worth")


def test_norm_strips_punctuation_and_case():
    assert norm("  Sell   My House\u2014FAST! ") == "sell my house fast"
    assert norm("Sotheby’s") == "sotheby's"


CFG = {"campaign_roles": {"generic": ["Sell House"], "competitors": ["Competitors"], "brand": ["Brand"]},
       "safety": {"allowed_customer_ids": ["1234567890"], "max_ops_per_run": 10}}


def test_role_of_prefix_case_insensitive():
    assert role_of(CFG, "sell house fast - search") == "generic"
    assert role_of(CFG, "Competitors (Imp Share)") == "competitors"
    assert role_of(CFG, "PMax") == "other"


def test_guard_refuses_other_accounts():
    with pytest.raises(WriteBlocked):
        guard_write(CFG, "999-999-9999", 1, executing=False)


def test_guard_refuses_over_cap():
    with pytest.raises(WriteBlocked):
        guard_write(CFG, "1234567890", 11, executing=False)


def test_guard_needs_kill_switch_to_execute(monkeypatch):
    monkeypatch.delenv("APPLY_ENABLED", raising=False)
    guard_write(CFG, "123-456-7890", 5, executing=False)        # dry run fine
    with pytest.raises(WriteBlocked):
        guard_write(CFG, "1234567890", 5, executing=True)
    monkeypatch.setenv("APPLY_ENABLED", "1")
    guard_write(CFG, "1234567890", 5, executing=True)
