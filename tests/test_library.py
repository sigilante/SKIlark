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
    "b1": (('RVal', [3, 1, 2, 4]), 11_807, 11_712),
    "b2": (('RVal', [2, 3, 1, 4]), 11_813, 11_718),
    "b3": (('RVal', [3, 2, 1, 4]), 12_774, 12_663),
    "b4": (('RErr', None), 9_058, 9_012),
    "b5": (('RVal', [1]), 21_997, 21_672),
    "b6": (('RVal', [2]), 22_991, 22_639),
    "b7": (('RVal', [2]), 22_967, 22_615),
    "b8": (('RErr', None), 5_259, 5_255),
    "b9": (('RVal', [64]), 856, 874),
    "b10": (('RVal', [[('Lit', 1), ('Lit', 3), ('Lit', 2)]]), 24_842, 24_490),
    "b11": (('RVal', [('Str', 'abcde')]), 24_676, 24_324),
    "b12": (('RErr', None), 22_709, 22_459),
    "b13": (('RVal', [25]), 14_963, 14_852),
    "b14": (('RErr', None), 9_743, 9_712),
    "b15": (('RErr', None), 26_867, 26_487),
    "b16": (('RVal', [3, 4]), 157_469, 146_335),
    "b17": (('RVal', [4, 6]), 159_691, 148_252),
    "b18": (('RVal', [10, 6]), 51_812, 50_410),
    "b19": (('RVal', [10, 7]), 65_189, 62_941),
    "b20": (('RVal', [10, 12]), 77_671, 74_621),
    "b21": (('RErr', None), 39_439, 38_601),
    "b22": (('RVal', [1, 4, 9]), 134_953, 126_736),
    "b23": (('RVal', [1, 3, 4]), 132_805, 124_843),
    "b24": (('RVal', [1, 3, 4, 5]), 210_025, 192_304),
    "b25": (('RVal', [1, 4, 9, 16, 25]), 301_931, 269_346),
    "b26": (('RVal', [1, 4, 9]), 134_953, 126_736),
    "b27": (('RVal', [4, 9]), 133_996, 125_907),
    "b28": (('RVal', [1, 4, 9, 16]), 213_288, 194_993),
    "b29": (('RVal', [6, 10]), 126_637, 119_290),
    "b31": (('RVal', [1, 5, 6, -1]), 1_619_631, 1_072_211),
    "b33": (('RVal', [3, ('Char', 97)]), 36_972, 36_333),
    "b34": (('RVal', [('Char', 120), ('Char', 98)]), 37_455, 36_816),
    "b35": (('RVal', [('Char', 120), 1]), 36_821, 36_182),
    "b36": (('RVal', [True, 1]), 36_695, 36_056),
    "b37": (('RVal', [('Set', (1,)), 1]), 37_084, 36_445),
    "b38": (('RVal', [('Str', 's'), 1]), 37_225, 36_586),
    "b39": (('RVal', [[], 1]), 37_379, 36_740),
    "b40": (('RVal', [1, 2]), 34_668, 34_065),
    "b41": (('RVal', [1, 2]), 34_668, 34_065),
    "b42": (('RVal', [5, ('Str', 'pos')]), 829_643, 642_168),
    "b43": (('RVal', [0, ('Str', 'zero')]), 705_114, 561_290),
    "b44": (('RVal', [-3, ('Str', 'neg')]), 849_210, 654_314),
    "b45": (('RVal', [1, 2]), 373_406, 324_329),
    "b46": (('RErr', None), 47_759, 46_797),
    "b47": (('RVal', [1, 1, 2]), 374_614, 325_223),
    "b48": (('RVal', [('Str', 'two')]), 105_179, 100_258),
    "b49": (('RVal', [5, ('Str', 'other')]), 114_443, 108_809),
    "b50": (('RVal', [1]), 84_430, 82_249),
    "b51": (('RVal', [2, 2, ('Str', 'two')]), 77_198, 74_454),
    "b52": (('RVal', [3, 2, ('Str', 'two')]), 77_198, 74_454),
    "b53": (('RErr', None), 31_197, 30_723),
    "b54": (('RVal', [3, [('Def', 'integer')]]), 74_045, 71_590),
    "b55": (('RVal', [('Char', 122), [('Def', 'char')]]), 126_297, 119_780),
    "b56": (('RVal', [[('Lit', 1)], [('Text', 'other')]]), 141_318, 133_356),
    "b57": (('RVal', [('Sym', 'dup'), [('Text', 'none')]]), 142_636, 134_419),
    "b58": (('RVal', [[('Lit', 2), ('Lit', 4)], [('Lit', 1), ('Lit', 3)]]), 1_618_294, 1_089_547),
    "b59": (('RVal', [('Str', 'cd'), ('Str', 'ab')]), 2_721_681, 1_823_410),
    "b60": (('RVal', [('Set', (1,)), ('Set', (2, 3))]), 1_218_505, 871_275),
    "b61": (('RVal', [[], []]), 339_790, 295_889),
    "b62": (('RErr', None), 31_777, 31_276),
    "b63": (('RVal', [True]), 402_613, 346_734),
    "b64": (('RVal', [False]), 461_467, 389_147),
    "b65": (('RVal', [True]), 113_236, 107_495),
    "b66": (('RVal', [False]), 105_733, 100_607),
    "b67": (('RVal', [True]), 478_027, 401_458),
    "b68": (('RVal', [False]), 167_227, 155_788),
    "b69": (('RVal', [False]), 167_227, 155_788),
    "b70": (('RVal', [True]), 104_655, 99_634),
    "b71": (('RVal', [True]), 341_626, 298_316),
    "b72": (('RVal', [True]), 129_887, 124_146),
    "b73": (('RVal', [True]), 2_732_107, 1_611_068),
    "b74": (('RVal', [False]), 2_721_864, 1_606_807),
    "b75": (('RVal', [False]), 1_166_567, 851_866),
    "b76": (('RVal', [True]), 91_579, 87_956),
    "b77": (('RVal', [True]), 91_579, 87_956),
    "b78": (('RVal', [1, 4, 9]), 582_579, 477_549),
    "b79": (('RVal', [10]), 1_183_180, 850_789),
    "b80": (('RVal', [25]), 37_626, 36_987),
    "b81": (('RVal', [[('Lit', 1), ('Quote', [('Lit', 4), ('Lit', 9)])]]), 1_161_846, 844_760),
    "b82": (('RVal', [9]), 55_429, 54_080),
    "b83": (('RVal', [[('Lit', 1), ('Quote', [('Lit', 4), ('Lit', 9)])]]), 1_288_858, 913_581),
    "b84": (('RVal', [True]), 296_095, 264_774),
    "b85": (('RVal', [False]), 287_338, 256_267),
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
    "b42": (('RVal', [5, ('Str', 'pos')]), 463_719, 461_371),
    "b43": (('RVal', [0, ('Str', 'zero')]), 432_310, 430_154),
    "b44": (('RVal', [-3, ('Str', 'neg')]), 478_040, 475_567),
    "b45": (('RVal', [1, 2]), 213_589, 213_028),
    "b46": (('RErr', None), 28_763, 28_818),
    "b47": (('RVal', [1, 1, 2]), 214_934, 214_373),
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
    "b58": (('RVal', [('quot', ('RVal', [2, 4])), ('quot', ('RVal', [1, 3]))]), 880_030, 859_198),
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
