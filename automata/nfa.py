"""Step 2: Thompson's construction (postfix regex -> NFA).

Every fragment has exactly one start and one accept state. While building, states
get temporary ids; at the end they are renumbered in breadth-first order from the
start state, so the start state is always q0 and the tables/diagrams read naturally.
"""

import re
from collections import defaultdict, deque

EPS = "ε"


def qname(state):
    return f"q{state}"


class NFA:
    def __init__(self, start, accept, transitions, alphabet, num_states, steps):
        self.start = start
        self.accept = accept
        self.transitions = transitions  # {state: {symbol_or_EPS: set(states)}}
        self.alphabet = sorted(alphabet)
        self.states = list(range(num_states))
        self.steps = steps  # human-readable construction log


def _ref(state):
    """Temporary marker for a state id; replaced after renumbering."""
    return f"@{state}@"


class _Builder:
    def __init__(self):
        self.count = 0
        self.trans = defaultdict(lambda: defaultdict(set))
        self.alphabet = set()
        self.steps = []

    def new_state(self):
        s = self.count
        self.count += 1
        return s

    def add(self, src, sym, dst):
        self.trans[src][sym].add(dst)

    def log(self, text):
        self.steps.append(text)


def _renumber_order(start, trans, count):
    """Map old state id -> new id, numbering breadth-first from the start state."""
    order = []
    seen = {start}
    queue = deque([start])
    while queue:
        s = queue.popleft()
        order.append(s)
        edges = trans.get(s, {})
        for sym in sorted(edges, key=lambda x: (x == EPS, x)):  # real symbols first, ε last
            for t in sorted(edges[sym]):
                if t not in seen:
                    seen.add(t)
                    queue.append(t)
    order.extend(s for s in range(count) if s not in seen)  # safety net; should be empty
    return {old: new for new, old in enumerate(order)}


def build_nfa(postfix):
    """Build an NFA from a postfix regex using Thompson's construction."""
    b = _Builder()
    stack = []  # fragments as (start, accept)

    for ch in postfix:
        if ch == ".":
            right = stack.pop()
            left = stack.pop()
            b.add(left[1], EPS, right[0])
            stack.append((left[0], right[1]))
            b.log(f"Concatenation: {_ref(left[1])} -ε-> {_ref(right[0])}; "
                  f"fragment runs {_ref(left[0])} → {_ref(right[1])}")

        elif ch == "|":
            right = stack.pop()
            left = stack.pop()
            s, a = b.new_state(), b.new_state()
            b.add(s, EPS, left[0])
            b.add(s, EPS, right[0])
            b.add(left[1], EPS, a)
            b.add(right[1], EPS, a)
            stack.append((s, a))
            b.log(f"Union: new start {_ref(s)} -ε-> {_ref(left[0])} and {_ref(right[0])}; "
                  f"{_ref(left[1])} and {_ref(right[1])} -ε-> new accept {_ref(a)}")

        elif ch == "*":
            inner = stack.pop()
            s, a = b.new_state(), b.new_state()
            b.add(s, EPS, inner[0])
            b.add(s, EPS, a)
            b.add(inner[1], EPS, inner[0])
            b.add(inner[1], EPS, a)
            stack.append((s, a))
            b.log(f"Star: new start {_ref(s)}, new accept {_ref(a)}; "
                  f"skip edge {_ref(s)} -ε-> {_ref(a)} and loop {_ref(inner[1])} -ε-> {_ref(inner[0])}")

        elif ch == "+":
            inner = stack.pop()
            s, a = b.new_state(), b.new_state()
            b.add(s, EPS, inner[0])
            b.add(inner[1], EPS, inner[0])
            b.add(inner[1], EPS, a)
            stack.append((s, a))
            b.log(f"Plus: new start {_ref(s)}, new accept {_ref(a)}; "
                  f"loop {_ref(inner[1])} -ε-> {_ref(inner[0])} but NO skip edge, "
                  "so the fragment must be used at least once")

        else:  # literal symbol
            s, a = b.new_state(), b.new_state()
            b.add(s, ch, a)
            b.alphabet.add(ch)
            stack.append((s, a))
            b.log(f"Symbol '{ch}': {_ref(s)} -{ch}-> {_ref(a)}")

    if len(stack) != 1:
        raise ValueError("Malformed expression: could not build a single NFA.")

    old_start, old_accept = stack[0]
    mapping = _renumber_order(old_start, b.trans, b.count)

    transitions = {}
    for s, by_symbol in b.trans.items():
        transitions[mapping[s]] = {
            sym: {mapping[t] for t in targets} for sym, targets in by_symbol.items()
        }

    steps = [
        re.sub(r"@(\d+)@", lambda m: qname(mapping[int(m.group(1))]), text)
        for text in b.steps
    ]
    return NFA(mapping[old_start], mapping[old_accept], transitions, b.alphabet, b.count, steps)