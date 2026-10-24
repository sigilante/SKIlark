"""Joy beyond the basis (PLAN.md §3, "Toward Joy in full"): stage 1,
arithmetic and comparison, on integers since stage 1b; stage 2, truth
values, ``branch`` and ``ifte``; stage 3, quotations as lists, with words
as symbols; in both forms.  Since stage 4 the words behave as the
reference implementation's (``test_conformance``): a test takes any value
as a truth value and ``=`` compares across kinds, so ``1 true =`` is true
and ``1 [2] [3] branch`` runs ``[2]``.  Every count was measured on
skijack 0.2.1.
"""

import pytest

from skilark import compiled, interpreted

PROGRAMS = {
    "w1": "3 4 *",
    "w2": "5 succ",
    "w3": "5 pred",
    "w4": "0 pred",
    "w5": "3 7 max",
    "w6": "3 7 min",
    "w7": "4 4 =",
    "w8": "2 3 <",
    "w9": "3 2 <",
    "w10": "2 3 >",
    "w11": "3 3 <=",
    "w12": "3 3 >=",
    "w13": "2 3 !=",
    "w14": "true false and",
    "w15": "true false or",
    "w16": "true not",
    "w17": "true true xor",
    "w18": "true false =",
    "w19": "true [1] [2] branch",
    "w20": "false [1] [2] branch",
    "w21": "1 [pop true] [2] [3] ifte",
    "w22": "4 [3 <] [1] [2] ifte",
    "w23": "5 fact",
    "w24": "1 true =",
    "w25": "1 [2] [3] branch",
    "w26": "true 1 *",
    "w27": "3 5 -",
    "w28": "-3 neg",
    "w29": "-3 abs",
    "w30": "-3 sign",
    "w31": "0 sign",
    "w32": "4 sign",
    "w33": "7 2 /",
    "w34": "-7 2 /",
    "w35": "7 -2 /",
    "w36": "-7 2 rem",
    "w37": "7 -2 rem",
    "w38": "7 0 /",
    "w39": "-2 3 *",
    "w40": "-2 -3 *",
    "w41": "-2 3 <",
    "w42": "-3 -2 <",
    "w43": "-1 succ",
    "w44": "-5 -5 =",
    "w45": "-1 1 max",
    "w46": "1 -2 +",
    "w47": "-1 unit",
    "w48": "4 sumto",
    "w49": "[1 2 3] first",
    "w50": "[1 2 3] rest",
    "w51": "[1 2 3] uncons",
    "w52": "[1 2 3] unswons",
    "w53": "[] null",
    "w54": "[1] null",
    "w55": "0 null",
    "w56": "[1] small",
    "w57": "[1 2] small",
    "w58": "1 small",
    "w59": "2 small",
    "w60": "[1 2 3] size",
    "w61": "[] size",
    "w62": "[dup +] first",
    "w63": "3 [dup +] first unit i",
    "w64": "[1 2] [3 4] concat size",
    "w65": "[1 2] [3 4] concat 2 at",
    "w66": "[1 2 3 4] 2 take",
    "w67": "[1 2 3 4] 2 drop",
    "w68": "[1 2] 5 take",
    "w69": "[1 2] 5 drop",
    "w70": "[] first",
    "w71": "[dup] first [dup] first =",
    "w72": "[dup] first [swap] first =",
    "w73": "[1 2] 0 swons",
    "w74": "[[1 2] 3] first size",
    "w75": "1 [2 3] of",
    "w76": "[2 3] 1 at",
    "w77": "[1 2] [3] cat uncons",
    "w78": "[true 1] first",
    "w79": "[] [1] cat first",
    "w80": "[1 2] [] cat size",
}

