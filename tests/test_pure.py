"""Joy's stage 9: the pure words the reference has that earlier stages
left (PLAN.md §3, stage 9): ``div pick compare condlinrec condnestrec
casting``.  ``compare`` is a kernel word, ext's ``Compare`` interpreted and
``wCompare`` compiled; the rest are derived, in both forms.  Each program
is compiled alone.  Every count was measured on skijack 0.2.3.
"""

import pytest

from skilark import compiled, interpreted

PROGRAMS = {
    "n1": '7 3 div',
    "n2": '-7 3 div',
    "n3": '7 -3 div',
    "n4": '7 0 div',
    "n5": "'a 3 div",
    "n6": '3 div',
    "n7": 'true 2 div',
    "n8": '1 2 3 4 0 pick',
    "n9": '1 2 3 4 1 pick',
    "n10": '1 2 3 4 3 pick',
    "n11": '1 2 3 4 9 pick',
    "n12": '1 2 3 -1 pick',
    "n13": '1 2 3 pick',
    "n14": '1 2 3 true pick',
    "n15": "1 2 3 'a pick",
    "n16": '1 2 compare',
    "n17": '2 1 compare',
    "n18": '3 3 compare',
    "n19": '"ab" "ac" compare',
    "n20": '"b" "a" compare',
    "n21": '[] [] compare',
    "n22": '[1] [2] compare',
    "n23": '{1} {2} compare',
    "n24": '{63} {0} compare',
    "n25": '{1} 2 compare',
    "n26": '[1] 1 compare',
    "n27": "'a 97 compare",
    "n28": '[dup] first [swap] first compare',
    "n29": 'true false compare',
    "n30": '1 compare',
    "n31": '3 [ [[0 =] [pop 1]] [[dup 1 -] [*]] ] condlinrec',
    "n32": '[1 2 3] [ [[null] [pop 0]] [[uncons] [+]] ] condlinrec',
    "n33": '0 [ [[0 =] ["zero"]] [[0 <] ["neg"]] [["pos"]] ] condlinrec',
    "n34": '-2 [ [[0 =] ["zero"]] [[0 <] ["neg"]] [["pos"]] ] condlinrec',
    "n35": '3 [ [[0 =] ["zero"]] [[0 <] ["neg"]] [["pos"]] ] condlinrec',
    "n36": '1 condlinrec',
    "n37": '[] condlinrec',
    "n38": '4 [ [[1 <=] [pop 1]] [[dup 1 -] [*]] ] condnestrec',
    "n39": '2 [ [[0 =] [pop 1]] [[1 - dup] [swap] [+]] ] condnestrec',
    "n40": '"x" condnestrec',
    "n41": '5 7 casting',
    "n42": '65 5 casting',
    "n43": '{0 2} 6 casting',
    "n44": 'true 6 casting',
    "n45": '1 4 casting',
    "n46": '0 4 casting',
    "n47": "'A 6 casting",
    "n48": '{3} 5 casting',
    "n49": 'true 7 casting',
    "n50": '5 6 casting',
    "n51": '6 casting',
}

