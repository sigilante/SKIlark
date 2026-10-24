"""Joy's stage 7: the reference's library words SKIlark had not yet
(PLAN.md §3, stage 7): ``rollupd rolldownd rotated choice setsize
enconcat``, the n-ary combinators ``app1 app11 app12 unary unary2 unary3
unary4 app2 app3 app4 binary ternary cleave construct``, the type
conditionals ``ifinteger`` ... ``iffile``, ``cond case opcase split some
all equal`` and the tree combinators ``treestep treerec treegenrec``; all
derived, in both forms.  Each program is compiled alone.  Every count was
measured on skijack 0.2.1.
"""

import pytest

from skilark import compiled, interpreted

PROGRAMS = {
    "b1": '1 2 3 4 rollupd',
    "b2": '1 2 3 4 rolldownd',
    "b3": '1 2 3 4 rotated',
    "b4": '1 2 3 rollupd',
    "b5": 'true 1 2 choice',
    "b6": '0 1 2 choice',
    "b7": '[] 1 2 choice',
    "b8": '1 2 choice',
    "b9": 'setsize',
    "b10": '3 [1] [2] enconcat',
    "b11": '\'c "ab" "de" enconcat',
    "b12": '3 [1] "a" enconcat',
    "b13": '5 [dup *] app1',
    "b14": '[1] app1',
    "b15": '1 5 [+] app11',
    "b16": '1 2 3 [+] app12',
    "b17": '1 2 3 [dup +] app12',
    "b18": '10 3 [dup +] unary',
    "b19": '10 3 4 [+] binary',
    "b20": '10 3 4 5 [+ +] ternary',
    "b21": '3 [pop pop] unary',
    "b22": '1 2 3 [dup *] unary2',
    "b23": '1 2 3 [+] unary2',
    "b24": '1 2 3 4 [+] unary3',
    "b25": '1 2 3 4 5 [dup *] unary4',
    "b26": '1 2 3 [dup *] app2',
    "b27": '2 3 [dup *] unary2',
    "b28": '1 2 3 4 [dup *] app3',
    "b29": '5 [1 +] [2 *] cleave',
    "b31": '1 [2 3] [[+] [*] [-]] construct',
    "b33": "3 ['a] ['b] ifinteger",
    "b34": "'x ['a] ['b] ifinteger",
    "b35": "'x [1] [2] ifchar",
    "b36": 'true [1] [2] iflogical',
    "b37": '{1} [1] [2] ifset',
    "b38": '"s" [1] [2] ifstring',
    "b39": '[] [1] [2] iflist',
    "b40": '1 [1] [2] iffloat',
    "b41": '1 [1] [2] iffile',
    "b42": '5 [[[0 =] "zero"] [[0 >] "pos"] ["neg"]] cond',
    "b43": '0 [[[0 =] "zero"] [[0 >] "pos"] ["neg"]] cond',
    "b44": '-3 [[[0 =] "zero"] [[0 >] "pos"] ["neg"]] cond',
    "b45": '1 [[2]] cond',
    "b46": '1 [] cond',
    "b47": '1 [[1 2]] cond',
    "b48": '2 [[1 "one"] [2 "two"] ["other"]] case',
    "b49": '5 [[1 "one"] [2 "two"] ["other"]] case',
    "b50": "'a [['a 1] [2]] case",
    "b51": '2 [[1 "one"] [2 "two"]] case',
    "b52": '3 [[1 "one"] [2 "two"]] case',
    "b53": '2 [] case',
    "b54": '3 [[0 integer] [\'a char] ["other"]] opcase',
    "b55": '\'z [[0 integer] [\'a char] ["other"]] opcase',
    "b56": '[1] [[0 integer] [\'a char] ["other"]] opcase',
    "b57": '[dup] first [[[dup] first "is-dup"] [[swap] first "is-swap"] ["none"]] opcase',
    "b58": '[1 2 3 4] [2 rem 0 =] split',
    "b59": '"abcd" [\'b >] split',
    "b60": '{1 2 3} [2 <] split',
    "b61": '[] [1 +] split',
    "b62": '5 [1 +] split',
    "b63": '[1 2 3] [2 >] some',
    "b64": '[1 2 3] [5 >] some',
    "b65": '[1 [] 2] [1 =] some',
    "b66": '[] [pop true] some',
    "b67": '[1 2 3] [0 >] all',
    "b68": '[1 2 3] [1 >] all',
    "b69": '[1 [] 3] [1 >] all',
    "b70": '[] [pop false] all',
    "b71": '{1 2} [0 >] all',
    "b72": '"ab" [\'a =] some',
    "b73": '[1 [2 3]] [1 [2 3]] equal',
    "b74": '[1 [2 3]] [1 [2 4]] equal',
    "b75": '[1 2] [1 2 3] equal',
    "b76": '[] 0 equal',
    "b77": '3 3 equal',
    "b78": '[1 [2 3]] [dup *] treestep',
    "b79": '[[1 2] [3 [4]]] 0 swap [+] treestep',
    "b80": '5 [dup *] treestep',
    "b81": '[1 [2 3]] [dup *] [map] treerec',
    "b82": '3 [dup *] [map] treerec',
    "b83": '[1 [2 3]] [dup *] [] [map] treegenrec',
    "b84": '[dup] first unit [dup] first has',
    "b85": '[size] first [{2}] in',
}

