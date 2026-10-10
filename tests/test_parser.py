import pytest

from automata.parser import insert_concat, parse, to_postfix, validate


@pytest.mark.parametrize("regex, postfix", [
    ("a", "a"),
    ("ab", "ab."),
    ("a|b", "ab|"),
    ("a*", "a*"),
    ("a+", "a+"),
    ("ab+(c|d)*", "ab+.cd|*."),
    ("(a|b)*abb", "ab|*a.b.b."),
    ("a|bc", "abc.|"),
    ("(ab)+", "ab.+"),
])
def test_postfix(regex, postfix):
    assert parse(regex)[2] == postfix


def test_insert_concat():
    assert insert_concat("ab+(c|d)*") == "a.b+.(c|d)*"
    assert insert_concat("(a)(b)") == "(a).(b)"


def test_spaces_are_ignored():
    assert validate("a | b") == "a|b"


@pytest.mark.parametrize("bad", [
    "", "   ", "*a", "+a", "|a", "a|", "a||b", "()", "(a", "a)", "(|a)", "(a|)",
    "a$b", "(*a)", "a" * 101,
])
def test_invalid(bad):
    with pytest.raises(ValueError):
        validate(bad)