INTERPRETED = {
    "n1": (('RVal', [2, 1]), 16_492, 16_327),
    "n2": (('RVal', [-2, -1]), 16_492, 16_327),
    "n3": (('RVal', [-2, 1]), 16_484, 16_319),
    "n4": (('RErr', None), 12_093, 12_013),
    "n5": (('RErr', None), 12_051, 11_971),
    "n6": (('RErr', None), 3_495, 3_504),
    "n7": (('RErr', None), 12_055, 11_975),
    "n8": (('RVal', [1, 2, 3, 4, 4]), 162_711, 151_577),
    "n9": (('RVal', [1, 2, 3, 4, 3]), 163_573, 152_439),
    "n10": (('RVal', [1, 2, 3, 4, 1]), 166_446, 155_162),
    "n11": (('RVal', [1, 2, 3, 4, 1]), 167_435, 156_151),
    "n12": (('RVal', [1, 2, 3, 3]), 163_027, 151_893),
    "n13": (('RErr', None), 9_058, 9_012),
    "n14": (('RErr', None), 30_550, 30_049),
    "n15": (('RErr', None), 30_796, 30_295),
    "n16": (('RVal', [-1]), 2_718, 2_727),
    "n17": (('RVal', [1]), 2_718, 2_727),
    "n18": (('RVal', [0]), 2_718, 2_727),
    "n19": (('RVal', [-1]), 2_718, 2_727),
    "n20": (('RVal', [1]), 2_718, 2_727),
    "n21": (('RVal', [0]), 2_718, 2_727),
    "n22": (('RVal', [1]), 2_718, 2_727),
    "n23": (('RVal', [-1]), 2_718, 2_727),
    "n24": (('RVal', [-1]), 2_718, 2_727),
    "n25": (('RVal', [0]), 2_718, 2_727),
    "n26": (('RVal', [1]), 2_718, 2_727),
    "n27": (('RVal', [0]), 2_718, 2_727),
    "n28": (('RVal', [-1]), 6_301, 6_280),
    "n29": (('RVal', [1]), 2_718, 2_727),
    "n30": (('RErr', None), 1_787, 1_805),
    "n31": (('RVal', [6]), 1_437_603, 979_342),
    "n32": (('RVal', [6]), 1_411_783, 963_046),
    "n33": (('RVal', [0, ('Str', 'zero')]), 225_295, 204_639),
    "n34": (('RVal', [-2, ('Str', 'neg')]), 270_796, 242_169),
    "n35": (('RVal', [3, ('Str', 'pos')]), 286_708, 255_132),
    "n36": (('RErr', None), 12_219, 12_166),
    "n37": (('RErr', None), 16_593, 16_465),
    "n38": (('RVal', [24]), 1_568_331, 1_050_836),
    "n39": (('RVal', [4]), 3_102_782, 1_706_063),
    "n40": (('RErr', None), 12_717, 12_664),
    "n41": (('RVal', [('Set', (0, 2))]), 572_013, 483_255),
    "n42": (('RVal', [('Char', 65)]), 59_234, 57_778),
    "n43": (('RVal', [5]), 478_494, 404_260),
    "n44": (('RVal', [1]), 50_577, 49_477),
    "n45": (('RVal', [True]), 53_247, 52_000),
    "n46": (('RVal', [False]), 53_247, 52_000),
    "n47": (('RVal', [65]), 57_192, 55_843),
    "n48": (('RVal', [('Char', 8)]), 397_973, 345_063),
    "n49": (('RVal', [('Set', (0,))]), 285_192, 256_325),
    "n50": (('RVal', [5]), 66_375, 64_634),
    "n51": (('RErr', None), 1_650, 1_668),
}

