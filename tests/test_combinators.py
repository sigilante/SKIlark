"""Joy's stage 4 (PLAN.md §3, "Toward Joy in full"): the stack as data
(``stack``, ``unstack``) and the recursion combinators, every one derived;
in both forms.  Each program is compiled alone, since a compiled set
grows with every quotation its programs hoist.  Every count was measured
on skijack 0.2.1.
"""

import pytest

from skilark import compiled, interpreted

PROGRAMS = {
    "c1": "1 2 3 stack",
    "c2": "[3 4] unstack",
    "c3": "1 2 [3] unstack",
    "c4": "1 2 3 [+] nullary",
    "c5": "[1 2] [3 4] [+] infra",
    "c6": "2 [10] times",
    "c7": "-1 [10] times",
    "c8": "0 [2 <] [succ] while",
    "c9": "2 [null] [succ] [dup pred] [*] linrec",
    "c10": "3 [1] [*] primrec",
    "c11": "[1 2] [0] [+] primrec",
    "c12": "[1 2] [dup *] map",
    "c13": "10 [1 2] [+] map",
    "c14": "[1 2 3] [2 rem 0 =] filter",
    "c15": "[1 2 3] 0 [+] fold",
    "c16": "[1 2 3] [dup] step",
    "c17": "2 [small] [] [pred dup pred] [+] binrec",
    "c18": "3 [null] [succ] [dup pred] [i *] genrec",
    "c19": "3 [null] [pop 0] [pred] tailrec",
    "c20": "[dup] first [1] dip",
    "c21": "[size] first",
    "c22": "[size] first [size] first =",
    "c23": "[dup] first [swap] first <",
    "c24": "[1 2] x",
    "c25": "1 2 3 rollup",
    "c26": "1 2 3 rolldown",
    "c27": "1 2 3 rotate",
    "c28": "[1 2 3 4] [2 rem 0 =] filter",
    "c29": "[1 2] [pop pop] infra",
    "c30": "[2 1] [[]] [cons] primrec",
}

#: outcome, then host contractions unfuelled (uP) and fuelled (rP)
INTERPRETED = {
    "c1": (('RVal', [1, 2, 3, [('Lit', 3), ('Lit', 2), ('Lit', 1)]]), 3_023, 3_019),
    "c2": (('RVal', [4, 3]), 1_597, 1_604),
    "c3": (('RVal', [3]), 3_146, 3_142),
    "c4": (('RVal', [1, 2, 3, 5]), 34_886, 34_086),
    "c5": (('RVal', [[('Lit', 1), ('Lit', 2)], [('Lit', 7)]]), 28_461, 27_920),
    "c6": (('RVal', [10, 10]), 173_598, 159_099),
    "c7": (('RVal', []), 51_750, 50_119),
    "c8": (('RVal', [2]), 119_118, 112_009),
    "c9": (('RVal', [2]), 212_934, 191_862),
    "c10": (('RVal', [6]), 607_450, 480_776),
    "c11": (('RVal', [3]), 272_964, 240_116),
    "c12": (('RVal', [[('Lit', 1), ('Lit', 4)]]), 335_565, 287_416),
    "c13": (('RVal', [10, [('Lit', 11), ('Lit', 12)]]), 333_576, 285_737),
    "c14": (('RVal', [[('Lit', 2)]]), 468_546, 385_587),
    "c15": (('RVal', [6]), 228_183, 203_252),
    "c16": (('RVal', [1, 1, 2, 2, 3, 3]), 220_826, 196_999),
    "c17": (('RVal', [1]), 202_565, 183_097),
    "c18": (('RVal', [6]), 287_366, 251_369),
    "c19": (('RVal', [0]), 188_847, 171_865),
    "c20": (('RVal', [1, ('Sym', 'dup')]), 5_792, 5_764),
    "c21": (('RVal', [('Sym', 'size')]), 2_440, 2_442),
    "c22": (('RVal', [True]), 5_699, 5_671),
    "c23": (('RVal', [True]), 5_697, 5_669),
    "c24": (('RVal', [[('Lit', 1), ('Lit', 2)], 1, 2]), 4_147, 4_136),
    "c25": (('RVal', [3, 1, 2]), 6_581, 6_543),
    "c26": (('RVal', [2, 3, 1]), 6_587, 6_549),
    "c27": (('RVal', [3, 2, 1]), 7_420, 7_367),
    "c28": (('RVal', [[('Lit', 2), ('Lit', 4)]]), 598_744, 475_562),
    "c29": (('RVal', [[]]), 27_857, 27_316),
    "c30": (('RVal', [[('Lit', 2), ('Lit', 1)]]), 271_916, 239_068),
}
COMPILED = {
    "c1": (('RVal', [1, 2, 3, ('quot', ('RVal', [3, 2, 1]))]), 152, 152),
    "c2": (('RVal', [4, 3]), 107, 107),
    "c3": (('RVal', [3]), 205, 205),
    "c4": (('RVal', [1, 2, 3, 5]), 8_486, 8_495),
    "c5": (('RVal', [('quot', ('RVal', [1, 2])), ('quot', ('RVal', [7]))]), 7_003, 6_998),
    "c6": (('RVal', [10, 10]), 33_298, 32_882),
    "c7": (('RVal', []), 9_619, 9_611),
    "c8": (('RVal', [2]), 23_288, 22_879),
    "c9": (('RVal', [2]), 77_875, 76_554),
    "c10": (('RVal', [6]), 220_869, 217_096),
    "c11": (('RVal', [3]), 128_173, 126_743),
    "c12": (('RVal', [('quot', ('RVal', [1, 4]))]), 153_440, 150_429),
    "c13": (('RVal', [10, ('quot', ('RVal', [11, 12]))]), 152_715, 149_704),
    "c14": (('RVal', [('quot', ('RVal', [2]))]), 266_494, 260_290),
    "c15": (('RVal', [6]), 76_792, 75_688),
    "c16": (('RVal', [1, 1, 2, 2, 3, 3]), 76_240, 75_122),
    "c17": (('RVal', [1]), 82_029, 81_079),
    "c18": (('RVal', [6]), 100_843, 98_451),
    "c19": (('RVal', [0]), 58_069, 57_104),
    "c20": (('RVal', [1, ('Sym', 'dup')]), 642, 656),
    "c21": (('RVal', [('Sym', 'size')]), 322, 322),
    "c22": (('RVal', [True]), 814, 814),
    "c23": (('RVal', [True]), 692, 692),
    "c24": (('RVal', [('quot', ('RVal', [1, 2])), 1, 2]), 304, 318),
    "c25": (('RVal', [3, 1, 2]), 609, 623),
    "c26": (('RVal', [2, 3, 1]), 607, 621),
    "c27": (('RVal', [3, 2, 1]), 727, 741),
    "c28": (('RVal', [('quot', ('RVal', [2, 4]))]), 369_049, 359_069),
    "c29": (('RVal', [('quot', ('RVal', []))]), 6_698, 6_693),
    "c30": (('RVal', [('quot', ('RVal', [2, 1]))]), 127_861, 126_431),
}


