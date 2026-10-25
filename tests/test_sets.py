"""Joy's stage 6, step 3: sets (PLAN.md §3, stage 6).  A set is its
members, the integers 0 to 63, ascending; the kernel's words take sets
as the reference's do, its ``not`` is the complement, and the derived
``and or xor`` are the set operations made of it; ``<`` is the subset
order when either value is a set, and ``=`` compares a set with a number
by its 64 bits; in both forms.  Each program is compiled alone.  Every
count was measured on skijack 0.2.1.
"""

import pytest

from skilark import compiled, interpreted, joy

PROGRAMS = {
    "s1": '{3 1 2}',
    "s2": '{}',
    "s3": '{1 2} typeof',
    "s4": '{1 2} set',
    "s5": '[1 2] set',
    "s6": '{3 1} first',
    "s7": '{3 1} rest',
    "s8": '{3 1} uncons',
    "s9": '{} first',
    "s10": '{1 2} 3 swap cons',
    "s11": '5 {1 2} cons',
    "s12": '{} 63 swap cons',
    "s13": '{} 64 swap cons',
    "s14": '{} -1 swap cons',
    "s15": "{} 'a swap cons",
    "s16": "{} '\\001 swap cons",
    "s17": '{} true swap cons',
    "s18": '{1 2} {2 3} concat',
    "s19": '{1 2} [3] concat',
    "s20": '{1 2 3} size',
    "s21": '{} null',
    "s22": '{1} null',
    "s23": '{1} small',
    "s24": '{1 2} small',
    "s25": '{1 2 3} 1 at',
    "s26": '{1 2 3} 5 at',
    "s27": '{1 2 3} 2 take',
    "s28": '{1 2 3} 2 drop',
    "s29": '{1 2 3} true take',
    "s30": '{1 2} {2 3} and',
    "s31": '{1 2} {2 3} or',
    "s32": '{1 2} {2 3} xor',
    "s33": '{1 2} not first',
    "s34": '{} not 63 has',
    "s35": '{1 2} not 1 has',
    "s36": '{1 2} true and',
    "s37": '{1 2} 2 has',
    "s38": '{1 2} 5 has',
    "s39": '2 {1 2} in',
    "s40": "{1 2} 'a has",
    "s41": '{1 2} {1 2} =',
    "s42": '{1 2} {1 3} =',
    "s43": '{0} 1 =',
    "s44": '{0 1} 3 =',
    "s45": '{} 0 =',
    "s46": '{} [] =',
    "s47": '{1} {1 2} <',
    "s48": '{1 2} {1 2} <',
    "s49": '{0} {1} <',
    "s50": '{0} {1} >',
    "s51": '{0} {1} >=',
    "s52": '{0} {1} <=',
    "s53": '{1 2} {1} >',
    "s54": '{1 2} {1} >=',
    "s55": '{1} 3 <',
    "s56": '3 {0 1} >',
    "s57": '{1 2} [succ] map',
    "s58": '{1 2} [0 =] map',
    "s59": '{1 2 3} [2 <] filter',
    "s60": '{1 2 3} 0 [+] fold',
    "s61": '0 {1 2 3} [+] step',
    "s62": '{1 2 3} [0] [+] primrec',
    "s63": '{1 2} [1] [2] branch',
    "s64": '{} [1] [2] branch',
    "s65": '{1} {2} sametype',
    "s66": '{1} [1] sametype',
    "s67": '{1 2} succ',
    "s68": '{1 2} [] cons',
    "s69": '[{1 2}] first',
    "s70": '{1 2} unit',
    "s71": '{1 2} [1] dip',
    "s72": '{1 2} 3 stack',
    "s73": '{1} max',
}