#: outcome, then host contractions unfuelled (uP) and fuelled (rP)
INTERPRETED = {
    "w1": (('RVal', [12]), 3_026, 3_028),
    "w2": (('RVal', [6]), 9_883, 9_823),
    "w3": (('RVal', [4]), 9_881, 9_821),
    "w4": (('RVal', [-1]), 9_881, 9_821),
    "w5": (('RVal', [7]), 53_707, 52_076),
    "w6": (('RVal', [3]), 52_721, 51_147),
    "w7": (('RVal', [True]), 2_470, 2_472),
    "w8": (('RVal', [True]), 2_468, 2_470),
    "w9": (('RVal', [False]), 2_468, 2_470),
    "w10": (('RVal', [False]), 41_565, 40_551),
    "w11": (('RVal', [True]), 15_746, 15_574),
    "w12": (('RVal', [True]), 24_720, 24_333),
    "w13": (('RVal', [True]), 3_371, 3_367),
    "w14": (('RVal', [False]), 43_702, 42_642),
    "w15": (('RVal', [True]), 46_053, 44_898),
    "w16": (('RVal', [False]), 1_713, 1_720),
    "w17": (('RVal', [False]), 41_580, 40_611),
    "w18": (('RVal', [False]), 2_470, 2_472),
    "w19": (('RVal', [1]), 4_607, 4_596),
    "w20": (('RVal', [2]), 4_601, 4_590),
    "w21": (('RVal', [1, 2]), 8_865, 8_812),
    "w22": (('RVal', [4, 2]), 9_596, 9_543),
    "w23": (('RVal', [120]), 192_273, 177_944),
    "w24": (('RVal', [True]), 2_470, 2_472),
    "w25": (('RVal', [2]), 4_643, 4_632),
    "w26": (('RErr', None), 2_960, 2_967),
    "w27": (('RVal', [-2]), 3_028, 3_030),
    "w28": (('RVal', [3]), 3_884, 3_880),
    "w29": (('RVal', [3]), 13_784, 13_666),
    "w30": (('RVal', [-1]), 12_227, 12_125),
    "w31": (('RVal', [0]), 16_352, 16_180),
    "w32": (('RVal', [1]), 16_778, 16_606),
    "w33": (('RVal', [3]), 3_076, 3_078),
    "w34": (('RVal', [-3]), 3_076, 3_078),
    "w35": (('RVal', [-3]), 3_072, 3_074),
    "w36": (('RVal', [-1]), 3_074, 3_076),
    "w37": (('RVal', [1]), 3_070, 3_072),
    "w38": (('RErr', None), 2_996, 3_003),
    "w39": (('RVal', [-6]), 3_026, 3_028),
    "w40": (('RVal', [6]), 3_026, 3_028),
    "w41": (('RVal', [True]), 2_468, 2_470),
    "w42": (('RVal', [True]), 2_468, 2_470),
    "w43": (('RVal', [0]), 9_883, 9_823),
    "w44": (('RVal', [True]), 2_470, 2_472),
    "w45": (('RVal', [1]), 53_491, 51_860),
    "w46": (('RVal', [-1]), 3_030, 3_032),
    "w47": (('RVal', [[('Lit', -1)]]), 1_614, 1_621),
    "w48": (('RVal', [10]), 155_592, 145_755),
    "w49": (('RVal', [1]), 2_547, 2_549),
    "w50": (('RVal', [[('Lit', 2), ('Lit', 3)]]), 3_408, 3_404),
    "w51": (('RVal', [1, [('Lit', 2), ('Lit', 3)]]), 1_767, 1_774),
    "w52": (('RVal', [[('Lit', 2), ('Lit', 3)], 1]), 2_625, 2_627),
    "w53": (('RVal', [True]), 1_587, 1_594),
    "w54": (('RVal', [False]), 1_587, 1_594),
    "w55": (('RVal', [True]), 1_587, 1_594),
    "w56": (('RVal', [True]), 1_729, 1_736),
    "w57": (('RVal', [False]), 1_729, 1_736),
    "w58": (('RVal', [True]), 1_731, 1_738),
    "w59": (('RVal', [False]), 1_731, 1_738),
    "w60": (('RVal', [3]), 82_459, 79_158),
    "w61": (('RVal', [0]), 24_108, 23_749),
    "w62": (('RVal', [('Sym', 'dup')]), 2_547, 2_549),
    "w63": (('RVal', [3, 3]), 6_139, 6_111),
    "w64": (('RVal', [4]), 105_055, 99_922),
    "w65": (('RVal', [3]), 161_143, 149_397),
    "w66": (('RVal', [[('Lit', 1), ('Lit', 2)]]), 415_906, 353_486),
    "w67": (('RVal', [[('Lit', 3), ('Lit', 4)]]), 156_574, 145_433),
    "w68": (('RVal', [[('Lit', 1), ('Lit', 2)]]), 258_193, 230_978),
    "w69": (('RVal', [[]]), 155_288, 144_444),
    "w70": (('RErr', None), 1_684, 1_695),
    "w71": (('RVal', [True]), 5_941, 5_913),
    "w72": (('RVal', [False]), 5_941, 5_913),
    "w73": (('RVal', [[('Lit', 0), ('Lit', 1), ('Lit', 2)]]), 3_469, 3_465),
    "w74": (('RVal', [2]), 65_161, 63_039),
    "w75": (('RVal', [3]), 112_551, 106_361),
    "w76": (('RVal', [3]), 111_574, 105_499),
    "w77": (('RVal', [1, [('Lit', 2), ('Lit', 3)]]), 3_800, 3_796),
    "w78": (('RVal', [True]), 2_547, 2_549),
    "w79": (('RVal', [1]), 4_552, 4_541),
    "w80": (('RVal', [2]), 65_037, 62_915),
}
COMPILED = {
    "w1": (('RVal', [12]), 343, 343),
    "w2": (('RVal', [6]), 3_183, 3_197),
    "w3": (('RVal', [4]), 3_183, 3_197),
    "w4": (('RVal', [-1]), 3_183, 3_197),
    "w5": (('RVal', [7]), 22_070, 22_196),
    "w6": (('RVal', [3]), 21_940, 22_066),
    "w7": (('RVal', [True]), 165, 165),
    "w8": (('RVal', [True]), 165, 165),
    "w9": (('RVal', [False]), 165, 165),
    "w10": (('RVal', [False]), 6_593, 6_635),
    "w11": (('RVal', [True]), 6_543, 6_585),
    "w12": (('RVal', [True]), 280, 280),
    "w13": (('RVal', [True]), 280, 280),
    "w14": (('RVal', [False]), 14_411, 14_495),
    "w15": (('RVal', [True]), 16_169, 16_250),
    "w16": (('RVal', [False]), 116, 116),
    "w17": (('RVal', [False]), 12_593, 12_663),
    "w18": (('RVal', [False]), 165, 165),
    "w19": (('RVal', [1]), 1_959, 1_973),
    "w20": (('RVal', [2]), 1_953, 1_967),
    "w21": (('RVal', [1, 2]), 3_804, 3_832),
    "w22": (('RVal', [4, 2]), 4_255, 4_283),
    "w23": (('RVal', [120]), 111_726, 110_728),
    "w24": (('RVal', [True]), 165, 165),
    "w25": (('RVal', [2]), 1_993, 2_007),
    "w26": (('RErr', None), 331, 331),
    "w27": (('RVal', [-2]), 343, 343),
    "w28": (('RVal', [3]), 461, 461),
    "w29": (('RVal', [3]), 3_325, 3_339),
    "w30": (('RVal', [-1]), 2_988, 3_002),
    "w31": (('RVal', [0]), 5_002, 5_013),
    "w32": (('RVal', [1]), 5_290, 5_301),
    "w33": (('RVal', [3]), 387, 387),
    "w34": (('RVal', [-3]), 387, 387),
    "w35": (('RVal', [-3]), 383, 383),
    "w36": (('RVal', [-1]), 387, 387),
    "w37": (('RVal', [1]), 383, 383),
    "w38": (('RErr', None), 363, 363),
    "w39": (('RVal', [-6]), 343, 343),
    "w40": (('RVal', [6]), 343, 343),
    "w41": (('RVal', [True]), 165, 165),
    "w42": (('RVal', [True]), 165, 165),
    "w43": (('RVal', [0]), 3_183, 3_197),
    "w44": (('RVal', [True]), 165, 165),
    "w45": (('RVal', [1]), 21_854, 21_980),
    "w46": (('RVal', [-1]), 343, 343),
    "w47": (('RVal', [('quot', ('RVal', [-1]))]), 82, 82),
    "w48": (('RVal', [10]), 91_053, 90_366),
    "w49": (('RVal', [1]), 698, 698),
    "w50": (('RVal', [('quot', ('RVal', [2, 3]))]), 819, 819),
    "w51": (('RVal', [1, ('quot', ('RVal', [2, 3]))]), 621, 621),
    "w52": (('RVal', [('quot', ('RVal', [2, 3])), 1]), 740, 740),
    "w53": (('RVal', [True]), 82, 82),
    "w54": (('RVal', [False]), 82, 82),
    "w55": (('RVal', [True]), 82, 82),
    "w56": (('RVal', [True]), 118, 118),
    "w57": (('RVal', [False]), 118, 118),
    "w58": (('RVal', [True]), 120, 120),
    "w59": (('RVal', [False]), 120, 120),
    "w60": (('RVal', [3]), 57_574, 57_240),
    "w61": (('RVal', [0]), 14_397, 14_382),
    "w62": (('RVal', [('Sym', 'dup')]), 692, 692),
    "w63": (('RVal', [3, 3]), 4_360, 4_371),
    "w64": (('RVal', [4]), 82_927, 82_434),
    "w65": (('RVal', [3]), 90_066, 89_815),
    "w66": (('RVal', [('quot', ('RVal', [1, 2]))]), 205_477, 203_844),
    "w67": (('RVal', [('quot', ('RVal', [3, 4]))]), 80_086, 79_835),
    "w68": (('RVal', [('quot', ('RVal', [1, 2]))]), 126_343, 125_699),
    "w69": (('RVal', [('quot', ('RVal', []))]), 81_371, 81_120),
    "w70": (('RErr', None), 670, 670),
    "w71": (('RVal', [True]), 1_654, 1_654),
    "w72": (('RVal', [False]), 1_590, 1_590),
    "w73": (('RVal', [('quot', ('RVal', [0, 1, 2]))]), 320, 320),
    "w74": (('RVal', [2]), 43_857, 43_667),
    "w75": (('RVal', [3]), 55_921, 55_842),
    "w76": (('RVal', [3]), 55_786, 55_707),
    "w77": (('RVal', [1, ('quot', ('RVal', [2, 3]))]), 2_707, 2_707),
    "w78": (('RVal', [True]), 672, 672),
    "w79": (('RVal', [1]), 3_300, 3_300),
    "w80": (('RVal', [2]), 51_820, 51_630),
}


