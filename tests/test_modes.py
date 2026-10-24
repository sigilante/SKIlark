"""Phase 2: the same Joy programs through the front end in its three
forms.  The counts are the kernel's with Joy's stages 1 to 3
(PLAN.md §3): ``sumto`` is written with ``ifte`` and ``pred``, so this
set compiles with integers and truth values; all measured on skijack
0.2.1.
"""

import pytest

from skilark import compiled, interpreted, joy
from skilark.joy import DEFINITIONS, expand, parse, words

PROGRAMS = {
    "p1": "1 2 + dup +",
    "p2": "3 [dup +] i",
    "p3": "1 2 over",
    "p4": "1 [2] [3] k",
    "p5": "1 2 unit cons",
    "p6": "+",
    "p7": "3 sumto",
    "p8": "5 sumto",
}

#: outcome, then host contractions unfuelled (uP) and fuelled (rP)
INTERPRETED = {
    "p1": (('RVal', [6]), 5_260, 5_256),
    "p2": (('RVal', [6]), 4_912, 4_908),
    "p3": (('RVal', [1, 2, 1]), 5_975, 5_954),
    "p4": (('RVal', [1, 3]), 7_723, 7_677),
    "p5": (('RVal', [[('Lit', 1), ('Lit', 2)]]), 3_406, 3_409),
    "p6": (('RErr', None), 730, 751),
    "p7": (('RVal', [6]), 125_182, 118_999),
    "p8": (('RVal', [15]), 205_529, 191_207),
}
COMPILED = {
    "p1": (('RVal', [6]), 668, 668),
    "p2": (('RVal', [6]), 684, 698),
    "p3": (('RVal', [1, 2, 1]), 700, 714),
    "p4": (('RVal', [1, 3]), 968, 996),
    "p5": (('RVal', [('quot', ('RVal', [1, 2]))]), 273, 273),
    "p6": (('RErr', None), 8, 8),
    "p7": (('RVal', [6]), 26_304, 25_866),
    "p8": (('RVal', [15]), 48_507, 47_509),
}


@pytest.fixture(scope="module")
def interp():
    return interpreted(PROGRAMS)


@pytest.fixture(scope="module")
def comp():
    return compiled(PROGRAMS)


# ---------------------------------------------------------------- front end

def test_the_parser_reads_quotations_numerals_and_words():
    assert parse("3 [dup +] i") == [3, ["dup", "+"], "i"]
    assert parse("[[1] [2 +] dip]") == [[[1], [2, "+"], "dip"]]
    assert words(parse("1 [2] [3] k")) == "1 [2] [3] k"


def test_derived_words_inline_to_the_kernel():
    assert expand(parse("1 2 over"), DEFINITIONS) == [1, 2, ["dup"], "dip", "swap"]
    assert expand(parse("[1] y"), DEFINITIONS) == \
        [[1], ["dup", "cons"], "swap", "cat", "dup", "cons", "i"]
    with pytest.raises(ValueError, match="unknown word"):
        expand(parse("1 frob"), DEFINITIONS)


def test_a_kept_name_survives_as_itself():
    assert expand(parse("1 2 + sq"), dict(DEFINITIONS, sq="dup +"), keep=["sq"]) == \
        [1, 2, "+", "sq"]


# ------------------------------------------------------------ interpreted

def test_interpreted_kernel_sizes(interp):
    s = interp.e.sizes
    assert (s["exec"], s["execU"], s["step"]) == (57_902, 57_906, 57_842)


@pytest.mark.parametrize("name", sorted(PROGRAMS))
def test_interpreted_outcomes_and_counts(interp, name):
    outcome, unfuelled, fuelled = INTERPRETED[name]
    assert interp.run("u" + name) == (outcome, unfuelled), PROGRAMS[name]
    assert interp.run("r" + name) == (outcome, fuelled), PROGRAMS[name]


# --------------------------------------------------------------- compiled

