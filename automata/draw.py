"""Step 6: state diagrams. Builds Graphviz DOT text and renders it to SVG.

Colours are NOT set here: the web page styles the SVG with CSS (black monochrome theme).
Nodes carry CSS classes ("accept", "dead") so the stylesheet can tell them apart.

If the Graphviz `dot` program is not installed, render_svg() returns None and
the web page falls back to drawing the DOT text in the browser (viz.js).
"""

import shutil
import subprocess
from collections import OrderedDict

from .nfa import EPS, qname

_HEADER = (
    'digraph G {\n'
    '  rankdir=LR;\n'
    '  bgcolor="transparent";\n'
    '  pad=0.3;\n'
    '  nodesep=0.45;\n'
    '  ranksep=0.6;\n'
    '  node [fontname="Helvetica", fontsize=13, shape=circle, width=0.55];\n'
    '  edge [fontname="Helvetica", fontsize=12, arrowsize=0.8];\n'
    '  __start [shape=none, label="", width=0, height=0];\n'
)


def _merge_edges(pairs):
    """pairs: iterable of (src, dst, symbol) -> {(src, dst): [symbols]} with ε last."""
    merged = OrderedDict()
    for src, dst, sym in pairs:
        merged.setdefault((src, dst), []).append(sym)
    for key, syms in merged.items():
        merged[key] = sorted(set(syms), key=lambda s: (s == EPS, s))
    return merged


def nfa_to_dot(nfa):
    lines = [_HEADER]
    for s in nfa.states:
        if s == nfa.accept:
            lines.append(f'  "{qname(s)}" [shape=doublecircle, class="accept"];\n')
        else:
            lines.append(f'  "{qname(s)}" [shape=circle];\n')
    lines.append(f'  __start -> "{qname(nfa.start)}";\n')

    pairs = []
    for s in sorted(nfa.transitions):
        for sym, targets in nfa.transitions[s].items():
            for t in sorted(targets):
                pairs.append((qname(s), qname(t), sym))
    for (src, dst), syms in _merge_edges(pairs).items():
        lines.append(f'  "{src}" -> "{dst}" [label="{",".join(syms)}"];\n')
    lines.append("}\n")
    return "".join(lines)


def dfa_to_dot(dfa):
    lines = [_HEADER]
    for s in dfa.states:
        classes = []
        if s in dfa.accepting:
            classes.append("accept")
        if s == "∅":
            classes.append("dead")
        shape = "doublecircle" if s in dfa.accepting else "circle"
        cls = f', class="{" ".join(classes)}"' if classes else ""
        style = ", style=dashed" if s == "∅" else ""
        lines.append(f'  "{s}" [shape={shape}{style}{cls}];\n')
    lines.append(f'  __start -> "{dfa.start}";\n')

    pairs = []
    for s in dfa.states:
        for sym, t in dfa.transitions.get(s, {}).items():
            pairs.append((s, t, sym))
    for (src, dst), syms in _merge_edges(pairs).items():
        lines.append(f'  "{src}" -> "{dst}" [label="{",".join(syms)}"];\n')
    lines.append("}\n")
    return "".join(lines)


def render_svg(dot_text):
    """Render DOT to an SVG string using the Graphviz `dot` program, or None."""
    dot = shutil.which("dot")
    if not dot:
        return None
    try:
        proc = subprocess.run(
            [dot, "-Tsvg"], input=dot_text.encode("utf-8"),
            capture_output=True, timeout=15, check=True,
        )
        svg = proc.stdout.decode("utf-8")
    except (subprocess.SubprocessError, OSError):
        return None
    start = svg.find("<svg")  # drop the XML prolog / DOCTYPE so it embeds cleanly
    return svg[start:] if start != -1 else None