@pytest.fixture(scope="module")
def interp():
    return interpreted(PROGRAMS)


@pytest.fixture(scope="module")
def comp():
    return compiled(PROGRAMS)


@pytest.mark.parametrize("name", sorted(PROGRAMS))
def test_interpreted_words(interp, name):
    outcome, unfuelled, fuelled = INTERPRETED[name]
    assert interp.run("u" + name) == (outcome, unfuelled), PROGRAMS[name]
    assert interp.run("r" + name) == (outcome, fuelled), PROGRAMS[name]


@pytest.mark.parametrize("name", sorted(PROGRAMS))
def test_compiled_words(comp, name):
    outcome, unfuelled, fuelled = COMPILED[name]
    assert comp.run("u" + name) == (outcome, unfuelled), PROGRAMS[name]
    assert comp.run("r" + name) == (outcome, fuelled), PROGRAMS[name]


def test_ifte_runs_its_test_then_restores_the_stack():
    """``[B] [T] [F] ifte`` runs B for its truth value alone: what B did to
    the stack is undone before T or F runs (w21 pops the 1, which comes
    back)."""
    assert INTERPRETED["w21"][0] == COMPILED["w21"][0] == ("RVal", [1, 2])


def test_a_program_that_cannot_go_negative_computes_on_naturals():
    """Negatives come only from ``- pred / rem`` and negative literals, so a
    compiled program without them computes on naturals, with the same
    answers; zk's verifiers are such programs."""
    from skilark import joy
    assert "int    ===" not in joy.compiled({"p": "3 4 * 5 +"})
    assert "int    ===" in joy.compiled({"p": "3 5 -"})
    assert "int    ===" in joy.compiled({"p": "[-1] i"})
    assert "int    ===" in joy.compiled({"p": "4 sumto"})      # sumto uses pred