#: outcome, then host contractions unfuelled (uP) and fuelled (rP)
INTERPRETED = {
    "s1": (('RVal', [('Set', (1, 2, 3))]), 856, 874),
    "s2": (('RVal', [('Set', ())]), 856, 874),
    "s3": (('RVal', [7]), 1_631, 1_645),
    "s4": (('RVal', [True]), 3_334, 3_337),
    "s5": (('RVal', [False]), 3_334, 3_337),
    "s6": (('RVal', [1]), 2_623, 2_632),
    "s7": (('RVal', [('Set', (3,))]), 3_512, 3_515),
    "s8": (('RVal', [1, ('Set', (3,))]), 1_815, 1_829),
    "s9": (('RErr', None), 1_732, 1_750),
    "s10": (('RVal', [('Set', (1, 2, 3))]), 6_474, 6_477),
    "s11": (('RVal', [('Set', (1, 2, 5))]), 6_382, 6_391),
    "s12": (('RVal', [('Set', (63,))]), 26_941, 26_944),
    "s13": (('RErr', None), 26_975, 26_984),
    "s14": (('RErr', None), 3_795, 3_804),
    "s15": (('RErr', None), 26_967, 26_976),
    "s16": (('RVal', [('Set', (1,))]), 5_706, 5_709),
    "s17": (('RErr', None), 3_714, 3_723),
    "s18": (('RVal', [('Set', (1, 2, 3))]), 2_741, 2_750),
    "s19": (('RErr', None), 2_810, 2_824),
    "s20": (('RVal', [3]), 2_021, 2_035),
    "s21": (('RVal', [True]), 1_645, 1_659),
    "s22": (('RVal', [False]), 1_645, 1_659),
    "s23": (('RVal', [True]), 1_777, 1_791),
    "s24": (('RVal', [False]), 1_777, 1_791),
    "s25": (('RVal', [2]), 3_518, 3_527),
    "s26": (('RErr', None), 3_669, 3_683),
    "s27": (('RVal', [('Set', (1, 2))]), 302_229, 270_406),
    "s28": (('RVal', [('Set', (3,))]), 165_694, 154_560),
    "s29": (('RVal', [('Set', (1,))]), 305_025, 271_669),
    "s30": (('RVal', [('Set', (2,))]), 31_767, 31_233),
    "s31": (('RVal', [('Set', (1, 2, 3))]), 27_762, 27_353),
    "s32": (('RVal', [('Set', (1, 3))]), 56_872, 55_190),
    "s33": (('RVal', [0]), 4_350, 4_353),
    "s34": (('RVal', [True]), 45_245, 44_971),
    "s35": (('RVal', [False]), 24_018, 23_744),
    "s36": (('RErr', None), 20_811, 20_584),
    "s37": (('RVal', [True]), 23_462, 23_212),
    "s38": (('RVal', [False]), 24_638, 24_388),
    "s39": (('RVal', [True]), 24_366, 24_092),
    "s40": (('RErr', None), 43_329, 43_119),
    "s41": (('RVal', [True]), 2_558, 2_567),
    "s42": (('RVal', [False]), 2_558, 2_567),
    "s43": (('RVal', [True]), 2_558, 2_567),
    "s44": (('RVal', [True]), 2_558, 2_567),
    "s45": (('RVal', [True]), 2_558, 2_567),
    "s46": (('RVal', [True]), 2_558, 2_567),
    "s47": (('RVal', [True]), 2_556, 2_565),
    "s48": (('RVal', [False]), 2_556, 2_565),
    "s49": (('RVal', [False]), 2_556, 2_565),
    "s50": (('RVal', [False]), 27_072, 26_633),
    "s51": (('RVal', [False]), 42_810, 41_803),
    "s52": (('RVal', [False]), 16_209, 16_044),
    "s53": (('RVal', [True]), 27_072, 26_633),
    "s54": (('RVal', [True]), 45_036, 43_936),
    "s55": (('RVal', [True]), 2_556, 2_565),
    "s56": (('RVal', [False]), 27_072, 26_633),
    "s57": (('RVal', [('Set', (2, 3))]), 436_152, 373_030),
    "s58": (('RVal', [('Set', (0,))]), 417_406, 357_095),
    "s59": (('RVal', [('Set', (1,))]), 493_056, 412_519),
    "s60": (('RVal', [6]), 245_898, 220_974),
    "s61": (('RVal', [6]), 241_370, 217_331),
    "s62": (('RVal', [6]), 380_932, 331_855),
    "s63": (('RVal', [1]), 4_771, 4_767),
    "s64": (('RVal', [2]), 4_745, 4_741),
    "s65": (('RVal', [True]), 12_991, 12_896),
    "s66": (('RVal', [False]), 13_011, 12_916),
    "s67": (('RErr', None), 10_998, 10_952),
    "s68": (('RVal', [[('Set', (1, 2))]]), 2_702, 2_711),
    "s69": (('RVal', [('Set', (1, 2))]), 2_633, 2_642),
    "s70": (('RVal', [[('Set', (1, 2))]]), 1_672, 1_686),
    "s71": (('RVal', [1, ('Set', (1, 2))]), 4_450, 4_446),
    "s72": (('RVal', [('Set', (1, 2)), 3, [('Lit', 3), ('Set', (1, 2))]]), 2_424, 2_433),
    "s73": (('RErr', None), 3_495, 3_504),
}
COMPILED = {
    "s1": (('RVal', [('Set', (1, 2, 3))]), 7, 7),
    "s2": (('RVal', [('Set', ())]), 7, 7),
    "s3": (('RVal', [7]), 82, 82),
    "s4": (('RVal', [True]), 240, 240),
    "s5": (('RVal', [False]), 240, 240),
    "s6": (('RVal', [1]), 228, 228),
    "s7": (('RVal', [('Set', (3,))]), 351, 351),
    "s8": (('RVal', [1, ('Set', (3,))]), 151, 151),
    "s9": (('RErr', None), 154, 154),
    "s10": (('RVal', [('Set', (1, 2, 3))]), 2_031, 2_031),
    "s11": (('RVal', [('Set', (1, 2, 5))]), 2_595, 2_595),
    "s12": (('RVal', [('Set', (63,))]), 19_198, 19_198),
    "s13": (('RErr', None), 19_290, 19_290),
    "s14": (('RErr', None), 432, 432),
    "s15": (('RErr', None), 19_324, 19_324),
    "s16": (('RVal', [('Set', (1,))]), 1_415, 1_415),
    "s17": (('RErr', None), 384, 384),
    "s18": (('RVal', [('Set', (1, 2, 3))]), 240, 240),
    "s19": (('RErr', None), 263, 263),
    "s20": (('RVal', [3]), 18_331, 17_997),
    "s21": (('RVal', [True]), 82, 82),
    "s22": (('RVal', [False]), 82, 82),
    "s23": (('RVal', [True]), 121, 121),
    "s24": (('RVal', [False]), 121, 121),
    "s25": (('RVal', [2]), 30_224, 30_145),
    "s26": (('RErr', None), 60_305, 59_838),
    "s27": (('RVal', [('Set', (1, 2))]), 115_246, 114_187),
    "s28": (('RVal', [('Set', (3,))]), 43_619, 43_368),
    "s29": (('RVal', [('Set', (1,))]), 124_596, 123_443),
    "s30": (('RVal', [('Set', (2,))]), 6_257, 6_313),
    "s31": (('RVal', [('Set', (1, 2, 3))]), 5_621, 5_677),
    "s32": (('RVal', [('Set', (1, 3))]), 10_318, 10_362),
    "s33": (('RVal', [0]), 1_135, 1_135),
    "s34": (('RVal', [True]), 24_167, 24_192),
    "s35": (('RVal', [False]), 6_350, 6_375),
    "s36": (('RErr', None), 3_808, 3_850),
    "s37": (('RVal', [True]), 6_546, 6_571),
    "s38": (('RVal', [False]), 7_557, 7_582),
    "s39": (('RVal', [True]), 6_668, 6_693),
    "s40": (('RErr', None), 24_287, 24_312),
    "s41": (('RVal', [True]), 165, 165),
    "s42": (('RVal', [False]), 165, 165),
    "s43": (('RVal', [True]), 165, 165),
    "s44": (('RVal', [True]), 165, 165),
    "s45": (('RVal', [True]), 165, 165),
    "s46": (('RVal', [True]), 165, 165),
    "s47": (('RVal', [True]), 165, 165),
    "s48": (('RVal', [False]), 165, 165),
    "s49": (('RVal', [False]), 165, 165),
    "s50": (('RVal', [False]), 4_300, 4_356),
    "s51": (('RVal', [False]), 6_608, 6_655),
    "s52": (('RVal', [False]), 2_518, 2_560),
    "s53": (('RVal', [True]), 4_300, 4_356),
    "s54": (('RVal', [True]), 6_780, 6_827),
    "s55": (('RVal', [True]), 165, 165),
    "s56": (('RVal', [False]), 4_300, 4_356),
    "s57": (('RVal', [('Set', (2, 3))]), 191_151, 187_761),
    "s58": (('RVal', [('Set', (0,))]), 189_324, 185_932),
    "s59": (('RVal', [('Set', (1,))]), 252_185, 245_981),
    "s60": (('RVal', [6]), 74_597, 73_493),
    "s61": (('RVal', [6]), 73_696, 72_578),
    "s62": (('RVal', [6]), 150_661, 147_976),
    "s63": (('RVal', [1]), 596, 610),
    "s64": (('RVal', [2]), 570, 584),
    "s65": (('RVal', [True]), 1_883, 1_897),
    "s66": (('RVal', [False]), 1_905, 1_919),
    "s67": (('RErr', None), 1_730, 1_744),
    "s68": (('RVal', [('quot', ('RVal', [('Set', (1, 2))]))]), 212, 212),
    "s69": (('RVal', [('Set', (1, 2))]), 267, 267),
    "s70": (('RVal', [('quot', ('RVal', [('Set', (1, 2))]))]), 82, 82),
    "s71": (('RVal', [1, ('Set', (1, 2))]), 379, 393),
    "s72": (('RVal', [('Set', (1, 2)), 3, ('quot', ('RVal', [3, ('Set', (1, 2))]))]), 103, 103),
    "s73": (('RErr', None), 565, 579),
}


