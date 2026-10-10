import itertools
import re

import pytest

from automata import build_dfa, build_min_dfa, convert
from automata.dfa import DEAD, simulate

REGEXES = [
    "a", "ab", "a|b", "a*", "a+", "ab*", "(ab)*", "(ab)+", "a*b+", "(a*)*",
    "a|b*", "(a|b)*abb", "(a|b)+c", "a+b+|c", "(a+)+", "((a|b)c)*", "a(b|c)*d",
]


def all_strings(alphabet, max_len):
    for n in range(max_len + 1):
        for t in itertools.product(alphabet, repeat=n):
            yield "".join(t)


@pytest.mark.parametrize("regex", REGEXES)
@pytest.mark.parametrize("dead", [True, False])
def test_matches_python_re(regex, dead):
    dfa = build_dfa(regex, dead_state=dead)
    for s in all_strings("abcd", 6):
        expected = bool(re.fullmatch(regex, s))
        assert simulate(dfa, s)["accepted"] == expected, (regex, s)


def test_known_dfa_size():
    # classic textbook example: subset construction on Thompson's NFA gives
    # 5 states (4 after minimization) and needs no dead state
    dfa = build_dfa("(a|b)*abb")
    assert len(dfa.states) == 5
    assert DEAD not in dfa.states
    assert len(dfa.accepting) == 1


def test_dead_state_added_when_needed():
    assert DEAD in build_dfa("ab").states
    assert DEAD not in build_dfa("ab", dead_state=False).states


def test_empty_string_and_foreign_symbol():
    dfa = build_dfa("a*")
    assert simulate(dfa, "")["accepted"] is True
    r = simulate(dfa, "ax")
    assert r["accepted"] is False and "not in the alphabet" in r["reason"]


def test_trace_path():
    r = simulate(build_dfa("(a|b)*abb"), "abb")
    assert r["accepted"] is True
    assert [p["symbol"] for p in r["path"]] == ["a", "b", "b"]


def test_convert_output_shape():
    out = convert("(a|b)*abb", ["abb", "ab"])
    assert out["postfix"] == "ab|*a.b.b."
    assert [r["accepted"] for r in out["results"]] == [True, False]
    assert out["nfa"]["table"]["columns"] == ["a", "b", "ε"]
    assert "digraph" in out["dfa"]["dot"]


def test_convert_rejects_bad_regex():
    with pytest.raises(ValueError):
        convert("a||b")


# ---------------------------------------------------------------- minimization

@pytest.mark.parametrize("regex, size", [
    ("(a|b)*abb", 4),   # 5 states before minimization
    ("a*", 1),
    ("a+", 2),
    ("a|b", 3),          # start, accepting, dead
])
def test_minimal_sizes(regex, size):
    assert len(build_min_dfa(regex).states) == size


def test_minimal_without_dead_state():
    assert DEAD in build_min_dfa("ab").states
    assert DEAD not in build_min_dfa("ab", dead_state=False).states


@pytest.mark.parametrize("regex", REGEXES)
@pytest.mark.parametrize("dead", [True, False])
def test_minimal_matches_python_re(regex, dead):
    dfa = build_min_dfa(regex, dead_state=dead)
    for s in all_strings("abcd", 6):
        assert simulate(dfa, s)["accepted"] == bool(re.fullmatch(regex, s)), (regex, s)


def _run_from(dfa, state, word):
    for ch in word:
        state = dfa.transitions[state][ch]
    return state in dfa.accepting


@pytest.mark.parametrize("regex", REGEXES)
def test_minimal_dfa_is_really_minimal(regex):
    dfa = build_min_dfa(regex)
    words = ["".join(t) for k in range(len(dfa.states) + 1)
             for t in itertools.product(dfa.alphabet, repeat=k)]
    for p, q in itertools.combinations(dfa.states, 2):
        assert any(_run_from(dfa, p, w) != _run_from(dfa, q, w) for w in words), (regex, p, q)


def test_convert_always_returns_minimized_dfa():
    out = convert("(a|b)*abb", ["abb", "ab"])
    assert out["counts"] == {"nfa": 14, "subset": 5, "minimal": 4}
    assert len(out["dfa"]["table"]["rows"]) == 4
    assert len(out["subset"]["table"]["rows"]) == 5
    assert out["dfa"]["table"]["info_label"] == "Merged DFA states"
    assert out["dfa"]["rounds"][-1].startswith("Round")
    assert out["dfa"]["start"] == "M0"