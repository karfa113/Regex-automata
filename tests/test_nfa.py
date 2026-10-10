from automata.nfa import EPS, build_nfa
from automata.parser import parse


def nfa_for(regex):
    return build_nfa(parse(regex)[2])


def test_single_symbol():
    n = nfa_for("a")
    assert len(n.states) == 2
    assert n.transitions[n.start]["a"] == {n.accept}


def test_union_has_six_states_for_two_symbols():
    # 2 states per symbol + new start + new accept
    assert len(nfa_for("a|b").states) == 6


def test_star_has_skip_edge():
    n = nfa_for("a*")
    assert n.accept in n.transitions[n.start][EPS]  # can skip the fragment


def test_plus_has_no_skip_edge():
    n = nfa_for("a+")
    assert n.accept not in n.transitions[n.start][EPS]  # must use fragment once
    assert len(n.states) == 4


def test_every_state_count_is_consistent():
    # Thompson NFAs have at most 2 states per symbol/operator
    for rx in ["a*", "(a|b)*abb", "(ab)+", "a+b+|c"]:
        n = nfa_for(rx)
        assert len(n.states) <= 2 * len(parse(rx)[2])


def test_alphabet():
    assert nfa_for("(a|b)*abb").alphabet == ["a", "b"]


def test_start_state_is_q0():
    for rx in ["a", "a|b", "(a|b)*abb", "a*", "(ab)+"]:
        assert nfa_for(rx).start == 0


def test_all_states_reachable_and_ids_contiguous():
    for rx in ["a|b", "(a|b)*abb", "a+b*", "((a|b)c)*"]:
        n = nfa_for(rx)
        seen, stack = {n.start}, [n.start]
        while stack:
            s = stack.pop()
            for targets in n.transitions.get(s, {}).values():
                for t in targets - seen:
                    seen.add(t)
                    stack.append(t)
        assert seen == set(n.states) == set(range(len(n.states)))
        assert n.accept in seen


def test_construction_steps_use_final_state_names():
    n = nfa_for("a|b")
    text = " ".join(n.steps)
    assert "@" not in text
    assert "new start q0" in text  # the union's new start is the NFA start