@pytest.fixture(scope="module")
def interp():
    return interpreted(PROGRAMS)


@pytest.mark.parametrize("name", sorted(PROGRAMS))
def test_interpreted_sets(interp, name):
    outcome, unfuelled, fuelled = INTERPRETED[name]
    assert interp.run("u" + name) == (outcome, unfuelled), PROGRAMS[name]
    assert interp.run("r" + name) == (outcome, fuelled), PROGRAMS[name]


@pytest.mark.parametrize("name", sorted(PROGRAMS))
def test_compiled_sets(name):
    comp = compiled({name: PROGRAMS[name]})
    outcome, unfuelled, fuelled = COMPILED[name]
    assert comp.run("u" + name) == (outcome, unfuelled), PROGRAMS[name]
    assert comp.run("r" + name) == (outcome, fuelled), PROGRAMS[name]


def test_a_set_literal_is_read_as_the_reference_reads_it():
    """factor.c list2set: integers and characters 0 to 63, in any order
    and with repeats; anything else is the reader's error."""
    assert joy.parse("{3 1 3 '\\001}") == [("Z", (1, 3))]
    for bad in ("{64}", "{-1}", "{[1]}", "{true}", "{1]", "{1"):
        with pytest.raises(ValueError):
            joy.parse(bad)