def test_ifz_has_left_the_kernel():
    """``ifz``, the Scott eliminator of a natural, is not Joy: the
    interpreted form refuses it, and the compiled form keeps it only for a
    program on naturals."""
    from skilark import joy
    with pytest.raises(ValueError, match="not a Joy word"):
        joy.interpreted({"p": "1 [2] [3] ifz"})
    assert "wIfz" in joy.compiled({"p": "1 [2] [3] ifz"})
    with pytest.raises(ValueError, match="ifz takes naturals"):
        joy.compiled({"p": "1 pred [2] [3] ifz"})


def test_a_word_in_a_quotation_is_a_symbol():
    """Joy's ``[dup +] first`` is the symbol ``dup``, which runs when it is
    consed back into a quotation and the quotation is run, and ``=`` tells
    two symbols apart by name."""
    assert INTERPRETED["w62"][0] == COMPILED["w62"][0] == ("RVal", [("Sym", "dup")])
    assert INTERPRETED["w63"][0] == COMPILED["w63"][0] == ("RVal", [3, 3])
    assert [INTERPRETED[w][0][1] for w in ("w71", "w72")] == [[True], [False]]


def test_only_a_list_reading_program_carries_symbols():
    """A compiled program has ``Sym`` items, and the views of its static
    quotations, only when it reads a quotation as a list."""
    from skilark import joy
    assert "Sym sym" not in joy.compiled({"p": "[1 2] i 3 +"})
    assert "Sym sym" in joy.compiled({"p": "[1 2] first"})
    assert "Sym sym" in joy.compiled({"p": "[1 2] size"})


