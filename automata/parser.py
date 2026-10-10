"""Step 1: turn a regular expression into postfix form.

Supported syntax
    a-z A-Z 0-9   literal symbols
    |             union
    (implicit)    concatenation (made explicit as '.')
    *             Kleene star  (zero or more)
    +             plus         (one or more)
    ( )           grouping
"""

MAX_LENGTH = 100
PRECEDENCE = {"|": 1, ".": 2, "*": 3, "+": 3}


def is_symbol(ch):
    return ch.isascii() and ch.isalnum()


def validate(regex):
    """Check the regex and return it with spaces removed.

    Raises ValueError with a readable message for any problem.
    """
    regex = regex.replace(" ", "")
    if not regex:
        raise ValueError("The regular expression is empty.")
    if len(regex) > MAX_LENGTH:
        raise ValueError(f"The regular expression is too long (max {MAX_LENGTH} characters).")

    depth = 0
    prev = None
    for i, ch in enumerate(regex, start=1):
        if not (is_symbol(ch) or ch in "|*+()"):
            raise ValueError(
                f"Invalid character '{ch}' at position {i}. "
                "Use letters, digits and the operators | * + ( )."
            )
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                raise ValueError(f"Unmatched ')' at position {i}.")
            if prev == "(":
                raise ValueError(f"Empty parentheses '()' at position {i - 1}.")
            if prev == "|":
                raise ValueError(f"Missing operand after '|' before position {i}.")
        elif ch in "*+":
            if prev is None or prev in "(|":
                raise ValueError(f"Operator '{ch}' at position {i} has nothing to repeat.")
        elif ch == "|":
            if prev is None or prev in "(|":
                raise ValueError(f"Operator '|' at position {i} is missing a left operand.")
        prev = ch

    if depth != 0:
        raise ValueError("Unmatched '(' - a closing ')' is missing.")
    if prev == "|":
        raise ValueError("The expression cannot end with '|'.")
    return regex


def insert_concat(regex):
    """Insert an explicit '.' between items that are implicitly concatenated.

    ab+(c|d)*  ->  a.b+.(c|d)*
    """
    out = []
    for i, ch in enumerate(regex):
        out.append(ch)
        if i + 1 < len(regex):
            nxt = regex[i + 1]
            left_ends_operand = is_symbol(ch) or ch in ")*+"
            right_starts_operand = is_symbol(nxt) or nxt == "("
            if left_ends_operand and right_starts_operand:
                out.append(".")
    return "".join(out)


def to_postfix(regex):
    """Shunting-yard: infix (with explicit '.') -> postfix.

    '*' and '+' are unary postfix operators, so they go straight to the output.
    """
    output = []
    stack = []
    for ch in regex:
        if is_symbol(ch) or ch in "*+":
            output.append(ch)
        elif ch == "(":
            stack.append(ch)
        elif ch == ")":
            while stack and stack[-1] != "(":
                output.append(stack.pop())
            stack.pop()  # discard '('
        else:  # binary operator: '|' or '.'
            while stack and stack[-1] != "(" and PRECEDENCE[stack[-1]] >= PRECEDENCE[ch]:
                output.append(stack.pop())
            stack.append(ch)
    while stack:
        output.append(stack.pop())
    return "".join(output)


def parse(regex):
    """Full pipeline. Returns (cleaned_regex, with_concat, postfix)."""
    clean = validate(regex)
    explicit = insert_concat(clean)
    return clean, explicit, to_postfix(explicit)
