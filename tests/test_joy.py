"""The kernel, the programs and the laws of PLAN.md, pinned.  Every number
here was measured on skijack 0.2.0; stacks are read bottom to top.
"""

import pytest

import skijack
from skilark import Joy, read

LEXICONS = ["ascii", "unicode"]


@pytest.fixture(params=LEXICONS, scope="module")
def joy(request):
    return Joy(request.param)


# ------------------------------------------------------------ the kernel

def test_the_kernel_and_its_words_have_these_sizes(joy):
    s = joy.e.sizes
    assert (s["exec"], s["step"], s["cat"], s["wordOf"]) == (2_538, 2_428, 69, 87)
    assert (s["add"], s["mul"], s["fuel"]) == (42, 77, 749)
    # derived words are programs, a few hundred atoms each
    assert (s["over"], s["nip"], s["tuck"], s["rot"], s["sip"]) == (209, 154, 209, 207, 199)
    assert (s["kComb"], s["yComb"], s["sumto"]) == (193, 399, 1_178)


def test_both_lexicons_compile_to_the_same_terms():
    a = skijack.compile(read("joy", "ascii"), lexicon="ascii")
    u = skijack.compile(read("joy", "unicode"), lexicon="unicode")
    assert a.sizes == u.sizes
    assert all(str(a.terms[k]) == str(u.terms[k]) for k in a.terms)


# ---------------------------------------------------------- the programs

def test_arithmetic_and_a_quotation_applied(joy):
    assert joy.run("r1") == (("RVal", [6]), 9_276)         # 1 2 + dup +
    assert joy.run("r2") == (("RVal", [6]), 9_291)         # 3 [dup +] i


def test_derived_words_over_and_k(joy):
    assert joy.run("r3") == (("RVal", [1, 2, 1]), 11_601)  # 1 2 over
    assert joy.run("r4") == (("RVal", [1, 3]), 14_030)     # 1 [2] [3] k


def test_unit_and_cons_build_a_quotation(joy):
    assert joy.run("r5") == (("RVal", [[("Lit", 1), ("Lit", 2)]]), 7_820)


def test_underflow_is_an_error_not_a_crash(joy):
    assert joy.run("r6") == (("RErr", None), 3_385)        # + on the empty stack


def test_recursion_through_kerbys_y(joy):
    """sumto is [swap [pop 0] [dup [swap i] dip 1 + +] ifz] y: no word
    names itself; the self-quotation y leaves on the stack is the only
    recursion."""
    assert joy.run("r7") == (("RVal", [6]), 110_770)       # 3 sumto
    assert joy.run("r8") == (("RVal", [15]), 173_876)      # 5 sumto


def test_fuel_runs_out_as_a_value(joy):
    assert joy.run("r8starved") == (("RTime", None), 4_839)  # 5 sumto, fuel 10


# ---------------------------------------------------- the algebra of programs

LAWS = {
    "Swap": "swap swap == id",
    "Dup":  "dup pop == id",
    "Do":   "[P] i == P",
    "Cat":  "[P] [Q] cat == [P Q]",
    "Dip":  "[P] [Q] dip == Q [P]",
    "Unit": "x unit == [x]",
    "K":    "[B] [A] k == A",
    "Sip":  "[B] [A] sip == [B] A [B]",
}


@pytest.mark.parametrize("law", sorted(LAWS))
def test_the_laws_hold_on_a_sample_stack(joy, law):
    """Each law's two sides are declared programs; both run to the same
    stack.  These are the obligations a jet for the word inherits."""
    left, right = joy.exec(f"law{law}L"), joy.exec(f"law{law}R")
    assert left == right and left[0] == "RVal", LAWS[law]
