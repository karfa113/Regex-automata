"""Steps 3 and 4: subset construction (NFA -> DFA), DFA minimization, string simulation."""

from collections import deque

from .nfa import EPS, qname

MAX_DFA_STATES = 200
DEAD = "∅"


class DFA:
    def __init__(self):
        self.start = None
        self.alphabet = []
        self.states = []          # ordered names
        self.transitions = {}     # {name: {symbol: name}}
        self.accepting = set()
        self.state_sets = {}      # subset DFA only: {name: sorted list of NFA state ids}
        self.info = {}            # {name: text shown in the "info" table column}
        self.info_label = ""      # header of that column
        self.steps = []           # subset construction log for the UI
        self.rounds = []          # minimization log for the UI


def epsilon_closure(nfa, states):
    """All NFA states reachable from `states` using only ε-moves."""
    closure = set(states)
    stack = list(states)
    while stack:
        s = stack.pop()
        for t in nfa.transitions.get(s, {}).get(EPS, ()):
            if t not in closure:
                closure.add(t)
                stack.append(t)
    return frozenset(closure)


def move(nfa, states, symbol):
    result = set()
    for s in states:
        result |= nfa.transitions.get(s, {}).get(symbol, set())
    return result


def _fmt(states):
    return "{" + ", ".join(qname(s) for s in sorted(states)) + "}" if states else "∅"


def subset_construction(nfa, add_dead_state=True):
    dfa = DFA()
    dfa.alphabet = list(nfa.alphabet)
    dfa.info_label = "NFA states"

    start_set = epsilon_closure(nfa, {nfa.start})
    names = {start_set: "D0"}
    queue = deque([start_set])

    dfa.start = "D0"
    dfa.states.append("D0")
    dfa.state_sets["D0"] = sorted(start_set)
    dfa.info["D0"] = _fmt(start_set)
    dfa.transitions["D0"] = {}
    if nfa.accept in start_set:
        dfa.accepting.add("D0")

    while queue:
        current = queue.popleft()
        cname = names[current]
        step = {"state": cname, "nfa_states": _fmt(current), "moves": []}

        for sym in dfa.alphabet:
            moved = move(nfa, current, sym)
            target_set = epsilon_closure(nfa, moved) if moved else frozenset()
            target_name = None

            if target_set:
                if target_set not in names:
                    if len(names) >= MAX_DFA_STATES:
                        raise ValueError(
                            f"The DFA would exceed {MAX_DFA_STATES} states. Try a smaller expression."
                        )
                    name = f"D{len(names)}"
                    names[target_set] = name
                    dfa.states.append(name)
                    dfa.state_sets[name] = sorted(target_set)
                    dfa.info[name] = _fmt(target_set)
                    dfa.transitions[name] = {}
                    if nfa.accept in target_set:
                        dfa.accepting.add(name)
                    queue.append(target_set)
                target_name = names[target_set]
                dfa.transitions[cname][sym] = target_name

            step["moves"].append({
                "symbol": sym,
                "move": _fmt(moved),
                "closure": _fmt(target_set),
                "target": target_name,
            })
        dfa.steps.append(step)

    if add_dead_state:
        needs_dead = any(
            sym not in dfa.transitions[s] for s in dfa.states for sym in dfa.alphabet
        )
        if needs_dead:
            dfa.states.append(DEAD)
            dfa.state_sets[DEAD] = []
            dfa.info[DEAD] = "∅"
            dfa.transitions[DEAD] = {}
            for s in dfa.states:
                for sym in dfa.alphabet:
                    dfa.transitions[s].setdefault(sym, DEAD)

    return dfa


# ---------------------------------------------------------------- minimization

def _alive_states(dfa):
    """States from which an accepting state can still be reached."""
    alive = set(dfa.accepting)
    changed = True
    while changed:
        changed = False
        for s in dfa.states:
            if s not in alive and any(t in alive for t in dfa.transitions.get(s, {}).values()):
                alive.add(s)
                changed = True
    return alive


def _fmt_blocks(block_of, states):
    groups = {}
    for s in states:
        groups.setdefault(block_of[s], []).append(s)
    return " | ".join("{" + ", ".join(g) + "}" for g in groups.values())


