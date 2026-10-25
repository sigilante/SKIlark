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
    "w1": (('RVal', [12]), 3_114, 3_123),
    "w2": (('RVal', [6]), 11_103, 11_050),
    "w3": (('RVal', [4]), 11_101, 11_048),
    "w4": (('RVal', [-1]), 11_101, 11_048),
    "w5": (('RVal', [7]), 59_455, 57_831),
    "w6": (('RVal', [3]), 58_441, 56_874),
    "w7": (('RVal', [True]), 2_558, 2_567),
    "w8": (('RVal', [True]), 2_556, 2_565),
    "w9": (('RVal', [False]), 2_556, 2_565),
    "w10": (('RVal', [False]), 45_899, 44_892),
    "w11": (('RVal', [True]), 16_548, 16_383),
    "w12": (('RVal', [True]), 28_052, 27_672),
    "w13": (('RVal', [True]), 3_487, 3_490),
    "w14": (('RVal', [False]), 47_856, 46_803),
    "w15": (('RVal', [True]), 50_267, 49_119),
    "w16": (('RVal', [False]), 1_771, 1_785),
    "w17": (('RVal', [False]), 45_674, 44_712),
    "w18": (('RVal', [False]), 2_558, 2_567),
    "w19": (('RVal', [1]), 4_755, 4_751),
    "w20": (('RVal', [2]), 4_749, 4_745),
    "w21": (('RVal', [1, 2]), 9_131, 9_085),
    "w22": (('RVal', [4, 2]), 10_596, 10_550),
    "w23": (('RVal', [120]), 210_359, 196_037),
    "w24": (('RVal', [True]), 2_558, 2_567),
    "w25": (('RVal', [2]), 4_791, 4_787),
    "w26": (('RErr', None), 3_048, 3_062),
    "w27": (('RVal', [-2]), 3_116, 3_125),
    "w28": (('RVal', [3]), 4_000, 4_003),
    "w29": (('RVal', [3]), 14_188, 14_077),
    "w30": (('RVal', [-1]), 12_603, 12_508),
    "w31": (('RVal', [0]), 16_846, 16_681),
    "w32": (('RVal', [1]), 17_242, 17_077),
    "w33": (('RVal', [3]), 3_164, 3_173),
    "w34": (('RVal', [-3]), 3_164, 3_173),
    "w35": (('RVal', [-3]), 3_160, 3_169),
    "w36": (('RVal', [-1]), 3_162, 3_171),
    "w37": (('RVal', [1]), 3_158, 3_167),
    "w38": (('RErr', None), 3_084, 3_098),
    "w39": (('RVal', [-6]), 3_114, 3_123),
    "w40": (('RVal', [6]), 3_114, 3_123),
    "w41": (('RVal', [True]), 2_556, 2_565),
    "w42": (('RVal', [True]), 2_556, 2_565),
    "w43": (('RVal', [0]), 11_103, 11_050),
    "w44": (('RVal', [True]), 2_558, 2_567),
    "w45": (('RVal', [1]), 58_537, 56_913),
    "w46": (('RVal', [-1]), 3_118, 3_127),
    "w47": (('RVal', [[('Lit', -1)]]), 1_672, 1_686),
    "w48": (('RVal', [10]), 168_017, 158_187),
    "w49": (('RVal', [1]), 2_633, 2_642),
    "w50": (('RVal', [[('Lit', 2), ('Lit', 3)]]), 3_522, 3_525),
    "w51": (('RVal', [1, [('Lit', 2), ('Lit', 3)]]), 1_825, 1_839),
    "w52": (('RVal', [[('Lit', 2), ('Lit', 3)], 1]), 2_711, 2_720),
    "w53": (('RVal', [True]), 1_645, 1_659),
    "w54": (('RVal', [False]), 1_645, 1_659),
    "w55": (('RVal', [True]), 1_645, 1_659),
    "w56": (('RVal', [True]), 1_787, 1_801),
    "w57": (('RVal', [False]), 1_787, 1_801),
    "w58": (('RVal', [True]), 1_789, 1_803),
    "w59": (('RVal', [False]), 1_789, 1_803),
    "w60": (('RVal', [3]), 2_031, 2_045),
    "w61": (('RVal', [0]), 2_031, 2_045),
    "w62": (('RVal', [('Sym', 'dup')]), 2_633, 2_642),
    "w63": (('RVal', [3, 3]), 6_343, 6_322),
    "w64": (('RVal', [4]), 4_072, 4_075),
    "w65": (('RVal', [3]), 5_929, 5_925),
    "w66": (('RVal', [[('Lit', 1), ('Lit', 2)]]), 354_102, 311_086),
    "w67": (('RVal', [[('Lit', 3), ('Lit', 4)]]), 165_874, 154_740),
    "w68": (('RVal', [[('Lit', 1), ('Lit', 2)]]), 243_394, 221_499),
    "w69": (('RVal', [[]]), 164_970, 154_133),
    "w70": (('RErr', None), 1_742, 1_760),
    "w71": (('RVal', [True]), 6_141, 6_120),
    "w72": (('RVal', [False]), 6_141, 6_120),
    "w73": (('RVal', [[('Lit', 0), ('Lit', 1), ('Lit', 2)]]), 3_585, 3_588),
    "w74": (('RVal', [2]), 3_984, 3_987),
    "w75": (('RVal', [3]), 4_412, 4_415),
    "w76": (('RVal', [3]), 3_528, 3_537),
    "w77": (('RVal', [1, [('Lit', 2), ('Lit', 3)]]), 3_916, 3_919),
    "w78": (('RVal', [True]), 2_633, 2_642),
    "w79": (('RVal', [1]), 4_696, 4_692),
    "w80": (('RVal', [2]), 4_072, 4_075),
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
    "w23": (('RVal', [120]), 120_411, 119_413),
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
    "w48": (('RVal', [10]), 95_830, 95_143),
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
    "w65": (('RVal', [3]), 90_899, 90_648),
    "w66": (('RVal', [('quot', ('RVal', [1, 2]))]), 207_809, 206_176),
    "w67": (('RVal', [('quot', ('RVal', [3, 4]))]), 80_919, 80_668),
    "w68": (('RVal', [('quot', ('RVal', [1, 2]))]), 127_631, 126_987),
    "w69": (('RVal', [('quot', ('RVal', []))]), 82_659, 82_408),
    "w70": (('RErr', None), 670, 670),
    "w71": (('RVal', [True]), 1_654, 1_654),
    "w72": (('RVal', [False]), 1_590, 1_590),
    "w73": (('RVal', [('quot', ('RVal', [0, 1, 2]))]), 320, 320),
    "w74": (('RVal', [2]), 43_857, 43_667),
    "w75": (('RVal', [3]), 56_110, 56_031),
    "w76": (('RVal', [3]), 55_975, 55_896),
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