#: outcome, then host contractions unfuelled (uP) and fuelled (rP)
INTERPRETED = {
    "b1": (('RVal', [3, 1, 2, 4]), 11_425, 11_330),
    "b2": (('RVal', [2, 3, 1, 4]), 11_431, 11_336),
    "b3": (('RVal', [3, 2, 1, 4]), 12_364, 12_253),
    "b4": (('RErr', None), 8_766, 8_720),
    "b5": (('RVal', [1]), 21_303, 20_978),
    "b6": (('RVal', [2]), 22_269, 21_917),
    "b7": (('RVal', [2]), 22_245, 21_893),
    "b8": (('RErr', None), 5_085, 5_081),
    "b9": (('RVal', [64]), 826, 844),
    "b10": (('RVal', [[('Lit', 1), ('Lit', 3), ('Lit', 2)]]), 23_354, 23_002),
    "b11": (('RVal', [('Str', 'abcde')]), 23_264, 22_912),
    "b12": (('RErr', None), 20_347, 20_097),
    "b13": (('RVal', [25]), 13_795, 13_684),
    "b14": (('RErr', None), 8_717, 8_686),
    "b15": (('RErr', None), 25_323, 24_943),
    "b16": (('RVal', [3, 4]), 152_405, 141_271),
    "b17": (('RVal', [4, 6]), 154_571, 143_132),
    "b18": (('RVal', [10, 6]), 49_558, 48_156),
    "b19": (('RVal', [10, 7]), 62_529, 60_281),
    "b20": (('RVal', [10, 12]), 74_683, 71_633),
    "b21": (('RErr', None), 37_519, 36_681),
    "b22": (('RVal', [1, 4, 9]), 130_497, 122_280),
    "b23": (('RVal', [1, 3, 4]), 128_405, 120_443),
    "b24": (('RVal', [1, 3, 4, 5]), 203_747, 186_026),
    "b25": (('RVal', [1, 4, 9, 16, 25]), 293_543, 260_958),
    "b26": (('RVal', [1, 4, 9]), 130_497, 122_280),
    "b27": (('RVal', [4, 9]), 129_570, 121_481),
    "b28": (('RVal', [1, 4, 9, 16]), 206_926, 188_631),
    "b29": (('RVal', [6, 10]), 121_631, 114_284),
    "b31": (('RVal', [1, 5, 6, -1]), 1_570_329, 1_022_909),
    "b33": (('RVal', [3, ('Char', 97)]), 33_912, 33_273),
    "b34": (('RVal', [('Char', 120), ('Char', 98)]), 33_840, 33_201),
    "b35": (('RVal', [('Char', 120), 1]), 33_837, 33_198),
    "b36": (('RVal', [True, 1]), 33_787, 33_148),
    "b37": (('RVal', [('Set', (1,)), 1]), 33_948, 33_309),
    "b38": (('RVal', [('Str', 's'), 1]), 34_013, 33_374),
    "b39": (('RVal', [[], 1]), 34_091, 33_452),
    "b40": (('RVal', [1, 2]), 32_174, 31_571),
    "b41": (('RVal', [1, 2]), 32_174, 31_571),
    "b42": (('RVal', [5, ('Str', 'pos')]), 993_667, 726_234),
    "b43": (('RVal', [0, ('Str', 'zero')]), 864_841, 650_108),
    "b44": (('RVal', [-3, ('Str', 'neg')]), 1_014_271, 737_994),
    "b45": (('RVal', [1, 2]), 466_255, 387_717),
    "b46": (('RErr', None), 66_477, 64_229),
    "b47": (('RVal', [1, 1, 2]), 467_516, 388_581),
    "b48": (('RVal', [('Str', 'two')]), 100_998, 96_077),
    "b49": (('RVal', [5, ('Str', 'other')]), 109_757, 104_123),
    "b50": (('RVal', [1]), 74_340, 72_159),
    "b51": (('RVal', [2, 2, ('Str', 'two')]), 73_987, 71_243),
    "b52": (('RVal', [3, 2, ('Str', 'two')]), 73_987, 71_243),
    "b53": (('RErr', None), 29_565, 29_091),
    "b54": (('RVal', [3, [('Def', 'integer')]]), 70_007, 67_552),
    "b55": (('RVal', [('Char', 122), [('Def', 'char')]]), 119_174, 112_657),
    "b56": (('RVal', [[('Lit', 1)], [('Text', 'other')]]), 133_061, 125_099),
    "b57": (('RVal', [('Sym', 'dup'), [('Text', 'none')]]), 135_222, 127_005),
    "b58": (('RVal', [[('Lit', 2), ('Lit', 4)], [('Lit', 1), ('Lit', 3)]]), 1_578_160, 1_049_413),
    "b59": (('RVal', [('Str', 'cd'), ('Str', 'ab')]), 2_388_331, 1_490_060),
    "b60": (('RVal', [('Set', (1,)), ('Set', (2, 3))]), 1_180_509, 833_279),
    "b61": (('RVal', [[], []]), 322_868, 278_967),
    "b62": (('RErr', None), 29_351, 28_850),
    "b63": (('RVal', [True]), 380_238, 324_359),
    "b64": (('RVal', [False]), 438_126, 365_806),
    "b65": (('RVal', [True]), 106_970, 101_229),
    "b66": (('RVal', [False]), 99_811, 94_685),
    "b67": (('RVal', [True]), 455_939, 379_370),
    "b68": (('RVal', [False]), 156_915, 145_476),
    "b69": (('RVal', [False]), 156_915, 145_476),
    "b70": (('RVal', [True]), 98_761, 93_740),
    "b71": (('RVal', [True]), 325_020, 281_710),
    "b72": (('RVal', [True]), 116_337, 110_596),
    "b73": (('RVal', [True]), 2_614_403, 1_493_364),
    "b74": (('RVal', [False]), 2_603_888, 1_488_831),
    "b75": (('RVal', [False]), 1_104_337, 789_636),
    "b76": (('RVal', [True]), 85_007, 81_384),
    "b77": (('RVal', [True]), 85_007, 81_384),
    "b78": (('RVal', [1, 4, 9]), 557_031, 452_001),
    "b79": (('RVal', [10]), 1_138_314, 805_923),
    "b80": (('RVal', [25]), 34_590, 33_951),
    "b81": (('RVal', [[('Lit', 1), ('Quote', [('Lit', 4), ('Lit', 9)])]]), 1_117_378, 800_292),
    "b82": (('RVal', [9]), 51_157, 49_808),
    "b83": (('RVal', [[('Lit', 1), ('Quote', [('Lit', 4), ('Lit', 9)])]]), 1_241_594, 866_317),
    "b84": (('RVal', [True]), 280_143, 248_822),
    "b85": (('RVal', [False]), 274_816, 243_745),
}
COMPILED = {
    "b1": (('RVal', [3, 1, 2, 4]), 951, 962),
    "b2": (('RVal', [2, 3, 1, 4]), 949, 960),
    "b3": (('RVal', [3, 2, 1, 4]), 1_069, 1_080),
    "b4": (('RErr', None), 835, 846),
    "b5": (('RVal', [1]), 2_498, 2_554),
    "b6": (('RVal', [2]), 2_626, 2_682),
    "b7": (('RVal', [2]), 2_701, 2_757),
    "b8": (('RErr', None), 582, 596),
    "b9": (('RVal', [64]), 7, 7),
    "b10": (('RVal', [('quot', ('RVal', [1, 3, 2]))]), 3_517, 3_573),
    "b11": (('RVal', [('Str', 'abcde')]), 3_686, 3_742),
    "b12": (('RErr', None), 3_126, 3_168),
    "b13": (('RVal', [25]), 2_322, 2_350),
    "b14": (('RErr', None), 1_658, 1_672),
    "b15": (('RErr', None), 3_810, 3_880),
    "b16": (('RVal', [3, 4]), 43_997, 43_834),
    "b17": (('RVal', [4, 6]), 44_951, 44_788),
    "b18": (('RVal', [10, 6]), 12_071, 12_108),
    "b19": (('RVal', [10, 7]), 14_380, 14_459),
    "b20": (('RVal', [10, 12]), 17_650, 17_723),
    "b21": (('RErr', None), 8_438, 8_486),
    "b22": (('RVal', [1, 4, 9]), 40_106, 39_921),
    "b23": (('RVal', [1, 3, 4]), 38_137, 37_952),
    "b24": (('RVal', [1, 3, 4, 5]), 96_741, 96_407),
    "b25": (('RVal', [1, 4, 9, 16, 25]), 257_602, 257_133),
    "b26": (('RVal', [1, 4, 9]), 40_106, 39_921),
    "b27": (('RVal', [4, 9]), 37_543, 37_358),
    "b28": (('RVal', [1, 4, 9, 16]), 100_721, 100_387),
    "b29": (('RVal', [6, 10]), 34_915, 34_886),
    "b31": (('RVal', [1, 5, 6, -1]), 760_102, 746_881),
    "b33": (('RVal', [3, ('Char', 97)]), 6_159, 6_209),
    "b34": (('RVal', [('Char', 120), ('Char', 98)]), 6_091, 6_141),
    "b35": (('RVal', [('Char', 120), 1]), 6_088, 6_138),
    "b36": (('RVal', [True, 1]), 5_488, 5_538),
    "b37": (('RVal', [('Set', (1,)), 1]), 6_778, 6_828),
    "b38": (('RVal', [('Str', 's'), 1]), 6_264, 6_314),
    "b39": (('RVal', [('quot', ('RVal', [])), 1]), 5_798, 5_848),
    "b40": (('RVal', [1, 2]), 4_945, 4_995),
    "b41": (('RVal', [1, 2]), 4_945, 4_995),
    "b42": (('RVal', [5, ('Str', 'pos')]), 456_603, 454_255),
    "b43": (('RVal', [0, ('Str', 'zero')]), 425_194, 423_038),
    "b44": (('RVal', [-3, ('Str', 'neg')]), 470_924, 468_451),
    "b45": (('RVal', [1, 2]), 213_278, 212_717),
    "b46": (('RErr', None), 28_785, 28_840),
    "b47": (('RVal', [1, 1, 2]), 214_623, 214_062),
    "b48": (('RVal', [('Str', 'two')]), 25_944, 25_758),
    "b49": (('RVal', [5, ('Str', 'other')]), 31_104, 30_807),
    "b50": (('RVal', [1]), 25_030, 24_983),
    "b51": (('RVal', [2, 2, ('Str', 'two')]), 20_435, 20_305),
    "b52": (('RVal', [3, 2, ('Str', 'two')]), 20_435, 20_305),
    "b53": (('RErr', None), 7_703, 7_702),
    "b54": (('RVal', [3, ('quot', ('RErr', None))]), 19_346, 19_307),
    "b55": (('RVal', [('Char', 122), ('quot', ('RErr', None))]), 33_893, 33_713),
    "b56": (('RVal', [('quot', ('RVal', [1])), ('quot', ('RVal', [('Str', 'other')]))]), 41_595, 41_295),
    "b57": (('RVal', [('Sym', 'dup'), ('quot', ('RVal', [('Str', 'none')]))]), 42_769, 42_469),
    "b58": (('RVal', [('quot', ('RVal', [2, 4])), ('quot', ('RVal', [1, 3]))]), 878_856, 858_024),
    "b59": (('RVal', [('Str', 'cd'), ('Str', 'ab')]), 1_033_725, 1_011_489),
    "b60": (('RVal', [('Set', (1,)), ('Set', (2, 3))]), 584_342, 571_386),
    "b61": (('RVal', [('quot', ('RVal', [])), ('quot', ('RVal', []))]), 89_756, 89_848),
    "b62": (('RErr', None), 8_567, 8_637),
    "b63": (('RVal', [True]), 85_548, 84_593),
    "b64": (('RVal', [False]), 103_016, 101_566),
    "b65": (('RVal', [True]), 31_658, 31_602),
    "b66": (('RVal', [False]), 27_950, 27_918),
    "b67": (('RVal', [True]), 110_140, 108_630),
    "b68": (('RVal', [False]), 38_917, 38_810),
    "b69": (('RVal', [False]), 38_917, 38_810),
    "b70": (('RVal', [True]), 29_229, 29_197),
    "b71": (('RVal', [True]), 101_057, 100_103),
    "b72": (('RVal', [True]), 41_736, 41_680),
    "b73": (('RVal', [True]), 398_993, 393_540),
    "b74": (('RVal', [False]), 408_950, 403_539),
    "b75": (('RVal', [False]), 212_413, 210_448),
    "b76": (('RVal', [True]), 20_672, 20_601),
    "b77": (('RVal', [True]), 20_668, 20_597),
    "b78": (('RVal', [1, 4, 9]), 195_033, 189_959),
    "b79": (('RVal', [10]), 351_122, 339_750),
    "b80": (('RVal', [25]), 12_175, 12_167),
    "b81": (('RVal', [('quot', ('RVal', [1, ('quot', ('RVal', [4, 9]))]))]), 471_531, 453_291),
    "b82": (('RVal', [9]), 18_449, 18_452),
    "b83": (('RVal', [('quot', ('RVal', [1, ('quot', ('RVal', [4, 9]))]))]), 539_220, 520_721),
    "b84": (('RVal', [True]), 107_653, 106_402),
    "b85": (('RVal', [False]), 136_748, 135_282),
}


