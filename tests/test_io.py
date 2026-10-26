"""Stage 14: the I/O words ``put putch putchars get argc argv getenv clock
abort quit``, the interpreted form's alone.  A run stops at one with
``RIO`` and the host answers it (``skilark.io``); each program here runs
in one fixed world, and its outcome and output must be the reference
model's in that world, with the contraction counts pinned."""

import pytest

import conform
import joyref
from skilark import compiled, interpreted, joyfile
from skilark.io import Host, factor_end

#: the world every program runs in
STDIN = "3 4 [1 'a \"b\" {1 2} dup] x"


def world() -> Host:
    return Host(stdin=STDIN, argv=["joy", "-v"], env={"USER": "joy"}, clock=lambda: 12)


PROGRAMS = {
    "o1": "1 2 + put",
    "o2": '"ab" putchars 10 putch',
    "o3": "'x putch",
    "o4": "[1 [2] \"c\" 'd {3} dup] put",
    "o5": "true put false put",
    "o6": "get get +",
    "o7": "get get get",
    "o8": "get get get i",
    "o9": "get get get get",
    "o10": "get get get get get",
    "o11": "argc argv",
    "o12": '"USER" getenv "NONE" getenv',
    "o13": "clock",
    "o14": "1 2 abort 3",
    "o15": "quit 1",
    "o16": "put",
    "o17": '"a" putch',
    "o18": "5 putchars",
    "o19": "5 getenv",
    "o20": "[put] first name",
    "o21": "1 [put] i 2 put",
    "o22": "[1 2 3] [put] step",
    "o23": "3 [dup 0 >] [dup put 1 -] while",
    "o24": "[get] i [get] i *",
}

#: name -> (outcome, contractions unfuelled, fuelled, what it writes)
INTERPRETED = {
    "o1": (('RVal', []), 4_193, 4_223, '3'),
    "o2": (('RVal', []), 3_669, 3_726, 'ab\n'),
    "o3": (('RVal', []), 1_931, 1_970, 'x'),
    "o4": (('RVal', []), 1_931, 1_970, '[1 [2] "c" \'d {3} dup]'),
    "o5": (('RVal', []), 3_669, 3_726, 'truefalse'),
    "o6": (('RVal', [7]), 3_415, 3_475, ''),
    "o7": (('RVal', [3, 4, [('Lit', 1), ('Glyph', 97), ('Text', 'b'), ('Set', (1, 2)), 'Dup']]), 3_063, 3_147, ''),
    "o8": (('RVal', [3, 4, 1, ('Char', 97), ('Str', 'b'), ('Set', (1, 2)), ('Set', (1, 2))]), 8_161, 8_212, ''),
    "o9": (('RVal', [3, 4, [('Lit', 1), ('Glyph', 97), ('Text', 'b'), ('Set', (1, 2)), 'Dup'], ('Sym', 'x')]), 4_045, 4_150, ''),
    "o10": (('RErr', None), 5_003, 5_108, ''),
    "o11": (('RVal', [2, [('Text', 'joy'), ('Text', '-v')]]), 2_081, 2_144, ''),
    "o12": (('RVal', [('Str', 'joy'), ('Str', '')]), 3_669, 3_726, ''),
    "o13": (('RVal', [12]), 1_099, 1_141, ''),
    "o14": (('RAbort', None), 2_740, 2_754, ''),
    "o15": (('RQuit', None), 1_075, 1_096, ''),
    "o16": (('RErr', None), 1_075, 1_096, ''),
    "o17": (('RErr', None), 1_907, 1_925, ''),
    "o18": (('RErr', None), 1_907, 1_925, ''),
    "o19": (('RErr', None), 1_907, 1_925, ''),
    "o20": (('RVal', [('Str', 'put')]), 3_783, 3_786, ''),
    "o21": (('RVal', []), 5_505, 5_553, '12'),
    "o22": (('RVal', []), 215_629, 208_150, '123'),
    "o23": (('RVal', [0]), 321_143, 309_111, '321'),
    "o24": (('RVal', [12]), 6_974, 7_020, ''),
}


@pytest.fixture(scope="module")
def run():
    return interpreted(PROGRAMS)


@pytest.mark.parametrize("name", sorted(PROGRAMS))
def test_interpreted_io(run, name):
    outcome, unfuelled, fuelled, out = INTERPRETED[name]
    h = world()
    assert run.run("u" + name, host=h) == (outcome, unfuelled), PROGRAMS[name]
    assert h.text() == out
    h = world()
    assert run.run("r" + name, host=h) == (outcome, fuelled), PROGRAMS[name]
    assert h.text() == out


@pytest.mark.parametrize("name", sorted(PROGRAMS))
def test_the_pinned_outcome_and_output_are_the_references(name):
    h = world()
    want = joyref.Joy(conform.OWN, host=h).run(PROGRAMS[name])
    outcome, _, _, out = INTERPRETED[name]
    assert conform.interpreted_outcome(outcome) == want, PROGRAMS[name]
    assert out == h.text(), PROGRAMS[name]


def test_with_no_host_a_run_stops_at_its_first_io_word(run):
    assert run.run("uo1")[0] == ("RIO", None)


def test_the_compiled_form_refuses_io():
    with pytest.raises(ValueError, match="interpreted form's alone"):
        compiled({"p": "1 put"})


def test_a_factor_ends_where_scan_c_ends_it():
    cases = {"12 3": "12", '[1 [2 3] "a]"] x': '[1 [2 3] "a]"]', '"a b" c': '"a b"',
             "'a b": "'a", "'\\n x": "'\\n", "'\\065 x": "'\\065", "dup[": "dup",
             "{1 2} 3": "{1 2}"}
    for text, factor in cases.items():
        assert text[:factor_end(text, 0)] == factor


# ---------------------------------------------------------- files

FILE = """DEFINE greet == "hello, " putchars putchars 10 putch .
"joy" greet .
1 2 + .
get dup put 10 putch .
1 2 abort .
.
pop pop pop .
5 .
quit .
6 .
"""


def test_a_file_writes_its_output_in_order_with_its_lines():
    want = joyref.Joy(host=world()).run_text(FILE)
    assert want == "hello, joy\n3\n3\n3\n2\nrun time error\n5\n"
    assert joyfile.run_text(FILE, host=world()) == want


#: after an error the reference runs on the stack as the error left it,
#: SKIlark on the stack the erring term began with: RErr carries no stack
ERRS = "1 2 3 .\npop pop pop pop .\n.\n"


def test_after_an_error_the_next_term_runs_on_the_stack_before_it():
    assert joyref.Joy().run_text(ERRS) == "3\nrun time error\n"
    assert joyfile.run_text(ERRS) == "3\nrun time error\n2\n"