def test_compiled_kernel_sizes(comp):
    s = comp.e.sizes
    assert (s["apply"], s["applyU"], s["seq"]) == (12_060, 12_064, 42)
    # every static quotation is one constructor of quot with one body;
    # the three runtime constructors are what cons, unit and cat build
    static = sorted(k for k in s if k[0] == "Q" and k[1:].isdigit())
    assert (len(static), s["b1"] > 0) == (15, True)
    assert all(k in s for k in ("QCons", "QUnit", "QThen"))


@pytest.mark.parametrize("name", sorted(PROGRAMS))
def test_compiled_outcomes_and_counts(comp, name):
    outcome, unfuelled, fuelled = COMPILED[name]
    assert comp.run("u" + name) == (outcome, unfuelled), PROGRAMS[name]
    assert comp.run("r" + name) == (outcome, fuelled), PROGRAMS[name]


def test_compiled_never_costs_more_than_interpreted():
    for name in PROGRAMS:
        assert COMPILED[name][1] < INTERPRETED[name][1], name


# ---------------------------------------------------- the laws, both forms

LAWS = {
    "swap swap == id":        ("1 2 swap swap", "1 2"),
    "dup pop == id":          ("1 dup pop", "1"),
    "[P] i == P":             ("2 [1 +] i", "2 1 +"),
    "[P] [Q] cat == [P Q]":   ("[1] [2] cat", "[1 2]"),
    "[P] [Q] dip == Q [P]":   ("5 [1] [2 +] dip", "5 2 + [1]"),
    "x unit == [x]":          ("1 unit", "[1]"),
    "[B] [A] k == A":         ("1 [2] [3] k", "1 3"),
    "[B] [A] sip == [B] A [B]": ("[1] [i 2 +] sip", "[1] i 2 + [1]"),
}
LAW_PROGRAMS = {f"l{i}{side}": text
                for i, (l, r) in enumerate(LAWS.values())
                for side, text in (("L", l), ("R", r))}


@pytest.fixture(scope="module", params=["interpreted", "compiled"])
def laws(request):
    return (interpreted if request.param == "interpreted" else compiled)(LAW_PROGRAMS)


@pytest.mark.parametrize("i", range(len(LAWS)))
def test_each_law_holds_in_both_forms(laws, i):
    """In the compiled form a quotation is opaque, so the reader compares
    quotations extensionally: the law [P] [Q] cat == [P Q] holds of two
    different quot values that apply to the same stack."""
    left, right = laws.run(f"ul{i}L")[0], laws.run(f"ul{i}R")[0]
    assert left == right and left[0] == "RVal", list(LAWS)[i]


@pytest.mark.parametrize("make", [interpreted, compiled])
def test_a_program_deeper_than_skijack_nests_spills_into_equations(make):
    """SKIjack refuses an expression whose applications nest more than 256
    deep, and a program nests about a level a word: past ``joy.SPILL``
    levels a subexpression is an equation of its own."""
    text = "1 " + "dup pop " * 150
    src = (joy.interpreted if make is interpreted else joy.compiled)({"p": text})
    lines = [line for line in src.split("\n") if line.startswith(("pp", "cp"))]
    assert any("Spill1" in line for line in lines)
    assert all(joy._app_depth(joy._tree(line.split("=", 1)[1])) <= joy.SPILL for line in lines)
    assert make({"p": text}).run("up")[0] == ("RVal", [1])


def test_the_linear_abstraction_gives_aviarys_terms():
    """skilark.abstraction.compile finds a node's free names once; the
    terms it gives are those of aviary's own abstraction, hash for hash,
    and aviary's free_vars is back when it returns."""
    import aviary_kernel.abstraction as AB
    import skijack
    from skijack.dictionary import from_expansion
    from skilark import abstraction
    src = joy.compiled({"p": "{1 2} {2 3} and", "q": "'a 'b max"})
    before = AB.free_vars
    fast, slow = from_expansion(abstraction.compile(src)), from_expansion(skijack.compile(src))
    assert AB.free_vars is before
    assert {n: fast[n].hash for n in fast.names()} == {n: slow[n].hash for n in slow.names()}
