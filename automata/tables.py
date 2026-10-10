"""Step 5: build transition tables as plain data for the web page."""

from .nfa import EPS, qname


def _set_text(names):
    return "{" + ", ".join(names) + "}" if names else "∅"


def nfa_table(nfa):
    columns = nfa.alphabet + [EPS]
    rows = []
    for s in nfa.states:
        cells = {}
        for col in columns:
            targets = sorted(nfa.transitions.get(s, {}).get(col, set()))
            cells[col] = _set_text([qname(t) for t in targets])
        rows.append({
            "state": qname(s),
            "start": s == nfa.start,
            "accept": s == nfa.accept,
            "cells": cells,
        })
    return {"columns": columns, "rows": rows}


def dfa_table(dfa):
    """Works for both the subset-construction DFA and the minimized DFA."""
    rows = []
    for s in dfa.states:
        cells = {}
        for sym in dfa.alphabet:
            cells[sym] = dfa.transitions.get(s, {}).get(sym, "—")
        rows.append({
            "state": s,
            "start": s == dfa.start,
            "accept": s in dfa.accepting,
            "info": dfa.info.get(s, ""),
            "cells": cells,
        })
    return {"columns": list(dfa.alphabet), "rows": rows, "info_label": dfa.info_label}