COMPILED = {
    "n1": (('RVal', [2, 1]), 1_835, 1_877),
    "n2": (('RVal', [-2, -1]), 1_835, 1_877),
    "n3": (('RVal', [-2, 1]), 1_827, 1_869),
    "n4": (('RErr', None), 1_285, 1_313),
    "n5": (('RErr', None), 1_393, 1_421),
    "n6": (('RErr', None), 355, 369),
    "n7": (('RErr', None), 1_323, 1_351),
    "n8": (('RVal', [1, 2, 3, 4, 4]), 111_846, 111_696),
    "n9": (('RVal', [1, 2, 3, 4, 3]), 127_914, 127_644),
    "n10": (('RVal', [1, 2, 3, 4, 1]), 187_786, 187_128),
    "n11": (('RVal', [1, 2, 3, 4, 1]), 187_803, 187_145),
    "n12": (('RVal', [1, 2, 3, 3]), 101_114, 101_123),
    "n13": (('RErr', None), 2_345, 2_356),
    "n14": (('RErr', None), 6_193, 6_215),
    "n15": (('RErr', None), 6_523, 6_545),
    "n16": (('RVal', [-1]), 165, 165),
    "n17": (('RVal', [1]), 165, 165),
    "n18": (('RVal', [0]), 165, 165),
    "n19": (('RVal', [-1]), 165, 165),
    "n20": (('RVal', [1]), 165, 165),
    "n21": (('RVal', [0]), 165, 165),
    "n22": (('RVal', [1]), 165, 165),
    "n23": (('RVal', [-1]), 165, 165),
    "n24": (('RVal', [-1]), 165, 165),
    "n25": (('RVal', [0]), 165, 165),
    "n26": (('RVal', [1]), 165, 165),
    "n27": (('RVal', [0]), 165, 165),
    "n28": (('RVal', [-1]), 692, 692),
    "n29": (('RVal', [1]), 165, 165),
    "n30": (('RErr', None), 85, 85),
    "n31": (('RVal', [6]), 505_046, 498_018),
    "n32": (('RVal', [6]), 488_726, 481_698),
    "n33": (('RVal', [0, ('Str', 'zero')]), 90_499, 90_166),
    "n34": (('RVal', [-2, ('Str', 'neg')]), 111_452, 110_942),
    "n35": (('RVal', [3, ('Str', 'pos')]), 123_258, 122_616),
    "n36": (('RErr', None), 2_685, 2_699),
    "n37": (('RErr', None), 4_943, 4_971),
    "n38": (('RVal', [24]), 549_534, 542_152),
    "n39": (('RVal', [4]), 875_234, 861_985),
    "n40": (('RErr', None), 2_968, 2_982),
    "n41": (('RVal', [('Set', (0, 2))]), 280_438, 278_618),
    "n42": (('RVal', [('Char', 65)]), 22_831, 22_858),
    "n43": (('RVal', [5]), 258_263, 256_024),
    "n44": (('RVal', [1]), 21_434, 21_462),
    "n45": (('RVal', [True]), 19_756, 19_786),
    "n46": (('RVal', [False]), 19_756, 19_786),
    "n47": (('RVal', [65]), 22_517, 22_545),
    "n48": (('RVal', [('Char', 8)]), 220_848, 219_103),
    "n49": (('RVal', [('Set', (0,))]), 135_130, 134_545),
    "n50": (('RVal', [5]), 25_937, 25_960),
    "n51": (('RErr', None), 119, 119),
}


@pytest.fixture(scope="module")
def interp():
    return interpreted(PROGRAMS)


@pytest.mark.parametrize("name", sorted(PROGRAMS))
def test_interpreted_pure(interp, name):
    outcome, unfuelled, fuelled = INTERPRETED[name]
    assert interp.run("u" + name) == (outcome, unfuelled), PROGRAMS[name]
    assert interp.run("r" + name) == (outcome, fuelled), PROGRAMS[name]


@pytest.mark.parametrize("name", sorted(PROGRAMS))
def test_compiled_pure(name):
    comp = compiled({name: PROGRAMS[name]})
    outcome, unfuelled, fuelled = COMPILED[name]
    assert comp.run("u" + name) == (outcome, unfuelled), PROGRAMS[name]
    assert comp.run("r" + name) == (outcome, fuelled), PROGRAMS[name]


# ---------------------------------------------------- the laws, both forms

LAWS = {
    "I J div == I J / I J rem":              ("7 3 div", "7 3 / 7 3 rem"),
    "0 pick == dup":                         ("1 2 3 4 0 pick", "1 2 3 4 dup"),
    "1 pick == over":                        ("1 2 3 4 1 pick", "1 2 3 4 over"),
    "X X compare == 0":                      ('"abc" "abc" compare', "0"),
    "condnestrec of two parts == condlinrec":
        ("3 [[[0 =] [pop 1]] [[dup 1 -] [*]]] condnestrec",
         "3 [[[0 =] [pop 1]] [[dup 1 -] [*]]] condlinrec"),
    "N 5 casting == N chr":                  ("65 5 casting", "65 chr"),
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