def test_a_program_without_truth_values_keeps_its_compiled_kernel():
    """The compiled form carries ``Logical`` items only for a program that
    uses a truth word, so the terms of every other program, among them
    zk's verifiers, are what they were."""
    from skilark import joy
    assert "Logical logical" not in joy.compiled({"p": "3 4 * 5 +"})
    assert "Logical logical" in joy.compiled({"p": "3 4 <"})
    assert "Logical logical" in joy.compiled({"p": "[true] i"})


# ---------------------------------------------------- the laws, both forms

LAWS = {
    "x y * == y x *":               ("3 4 *", "4 3 *"),
    "x succ pred == x":             ("5 succ pred", "5"),
    "x y max == y x max":           ("3 7 max", "7 3 max"),
    "x y min == y x min":           ("3 7 min", "7 3 min"),
    "x y < == y x >":               ("2 3 <", "3 2 >"),
    "x y != == x y = not":          ("2 3 !=", "2 3 = not"),
    "b not not == b":               ("false not not", "false"),
    "a b and == b a and":           ("true false and", "false true and"),
    "a b or == b a or":             ("true false or", "false true or"),
    "a b and not == a not b not or": ("true false and not", "true not false not or"),
    "true [T] [F] branch == T":     ("true [1 2 +] [5] branch", "1 2 +"),
    "false [T] [F] branch == F":    ("false [1 2 +] [5] branch", "5"),
    "x [P] [T] [F] ifte == x x P [T] [F] branch":
        ("4 [3 <] [1] [2] ifte", "4 dup 3 < [1] [2] branch"),
    "x y - == x y neg +":           ("3 5 -", "3 5 neg +"),
    "x neg neg == x":               ("-4 neg neg", "-4"),
    "x pred succ == x":             ("-2 pred succ", "-2"),
    "x y / y * x y rem + == x":     ("-7 2 / 2 * -7 2 rem +", "-7"),
    "x abs == x sign x *":          ("-3 abs", "-3 sign -3 *"),
    "x y < == x y - 0 <":           ("-3 2 <", "-3 2 - 0 <"),
    "[x A] first == x":             ("[7 8 9] first", "7"),
    "x A cons uncons == x A":       ("1 [2 3] cons uncons", "1 [2 3]"),
    "A B concat size == A size B size +": ("[1 2] [3] concat size", "[1 2] size [3] size +"),
    "A n take A n drop concat == A": ("[1 2 3] 1 take [1 2 3] 1 drop concat", "[1 2 3]"),
    "A unswons swons == A":         ("[4 5] unswons swons", "[4 5]"),
    "[] null == true":              ("[] null", "true"),
}
LAW_PROGRAMS = {f"l{i}{side}": text
                for i, (l, r) in enumerate(LAWS.values())
                for side, text in (("L", l), ("R", r))}


@pytest.fixture(scope="module", params=["interpreted", "compiled"])
def laws(request):
    return (interpreted if request.param == "interpreted" else compiled)(LAW_PROGRAMS)


@pytest.mark.parametrize("i", range(len(LAWS)))
def test_each_law_holds_in_both_forms(laws, i):
    left, right = laws.run(f"ul{i}L")[0], laws.run(f"ul{i}R")[0]
    assert left == right and left[0] == "RVal", list(LAWS)[i]
