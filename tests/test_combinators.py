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
    "c1": (('RVal', [1, 2, 3, [('Lit', 3), ('Lit', 2), ('Lit', 1)]]), 2_865, 2_861),
    "c2": (('RVal', [4, 3]), 1_488, 1_495),
    "c3": (('RVal', [3]), 2_959, 2_955),
    "c4": (('RVal', [1, 2, 3, 5]), 32_667, 31_867),
    "c5": (('RVal', [[('Lit', 1), ('Lit', 2)], [('Lit', 7)]]), 26_612, 26_071),
    "c6": (('RVal', [10, 10]), 140_612, 129_471),
    "c7": (('RVal', []), 41_843, 40_589),
    "c8": (('RVal', [2]), 78_919, 75_116),
    "c9": (('RVal', [2]), 125_154, 116_007),
    "c10": (('RVal', [6]), 320_046, 272_824),
    "c11": (('RVal', [3]), 219_070, 193_690),
    "c12": (('RVal', [[('Lit', 1), ('Lit', 4)]]), 238_594, 208_995),
    "c13": (('RVal', [10, [('Lit', 11), ('Lit', 12)]]), 237_035, 207_679),
    "c14": (('RVal', [[('Lit', 2)]]), 371_403, 309_683),
    "c15": (('RVal', [6]), 172_481, 155_499),
    "c16": (('RVal', [1, 1, 2, 2, 3, 3]), 166_025, 149_952),
    "c17": (('RVal', [1]), 123_559, 114_547),
    "c18": (('RVal', [6]), 183_384, 165_082),
    "c19": (('RVal', [0]), 120_966, 112_348),
    "c20": (('RVal', [1, ('Sym', 'dup')]), 7_121, 7_068),
    "c21": (('RVal', [('Sym', 'size')]), 2_281, 2_283),
    "c22": (('RVal', [True]), 5_342, 5_314),
    "c23": (('RVal', [True]), 5_340, 5_312),
    "c24": (('RVal', [[('Lit', 1), ('Lit', 2)], 1, 2]), 3_914, 3_903),
    "c25": (('RVal', [3, 1, 2]), 6_282, 6_244),
    "c26": (('RVal', [2, 3, 1]), 6_289, 6_251),
    "c27": (('RVal', [3, 2, 1]), 7_086, 7_033),
    "c28": (('RVal', [[('Lit', 2), ('Lit', 4)]]), 488_623, 391_675),
    "c29": (('RVal', [[]]), 26_194, 25_653),
    "c30": (('RVal', [[('Lit', 2), ('Lit', 1)]]), 218_278, 192_898),
}
COMPILED = {
    "c1": (('RVal', [1, 2, 3, ('quot', ('RVal', [3, 2, 1]))]), 152, 152),
    "c2": (('RVal', [4, 3]), 107, 107),
    "c3": (('RVal', [3]), 205, 205),
    "c4": (('RVal', [1, 2, 3, 5]), 8_486, 8_495),
    "c5": (('RVal', [('quot', ('RVal', [1, 2])), ('quot', ('RVal', [7]))]), 7_003, 6_998),
    "c6": (('RVal', [10, 10]), 25_998, 25_587),
    "c7": (('RVal', []), 7_174, 7_152),
    "c8": (('RVal', [2]), 14_227, 13_826),
    "c9": (('RVal', [2]), 47_664, 46_382),
    "c10": (('RVal', [6]), 126_911, 123_640),
    "c11": (('RVal', [3]), 91_373, 89_586),
    "c12": (('RVal', [('quot', ('RVal', [1, 4]))]), 119_555, 116_496),
    "c13": (('RVal', [10, ('quot', ('RVal', [11, 12]))]), 120_440, 117_381),
    "c14": (('RVal', [('quot', ('RVal', [2]))]), 223_031, 216_779),
    "c15": (('RVal', [6]), 59_004, 57_854),
    "c16": (('RVal', [1, 1, 2, 2, 3, 3]), 57_628, 56_464),
    "c17": (('RVal', [1]), 53_475, 52_519),
    "c18": (('RVal', [6]), 65_144, 62_862),
    "c19": (('RVal', [0]), 35_845, 34_908),
    "c20": (('RVal', [1, ('Sym', 'dup')]), 642, 656),
    "c21": (('RVal', [('Sym', 'size')]), 322, 322),
    "c22": (('RVal', [True]), 814, 814),
    "c23": (('RVal', [True]), 692, 692),
    "c24": (('RVal', [('quot', ('RVal', [1, 2])), 1, 2]), 304, 318),
    "c25": (('RVal', [3, 1, 2]), 609, 623),
    "c26": (('RVal', [2, 3, 1]), 607, 621),
    "c27": (('RVal', [3, 2, 1]), 727, 741),
    "c28": (('RVal', [('quot', ('RVal', [2, 4]))]), 315_069, 305_041),
    "c29": (('RVal', [('quot', ('RVal', []))]), 6_698, 6_693),
    "c30": (('RVal', [('quot', ('RVal', [2, 1]))]), 90_061, 88_274),
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