def minimize(dfa):
    """Moore's partition refinement. `dfa` must be complete (every state has every symbol)."""
    states = list(dfa.states)
    for s in states:
        for a in dfa.alphabet:
            if a not in dfa.transitions.get(s, {}):
                raise ValueError("Minimization needs a complete DFA (include the dead state).")

    # Round 0: accepting vs non-accepting
    block_of = {s: (1 if s in dfa.accepting else 0) for s in states}
    rounds = [f"Round 0 (accepting vs non-accepting): {_fmt_blocks(block_of, states)}"]
    count = len(set(block_of.values()))
    round_no = 0

    while True:
        round_no += 1
        signature = {
            s: (block_of[s], tuple(block_of[dfa.transitions[s][a]] for a in dfa.alphabet))
            for s in states
        }
        ids = {}
        new_block = {s: ids.setdefault(signature[s], len(ids)) for s in states}
        new_count = len(ids)
        if new_count == count:
            rounds.append(
                f"Round {round_no}: no group splits. The groups above are the states of the minimal DFA."
            )
            break
        block_of, count = new_block, new_count
        rounds.append(f"Round {round_no}: {_fmt_blocks(block_of, states)}")

    # Build the minimal DFA
    alive = _alive_states(dfa)
    members = {}
    for s in states:
        members.setdefault(block_of[s], []).append(s)

    name_of_block = {}
    counter = 0
    for bid, group in members.items():
        if not any(s in alive for s in group):
            name_of_block[bid] = DEAD
        else:
            name_of_block[bid] = f"M{counter}"
            counter += 1

    mini = DFA()
    mini.alphabet = list(dfa.alphabet)
    mini.info_label = "Merged DFA states"
    mini.rounds = rounds
    mini.start = name_of_block[block_of[dfa.start]]
    for bid, group in members.items():
        name = name_of_block[bid]
        mini.states.append(name)
        mini.info[name] = "{" + ", ".join(group) + "}"
        rep = group[0]
        mini.transitions[name] = {
            a: name_of_block[block_of[dfa.transitions[rep][a]]] for a in dfa.alphabet
        }
        if rep in dfa.accepting:
            mini.accepting.add(name)
    return mini


def drop_dead(dfa):
    """Copy of `dfa` without states that can never reach an accepting state."""
    alive = _alive_states(dfa)
    if dfa.start not in alive:
        return dfa  # empty language: keep as is
    out = DFA()
    out.start = dfa.start
    out.alphabet = list(dfa.alphabet)
    out.info_label = dfa.info_label
    out.steps = dfa.steps
    out.rounds = dfa.rounds
    for s in dfa.states:
        if s not in alive:
            continue
        out.states.append(s)
        out.transitions[s] = {a: t for a, t in dfa.transitions[s].items() if t in alive}
        out.info[s] = dfa.info.get(s, "")
        if s in dfa.state_sets:
            out.state_sets[s] = dfa.state_sets[s]
        if s in dfa.accepting:
            out.accepting.add(s)
    return out


# ------------------------------------------------------------------ simulation

def simulate(dfa, string):
    """Run the DFA on `string` and return the full trace."""
    current = dfa.start
    path = []
    result = {
        "string": string,
        "accepted": False,
        "path": path,
        "start_state": dfa.start,
        "final_state": None,
        "reason": "",
    }

    for i, ch in enumerate(string):
        if ch not in dfa.alphabet:
            result["final_state"] = current
            result["reason"] = (
                f"Rejected: symbol '{ch}' (position {i + 1}) is not in the alphabet "
                f"{{{', '.join(dfa.alphabet)}}}."
            )
            return result
        nxt = dfa.transitions.get(current, {}).get(ch)
        if nxt is None:
            result["final_state"] = current
            result["reason"] = (
                f"Rejected: no transition from {current} on '{ch}' (position {i + 1})."
            )
            return result
        path.append({"from": current, "symbol": ch, "to": nxt})
        current = nxt

    result["final_state"] = current
    result["accepted"] = current in dfa.accepting
    if result["accepted"]:
        result["reason"] = f"Accepted: ended in accepting state {current}."
    elif current == DEAD:
        result["reason"] = "Rejected: the DFA entered the dead state."
    else:
        result["reason"] = f"Rejected: ended in non-accepting state {current}."
    return result