@pytest.fixture(scope="module")
def interp():
    return interpreted(PROGRAMS)


@pytest.mark.parametrize("name", sorted(PROGRAMS))
def test_interpreted_library(interp, name):
    outcome, unfuelled, fuelled = INTERPRETED[name]
    assert interp.run("u" + name) == (outcome, unfuelled), PROGRAMS[name]
    assert interp.run("r" + name) == (outcome, fuelled), PROGRAMS[name]


@pytest.mark.parametrize("name", sorted(PROGRAMS))
def test_compiled_library(name):
    comp = compiled({name: PROGRAMS[name]})
    outcome, unfuelled, fuelled = COMPILED[name]
    assert comp.run("u" + name) == (outcome, unfuelled), PROGRAMS[name]
    assert comp.run("r" + name) == (outcome, fuelled), PROGRAMS[name]


# ---------------------------------------------------- the laws, both forms

LAWS = {
    "X Y [P] binary == X Y P":              ("3 4 [+] binary", "3 4 +"),
    "X [P] [Q] cleave == X P X Q":           ("5 [1 +] [2 *] cleave", "5 1 + 5 2 *"),
    "A [B] split concat size == A size":     ("[1 2 3] [2 <] split concat size", "[1 2 3] size"),
    "A [B] some == A [B] filter null not":   ("[1 2 3] [2 >] some", "[1 2 3] [2 >] filter null not"),
    "A [B] all == A [B] split popd null":    ("[1 2 3] [0 >] all", "[1 2 3] [0 >] split popd null"),
    "T T equal":                             ("[1 [2 'a]] [1 [2 'a]] equal", "true"),
    "X Y [P] unary2 == X P Y P (P unary)":   ("3 4 [dup *] unary2", "3 dup * 4 dup *"),
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