def test_the_complement_is_the_kernels_not():
    """not is a kernel word: logical negation of a number, a character or
    a truth value, the complement of a set, an error otherwise."""
    assert joy.KERNEL["not"] == "Not" and "not" not in joy.DEFINITIONS
    assert INTERPRETED["s33"][0] == COMPILED["s33"][0] == ("RVal", [0])


def test_a_program_without_a_set_keeps_its_compiled_kernel():
    """The compiled form has sets only where a program has a set literal,
    which alone makes a set, and takes the set words without their set
    branches elsewhere, so every other program, zk's verifiers among
    them, compiles as before."""
    assert "Set set" not in joy.compiled({"p": "[1 2] 1 has 3 2 > and"})
    assert "Set set" in joy.compiled({"p": "{1}"})


# ---------------------------------------------------- the laws, both forms

LAWS = {
    "S not not == S":                     ("{1 2} not not", "{1 2}"),
    "S T and == T S and":                 ("{1 2} {2 3} and", "{2 3} {1 2} and"),
    "S T or not == S not T not and":      ("{1} {2} or not", "{1} not {2} not and"),
    "S T xor == S T or S T and not and":  ("{1 2} {2 3} xor", "{1 2} {2 3} or {1 2} {2 3} and not and"),
    "S first S rest cons == S":           ("{3 1} first {3 1} rest cons", "{3 1}"),
    "S n take S n drop concat == S":      ("{1 2 3} 2 take {1 2 3} 2 drop concat", "{1 2 3}"),
    "x S cons x has":                     ("5 {1} cons 5 has", "true"),
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
