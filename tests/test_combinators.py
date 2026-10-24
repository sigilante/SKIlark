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
    "c1": (('RVal', [1, 2, 3, [('Lit', 3), ('Lit', 2), ('Lit', 1)]]), 3_141, 3_144),
    "c2": (('RVal', [4, 3]), 1_669, 1_683),
    "c3": (('RVal', [3]), 3_278, 3_281),
    "c4": (('RVal', [1, 2, 3, 5]), 36_457, 35_664),
    "c5": (('RVal', [[('Lit', 1), ('Lit', 2)], [('Lit', 7)]]), 29_764, 29_230),
    "c6": (('RVal', [10, 10]), 100_940, 96_216),
    "c7": (('RVal', []), 39_465, 38_627),
    "c8": (('RVal', [2]), 128_619, 121_517),
    "c9": (('RVal', [2]), 227_750, 206_685),
    "c10": (('RVal', [6]), 395_316, 340_431),
    "c11": (('RVal', [3]), 295_812, 262_971),
    "c12": (('RVal', [[('Lit', 1), ('Lit', 4)]]), 369_194, 317_573),
    "c13": (('RVal', [10, [('Lit', 11), ('Lit', 12)]]), 367_148, 315_852),
    "c14": (('RVal', [[('Lit', 2)]]), 491_288, 408_336),
    "c15": (('RVal', [6]), 240_064, 215_140),
    "c16": (('RVal', [1, 1, 2, 2, 3, 3]), 232_276, 208_456),
    "c17": (('RVal', [1]), 215_952, 196_491),
    "c18": (('RVal', [6]), 306_256, 270_266),
    "c19": (('RVal', [0]), 202_465, 185_490),
    "c20": (('RVal', [1, ('Sym', 'dup')]), 6_038, 6_017),
    "c21": (('RVal', [('Sym', 'size')]), 2_547, 2_556),
    "c22": (('RVal', [True]), 5_941, 5_920),
    "c23": (('RVal', [True]), 5_939, 5_918),
    "c24": (('RVal', [[('Lit', 1), ('Lit', 2)], 1, 2]), 4_314, 4_310),
    "c25": (('RVal', [3, 1, 2]), 6_836, 6_805),
    "c26": (('RVal', [2, 3, 1]), 6_842, 6_811),
    "c27": (('RVal', [3, 2, 1]), 7_703, 7_657),
    "c28": (('RVal', [[('Lit', 2), ('Lit', 4)]]), 625_478, 502_303),
    "c29": (('RVal', [[]]), 29_064, 28_530),
    "c30": (('RVal', [[('Lit', 2), ('Lit', 1)]]), 294_630, 261_789),
}
COMPILED = {
    "c1": (('RVal', [1, 2, 3, ('quot', ('RVal', [3, 2, 1]))]), 152, 152),
    "c2": (('RVal', [4, 3]), 107, 107),
    "c3": (('RVal', [3]), 205, 205),
    "c4": (('RVal', [1, 2, 3, 5]), 8_486, 8_495),
    "c5": (('RVal', [('quot', ('RVal', [1, 2])), ('quot', ('RVal', [7]))]), 7_003, 6_998),
    "c6": (('RVal', [10, 10]), 18_336, 18_086),
    "c7": (('RVal', []), 6_651, 6_664),
    "c8": (('RVal', [2]), 23_288, 22_879),
    "c9": (('RVal', [2]), 78_339, 77_018),
    "c10": (('RVal', [6]), 155_372, 152_687),
    "c11": (('RVal', [3]), 118_503, 117_073),
    "c12": (('RVal', [('quot', ('RVal', [1, 4]))]), 153_440, 150_429),
    "c13": (('RVal', [10, ('quot', ('RVal', [11, 12]))]), 152_715, 149_704),
    "c14": (('RVal', [('quot', ('RVal', [2]))]), 267_191, 260_987),
    "c15": (('RVal', [6]), 76_792, 75_688),
    "c16": (('RVal', [1, 1, 2, 2, 3, 3]), 76_240, 75_122),
    "c17": (('RVal', [1]), 82_493, 81_543),
    "c18": (('RVal', [6]), 101_898, 99_506),
    "c19": (('RVal', [0]), 59_124, 58_159),
    "c20": (('RVal', [1, ('Sym', 'dup')]), 642, 656),
    "c21": (('RVal', [('Sym', 'size')]), 322, 322),
    "c22": (('RVal', [True]), 814, 814),
    "c23": (('RVal', [True]), 692, 692),
    "c24": (('RVal', [('quot', ('RVal', [1, 2])), 1, 2]), 304, 318),
    "c25": (('RVal', [3, 1, 2]), 609, 623),
    "c26": (('RVal', [2, 3, 1]), 607, 621),
    "c27": (('RVal', [3, 2, 1]), 727, 741),
    "c28": (('RVal', [('quot', ('RVal', [2, 4]))]), 369_859, 359_879),
    "c29": (('RVal', [('quot', ('RVal', []))]), 6_698, 6_693),
    "c30": (('RVal', [('quot', ('RVal', [2, 1]))]), 118_191, 116_761),
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
