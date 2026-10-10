"""Regex -> NFA -> DFA -> minimal DFA pipeline used by the Flask app and the tests."""

from .dfa import drop_dead, minimize, simulate, subset_construction
from .draw import dfa_to_dot, nfa_to_dot, render_svg
from .nfa import build_nfa
from .parser import parse
from .tables import dfa_table, nfa_table


def _dfa_part(dfa, render):
    dot = dfa_to_dot(dfa) if render else None
    return {
        "table": dfa_table(dfa),
        "dot": dot,
        "svg": render_svg(dot) if render else None,
        "start": dfa.start,
        "accepting": sorted(dfa.accepting),
    }


def convert(regex, tests=None, dead_state=True, render=True):
    """Run the whole pipeline and return a JSON-friendly dict.

    "dfa"    is the MINIMIZED DFA (this is what the page always shows and tests strings on).
    "subset" is the DFA straight out of subset construction (before minimization).

    dead_state=False hides the dead state in both DFAs (they stay correct, just partial).
    render=False skips diagram generation; used when only test results are needed.

    Raises ValueError for invalid regular expressions.
    """
    clean, explicit, postfix = parse(regex)
    nfa = build_nfa(postfix)

    full = subset_construction(nfa, add_dead_state=True)  # complete, needed for minimization
    mini = minimize(full)
    shown_full = full if dead_state else drop_dead(full)
    shown_mini = mini if dead_state else drop_dead(mini)

    nfa_dot = nfa_to_dot(nfa) if render else None
    results = [simulate(shown_mini, t) for t in (tests or [])]

    subset = _dfa_part(shown_full, render)
    subset["steps"] = full.steps
    dfa = _dfa_part(shown_mini, render)
    dfa["rounds"] = mini.rounds

    return {
        "regex": clean,
        "with_concat": explicit,
        "postfix": postfix,
        "alphabet": list(nfa.alphabet),
        "counts": {
            "nfa": len(nfa.states),
            "subset": len(shown_full.states),
            "minimal": len(shown_mini.states),
        },
        "nfa": {
            "table": nfa_table(nfa),
            "dot": nfa_dot,
            "svg": render_svg(nfa_dot) if render else None,
            "steps": nfa.steps,
            "start": f"q{nfa.start}",
            "accept": f"q{nfa.accept}",
        },
        "dfa": dfa,
        "subset": subset,
        "results": results,
    }


def build_dfa(regex, dead_state=True):
    """Helper for tests: the DFA straight from subset construction."""
    _, _, postfix = parse(regex)
    return subset_construction(build_nfa(postfix), add_dead_state=dead_state)


def build_min_dfa(regex, dead_state=True):
    """Helper for tests: the minimized DFA."""
    full = build_dfa(regex, dead_state=True)
    mini = minimize(full)
    return mini if dead_state else drop_dead(mini)