@pytest.fixture(scope="module")
def interp():
    return interpreted(PROGRAMS)


@pytest.mark.parametrize("name", sorted(PROGRAMS))
def test_interpreted_combinators(interp, name):
    outcome, unfuelled, fuelled = INTERPRETED[name]
    assert interp.run("u" + name) == (outcome, unfuelled), PROGRAMS[name]
    assert interp.run("r" + name) == (outcome, fuelled), PROGRAMS[name]


@pytest.mark.parametrize("name", sorted(PROGRAMS))
def test_compiled_combinators(name):
    comp = compiled({name: PROGRAMS[name]})
    outcome, unfuelled, fuelled = COMPILED[name]
    assert comp.run("u" + name) == (outcome, unfuelled), PROGRAMS[name]
    assert comp.run("r" + name) == (outcome, fuelled), PROGRAMS[name]


def test_a_quoted_derived_word_is_its_symbol():
    """Joy reads ``[size] first`` as the symbol ``size``: a derived word in
    a quotation is a symbol, named as the reference's builtin is, and two
    symbols compare by name (``dup`` before ``swap``)."""
    for table in (INTERPRETED, COMPILED):
        assert table["c21"][0] == ("RVal", [("Sym", "size")])
        assert table["c22"][0] == table["c23"][0] == ("RVal", [True])


def test_dip_puts_a_symbol_back_as_a_symbol():
    """``dip`` restores the item it held: a symbol comes back as itself,
    not run."""
    assert INTERPRETED["c20"][0] == COMPILED["c20"][0] == ("RVal", [1, ("Sym", "dup")])


def test_map_and_filter_run_on_the_callers_stack():
    """``map`` and ``filter`` run their quotation on each element above
    the stack they were called on, as the reference does: ``10 [1 2] [+]
    map`` adds the 10 to each."""
    assert INTERPRETED["c13"][0] == ("RVal", [10, [("Lit", 11), ("Lit", 12)]])


# ---------------------------------------------------- the laws, both forms

LAWS = {
    "stack unstack == id":               ("1 2 stack unstack", "1 2"),
    "x [P] nullary == x x P":            ("3 [dup *] nullary", "3 3 dup *"),
    "L [P] infra == [L unstack P stack]": ("[1 2] [+] infra", "[3]"),
    "2 [P] times == P P":                ("1 [dup +] 2 swap times", "1 dup + dup +"),
    "n [I] [C] primrec == n .. 1 I C ..": ("3 [1] [*] primrec", "3 2 1 1 * * *"),
    "linrec == primrec":                 ("3 [null] [succ] [dup pred] [*] linrec", "3 [1] [*] primrec"),
    "A [P] map size == A size":          ("[1 2] [dup *] map size", "[1 2] size"),
    "A [B] filter":                      ("[1 2 3] [2 <] filter", "[1]"),
    "A V [P] fold == V A [P] step":      ("[1 2] 0 [+] fold", "0 [1 2] [+] step"),
    "[B] [D] while":                     ("0 [2 <] [succ] while", "2"),
}
LAW_PROGRAMS = {f"l{i}{side}": text
                for i, (l, r) in enumerate(LAWS.values())
                for side, text in (("L", l), ("R", r))}


@pytest.fixture(scope="module")
def interp_laws():
    return interpreted(LAW_PROGRAMS)


@pytest.mark.parametrize("i", range(len(LAWS)))
def test_each_law_holds_interpreted(interp_laws, i):
    left, right = interp_laws.run(f"ul{i}L")[0], interp_laws.run(f"ul{i}R")[0]
    assert left == right and left[0] == "RVal", list(LAWS)[i]


@pytest.mark.parametrize("i", range(len(LAWS)))
def test_each_law_holds_compiled(i):
    left, right = (compiled({"p": LAW_PROGRAMS[f"l{i}{side}"]}).run("up")[0]
                   for side in ("L", "R"))
    assert left == right and left[0] == "RVal", list(LAWS)[i]
