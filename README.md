# Regex → NFA → DFA → Minimal DFA

A small web simulator (Python + Flask + Graphviz) that converts a regular expression into an NFA
(Thompson's construction), then into a DFA (subset construction), then **always shows the minimized DFA**.
Strings are tested on the minimized DFA, with a step-by-step mode that lights up the current state.

Supported syntax: letters/digits, `|` union, implicit concatenation, `*`, `+`, `( )`.

## Setup

1. Install Python 3.10+ and the **Graphviz program** (`dot -V` should work):
   - Windows: `winget install graphviz` (or graphviz.org, tick "add to PATH")
   - Ubuntu: `sudo apt install graphviz`
   - macOS: `brew install graphviz`
2. Create a virtual environment and install packages:
   ```
   python -m venv venv
   venv\Scripts\activate          # Windows   (Mac/Linux: source venv/bin/activate)
   pip install -r requirements.txt
   ```
3. Run the site:
   ```
   python app.py
   ```
   Open http://127.0.0.1:5000

Notes:
- The page loads the **Space Grotesk** font from Google Fonts, so it needs internet the first time (it falls back to a system font offline).
- If Graphviz is not installed, diagrams are drawn in the browser instead (also needs internet).

## Run the tests

```
pytest
```

Every automaton is cross-checked against Python's own `re.fullmatch` on all strings up to length 6,
and the minimized DFA is checked to be truly minimal (no two states are equivalent).

## Project layout

```
app.py                 Flask routes: GET /, POST /api/convert (everything), POST /api/test (strings only)
automata/
  parser.py            validate, insert concatenation, infix → postfix
  nfa.py               Thompson's construction (|, concat, *, +); states renumbered so the start is q0
  dfa.py               ε-closure, move, subset construction, minimization, string simulation
  tables.py            transition tables for the page
  draw.py              Graphviz DOT + SVG (styling is done in CSS)
  __init__.py          convert(): the whole pipeline
templates/index.html   page
static/style.css       black monochrome glassmorphic theme
static/script.js       page logic, zoom, step-through simulation
tests/                 pytest tests
```

## Notes

- `+` uses Thompson's star construction without the ε "skip" edge, so the fragment must be used at least once.
- Minimization uses Moore's partition refinement on the complete DFA (dead state included), so the
  result is the smallest DFA. For `(a|b)*abb`: 14 NFA states → 5 DFA states → 4 after minimization.
- The "dead state" checkbox hides the dead state (∅) in both DFAs; the DFAs stay correct, just partial.
- The DFA tab shows the minimized DFA. The DFA before minimization is under "DFA before minimization".# Regex-automata
