# Regex Automata

<p align="center">
  <a href="https://github.com/"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+"></a>
  <a href="https://flask.palletsprojects.com/"><img src="https://img.shields.io/badge/Flask-3.x-000000?logo=flask&logoColor=white" alt="Flask 3"></a>
  <a href="https://graphviz.org/"><img src="https://img.shields.io/badge/Graphviz-diagrams-FF9A3D" alt="Graphviz"></a>
  <a href="https://github.com/"><img src="https://img.shields.io/badge/Tests-132%20passing-2ea44f" alt="Tests passing"></a>
</p>

<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Space+Grotesk&weight=600&size=24&pause=900&color=FF9A3D&center=true&vCenter=true&width=700&lines=Write+a+regex.;Build+an+NFA.;Convert+it+to+a+DFA.;Minimize+the+automaton.;Test+strings+step+by+step." alt="Animated project description">
</p>

<p align="center">
  An interactive visualizer that turns regular expressions into NFAs, DFAs, and minimal DFAs.
</p>

## What it does

Regex Automata is a browser-based learning tool for exploring how regular expressions become finite automata. Enter an expression and the application:

1. Parses the expression and makes concatenation explicit.
2. Builds an NFA using Thompson's construction.
3. Converts the NFA into a DFA using subset construction.
4. Minimizes the DFA using Moore-style partition refinement.
5. Draws each automaton as an interactive Graphviz diagram.
6. Tests strings against the minimized DFA, either instantly or one transition at a time.

The interface uses a black background with orange accents so the automata, transitions, accepting states, and current simulation state remain easy to see.

## Supported syntax

| Syntax | Meaning | Example |
| --- | --- | --- |
| Letters and digits | Input symbols | `a`, `b`, `0`, `1` |
| `\|` | Union | `a\|b` |
| Implicit concatenation | Sequence | `ab` |
| `*` | Zero or more repetitions | `a*` |
| `+` | One or more repetitions | `a+` |
| `( )` | Grouping | `(a\|b)*abb` |

## Construction pipeline

```mermaid
flowchart LR
    A["Regular expression"] --> B["Parser"]
    B --> C["Thompson NFA"]
    C --> D["Subset construction"]
    D --> E["Complete DFA"]
    E --> F["Minimized DFA"]
    F --> G["String simulation"]

    classDef accent fill:#17100a,stroke:#ff9a3d,color:#ffd9a8,stroke-width:2px;
    class A,B,C,D,E,F,G accent;
```

For the sample expression `(a|b)*abb`, the application reports:

```text
14 NFA states → 5 DFA states → 4 minimized DFA states
```

## Highlights

- **Visual learning:** inspect transition tables, construction steps, and diagrams.
- **Interactive diagrams:** zoom, fit, pan, and switch between NFA and minimized DFA views.
- **Step-through simulation:** watch the active DFA state move across each input symbol.
- **Complete or partial DFA:** include or hide the dead state with one checkbox.
- **Batch testing:** test many strings at once and see accepted/rejected results in a table.
- **Validation:** invalid expressions and empty input receive clear error messages.
- **Graceful diagram fallback:** if server-side Graphviz is unavailable, the browser tries Viz.js.

## Quick start

### Prerequisites

- Python 3.10 or newer
- Graphviz installed and available as `dot`

Check Graphviz with:

```bash
dot -V
```

Install Graphviz:

```bash
# Windows
winget install graphviz

# Ubuntu/Debian
sudo apt install graphviz

# macOS
brew install graphviz
```

### Run locally

```bash
git clone https://github.com/YOUR_USERNAME/regex-automata.git
cd regex-automata

python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

### Run the tests

```bash
pytest
```

The test suite cross-checks automata behavior against Python's `re.fullmatch`, validates known automata sizes, checks error handling, and verifies that minimized DFAs are actually minimal.

## Deploy on Render

This repository includes the files needed for a Render deployment:

- `requirements.txt` installs Flask, Graphviz's Python package, Gunicorn, and pytest.
- `apt.txt` installs the Graphviz system executable.
- `.gitignore` excludes local environments and generated files.

Create a Render **Web Service** connected to your GitHub repository with:

```text
Build command: pip install -r requirements.txt
Start command: gunicorn app:app
```

Render will install the system dependency from `apt.txt` and deploy the Flask application with Gunicorn.

## API

The Flask server exposes three routes:

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/` | Serves the web interface |
| `POST` | `/api/convert` | Returns parsed data, NFA/DFA tables, diagrams, and optional test results |
| `POST` | `/api/test` | Runs test strings without generating diagrams |

Example request:

```json
{
  "regex": "(a|b)*abb",
  "tests": ["abb", "ab", ""],
  "dead_state": true
}
```

## Project structure

```text
.
├── app.py                 # Flask routes and request validation
├── apt.txt                # Render/system dependency: Graphviz
├── requirements.txt       # Python dependencies
├── automata/
│   ├── parser.py          # Regex validation and infix-to-postfix conversion
│   ├── nfa.py             # Thompson NFA construction
│   ├── dfa.py             # Subset construction, minimization, simulation
│   ├── tables.py          # Data structures for UI tables and steps
│   ├── draw.py            # Graphviz DOT and SVG generation
│   └── __init__.py        # Conversion pipeline
├── templates/
│   └── index.html         # Application markup
├── static/
│   ├── style.css          # Black/orange visual theme
│   └── script.js          # UI, diagrams, zoom, and simulation
└── tests/                 # Parser, NFA, and DFA tests
```

## Implementation notes

- `+` uses Thompson's repetition construction without the epsilon skip edge, so the fragment must be used at least once.
- Minimization uses partition refinement on the complete DFA when the dead state is enabled.
- When the dead state is hidden, the displayed DFA is partial but remains behaviorally correct.
- Server-rendered SVG diagrams are styled by the browser stylesheet rather than by Graphviz colors.

## License

This project is open source and distributed under the [MIT License](./LICENSE).
You are free to use, modify, distribute, and build upon the project, subject
to the terms of that license.
