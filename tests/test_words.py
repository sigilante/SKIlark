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
    "w1": (('RVal', [12]), 2_768, 2_770),
    "w2": (('RVal', [6]), 2_772, 2_774),
    "w3": (('RVal', [4]), 2_770, 2_772),
    "w4": (('RVal', [-1]), 2_770, 2_772),
    "w5": (('RVal', [7]), 23_371, 22_925),
    "w6": (('RVal', [3]), 22_483, 22_067),
    "w7": (('RVal', [True]), 2_294, 2_296),
    "w8": (('RVal', [True]), 2_292, 2_294),
    "w9": (('RVal', [False]), 2_292, 2_294),
    "w10": (('RVal', [False]), 15_988, 15_771),
    "w11": (('RVal', [True]), 14_460, 14_288),
    "w12": (('RVal', [True]), 8_576, 8_516),
    "w13": (('RVal', [True]), 8_531, 8_471),
    "w14": (('RVal', [False]), 28_594, 27_948),
    "w15": (('RVal', [True]), 30_272, 29_551),
    "w16": (('RVal', [False]), 6_554, 6_516),
    "w17": (('RVal', [False]), 16_451, 16_217),
    "w18": (('RVal', [False]), 2_294, 2_296),
    "w19": (('RVal', [1]), 4_254, 4_243),
    "w20": (('RVal', [2]), 4_248, 4_237),
    "w21": (('RVal', [1, 2]), 8_168, 8_115),
    "w22": (('RVal', [4, 2]), 8_706, 8_653),
    "w23": (('RVal', [120]), 140_118, 131_106),
    "w24": (('RVal', [True]), 2_294, 2_296),
    "w25": (('RVal', [2]), 4_290, 4_279),
    "w26": (('RErr', None), 2_702, 2_709),
    "w27": (('RVal', [-2]), 2_770, 2_772),
    "w28": (('RVal', [3]), 3_570, 3_566),
    "w29": (('RVal', [3]), 12_560, 12_442),
    "w30": (('RVal', [-1]), 11_141, 11_039),
    "w31": (('RVal', [0]), 15_019, 14_847),
    "w32": (('RVal', [1]), 15_329, 15_157),
    "w33": (('RVal', [3]), 2_818, 2_820),
    "w34": (('RVal', [-3]), 2_818, 2_820),
    "w35": (('RVal', [-3]), 2_814, 2_816),
    "w36": (('RVal', [-1]), 2_816, 2_818),
    "w37": (('RVal', [1]), 2_812, 2_814),
    "w38": (('RErr', None), 2_738, 2_745),
    "w39": (('RVal', [-6]), 2_768, 2_770),
    "w40": (('RVal', [6]), 2_768, 2_770),
    "w41": (('RVal', [True]), 2_292, 2_294),
    "w42": (('RVal', [True]), 2_292, 2_294),
    "w43": (('RVal', [0]), 2_772, 2_774),
    "w44": (('RVal', [True]), 2_294, 2_296),
    "w45": (('RVal', [1]), 23_155, 22_709),
    "w46": (('RVal', [-1]), 2_772, 2_774),
    "w47": (('RVal', [[('Lit', -1)]]), 1_498, 1_505),
    "w48": (('RVal', [10]), 114_271, 107_974),
    "w49": (('RVal', [1]), 2_354, 2_356),
    "w50": (('RVal', [[('Lit', 2), ('Lit', 3)]]), 3_159, 3_155),
    "w51": (('RVal', [1, [('Lit', 2), ('Lit', 3)]]), 1_630, 1_637),
    "w52": (('RVal', [[('Lit', 2), ('Lit', 3)], 1]), 2_432, 2_434),
    "w53": (('RVal', [True]), 1_471, 1_478),
    "w54": (('RVal', [False]), 1_471, 1_478),
    "w55": (('RVal', [True]), 1_471, 1_478),
    "w56": (('RVal', [True]), 1_592, 1_599),
    "w57": (('RVal', [False]), 1_592, 1_599),
    "w58": (('RVal', [True]), 1_594, 1_601),
    "w59": (('RVal', [False]), 1_594, 1_601),
    "w60": (('RVal', [3]), 76_538, 73_237),
    "w61": (('RVal', [0]), 22_330, 21_971),
    "w62": (('RVal', [('Sym', 'dup')]), 2_354, 2_356),
    "w63": (('RVal', [3, 3]), 5_683, 5_655),
    "w64": (('RVal', [4]), 97_586, 92_453),
    "w65": (('RVal', [3]), 210_405, 188_078),
    "w66": (('RVal', [[('Lit', 1), ('Lit', 2)]]), 538_391, 427_306),
    "w67": (('RVal', [[('Lit', 3), ('Lit', 4)]]), 205_868, 184_383),
    "w68": (('RVal', [[('Lit', 1), ('Lit', 2)]]), 325_105, 277_266),
    "w69": (('RVal', [[]]), 208_459, 186_557),
    "w70": (('RErr', None), 1_547, 1_558),
    "w71": (('RVal', [True]), 5_499, 5_471),
    "w72": (('RVal', [False]), 5_499, 5_471),
    "w73": (('RVal', [[('Lit', 0), ('Lit', 1), ('Lit', 2)]]), 3_216, 3_212),
    "w74": (('RVal', [2]), 60_440, 58_318),
    "w75": (('RVal', [3]), 139_033, 128_336),
    "w76": (('RVal', [3]), 138_085, 127_534),
    "w77": (('RVal', [1, [('Lit', 2), ('Lit', 3)]]), 3_496, 3_492),
    "w78": (('RVal', [True]), 2_354, 2_356),
    "w79": (('RVal', [1]), 4_192, 4_181),
    "w80": (('RVal', [2]), 60_330, 58_208),
}
COMPILED = {
    "w1": (('RVal', [12]), 427, 427),
    "w2": (('RVal', [6]), 427, 427),
    "w3": (('RVal', [4]), 427, 427),
    "w4": (('RVal', [-1]), 427, 427),
    "w5": (('RVal', [7]), 9_034, 9_090),
    "w6": (('RVal', [3]), 8_915, 8_971),
    "w7": (('RVal', [True]), 165, 165),
    "w8": (('RVal', [True]), 165, 165),
    "w9": (('RVal', [False]), 165, 165),
    "w10": (('RVal', [False]), 6_545, 6_587),
    "w11": (('RVal', [True]), 6_495, 6_537),
    "w12": (('RVal', [True]), 2_878, 2_892),
    "w13": (('RVal', [True]), 2_831, 2_845),
    "w14": (('RVal', [False]), 11_166, 11_236),
    "w15": (('RVal', [True]), 11_248, 11_318),
    "w16": (('RVal', [False]), 2_264, 2_278),
    "w17": (('RVal', [False]), 5_192, 5_220),
    "w18": (('RVal', [False]), 165, 165),
    "w19": (('RVal', [1]), 1_961, 1_975),
    "w20": (('RVal', [2]), 1_955, 1_969),
    "w21": (('RVal', [1, 2]), 3_786, 3_814),
    "w22": (('RVal', [4, 2]), 4_285, 4_313),
    "w23": (('RVal', [120]), 96_714, 95_815),
    "w24": (('RVal', [True]), 165, 165),
    "w25": (('RVal', [2]), 1_995, 2_009),
    "w26": (('RErr', None), 415, 415),
    "w27": (('RVal', [-2]), 427, 427),
    "w28": (('RVal', [3]), 545, 545),
    "w29": (('RVal', [3]), 3_543, 3_557),
    "w30": (('RVal', [-1]), 3_122, 3_136),
    "w31": (('RVal', [0]), 5_122, 5_133),
    "w32": (('RVal', [1]), 5_474, 5_485),
    "w33": (('RVal', [3]), 471, 471),
    "w34": (('RVal', [-3]), 471, 471),
    "w35": (('RVal', [-3]), 467, 467),
    "w36": (('RVal', [-1]), 471, 471),
    "w37": (('RVal', [1]), 467, 467),
    "w38": (('RErr', None), 447, 447),
    "w39": (('RVal', [-6]), 427, 427),
    "w40": (('RVal', [6]), 427, 427),
    "w41": (('RVal', [True]), 165, 165),
    "w42": (('RVal', [True]), 165, 165),
    "w43": (('RVal', [0]), 427, 427),
    "w44": (('RVal', [True]), 165, 165),
    "w45": (('RVal', [1]), 8_818, 8_874),
    "w46": (('RVal', [-1]), 427, 427),
    "w47": (('RVal', [('quot', ('RVal', [-1]))]), 82, 82),
    "w48": (('RVal', [10]), 78_967, 78_344),
    "w49": (('RVal', [1]), 692, 692),
    "w50": (('RVal', [('quot', ('RVal', [2, 3]))]), 813, 813),
    "w51": (('RVal', [1, ('quot', ('RVal', [2, 3]))]), 615, 615),
    "w52": (('RVal', [('quot', ('RVal', [2, 3])), 1]), 734, 734),
    "w53": (('RVal', [True]), 82, 82),
    "w54": (('RVal', [False]), 82, 82),
    "w55": (('RVal', [True]), 82, 82),
    "w56": (('RVal', [True]), 136, 136),
    "w57": (('RVal', [False]), 136, 136),
    "w58": (('RVal', [True]), 138, 138),
    "w59": (('RVal', [False]), 138, 138),
    "w60": (('RVal', [3]), 56_718, 56_384),
    "w61": (('RVal', [0]), 14_195, 14_180),
    "w62": (('RVal', [('Sym', 'dup')]), 686, 686),
    "w63": (('RVal', [3, 3]), 4_272, 4_283),
    "w64": (('RVal', [4]), 81_556, 81_063),
    "w65": (('RVal', [3]), 105_284, 104_866),
    "w66": (('RVal', [('quot', ('RVal', [1, 2]))]), 232_370, 230_382),
    "w67": (('RVal', [('quot', ('RVal', [3, 4]))]), 93_717, 93_299),
    "w68": (('RVal', [('quot', ('RVal', [1, 2]))]), 141_087, 140_287),
    "w69": (('RVal', [('quot', ('RVal', []))]), 94_633, 94_215),
    "w70": (('RErr', None), 644, 644),
    "w71": (('RVal', [True]), 1_642, 1_642),
    "w72": (('RVal', [False]), 1_578, 1_578),
    "w73": (('RVal', [('quot', ('RVal', [0, 1, 2]))]), 338, 338),
    "w74": (('RVal', [2]), 43_215, 43_025),
    "w75": (('RVal', [3]), 63_511, 63_321),
    "w76": (('RVal', [3]), 63_383, 63_193),
    "w77": (('RVal', [1, ('quot', ('RVal', [2, 3]))]), 2_698, 2_698),
    "w78": (('RVal', [True]), 666, 666),
    "w79": (('RVal', [1]), 3_247, 3_247),
    "w80": (('RVal', [2]), 50_962, 50_772),
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
