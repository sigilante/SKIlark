"""The example programs (examples/*.joy): whole Joy files, run as the
reference runs them, each term on the stack the terms before it left and
the top printed after each.  examples/NAME.out is what the reference
prints; joyref's model gives it, and SKIlark, interpreted, must too.
Each file is its own test, and its own program set."""

import pathlib
import re

import pytest

import joyref
from skilark import joyfile

EXAMPLES = sorted((pathlib.Path(__file__).resolve().parent.parent / "examples").glob("*.joy"))


def _want(path):
    return path.with_suffix(".out").read_text(encoding="utf-8").splitlines()


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.stem)
def test_the_model_prints_what_the_example_says(path):
    assert joyref.Joy().run_file(path.read_text(encoding="utf-8")) == _want(path)


@pytest.mark.slow
@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.stem)
def test_skilark_prints_what_the_reference_prints(path):
    """Slow: whole programs, tens of millions of contractions in copy mode,
    which the slow job runs on Avon and the reference job would check
    against aviary, in Python, at length."""
    assert joyfile.run_file(path.read_text(encoding="utf-8")) == _want(path)


def test_there_are_examples():
    assert len(EXAMPLES) >= 8


# ---------------------------------------------------------- the reader

def test_comments_definitions_and_terms():
    text = ("(* a\n comment *) DEFINE sq == dup * ; one == 1 .\n"
            "2 sq . # to the end of the line\n"
            '"a.b" size .  ' + "'. ord .")
    assert joyfile.read(text) == [("define", {"sq": "dup *", "one": "1"}),
                                  ("term", "2 sq"), ("term", '"a.b" size'), ("term", "'. ord")]


def test_an_empty_term_prints_the_top():
    assert joyref.Joy().run_file("1 2 . .") == ["2", "1"]
    assert joyfile.read("1 2 . .") == [("term", "1 2"), ("term", "")]


def test_a_term_needs_its_period():
    with pytest.raises(joyfile.JoyFileError, match="no period"):
        joyfile.read("1 2 +")


def test_a_float_is_refused_by_name():
    """scan.c reads a number, a full stop and a digit as a float; SKIlark,
    which has none, refuses it rather than reading two terms."""
    for text, lit in (("1 2.5 + .", "2.5"), ("[-3.14] .", "-3.14"), ("0.5e3 .", "0.5e3")):
        with pytest.raises(joyfile.JoyFileError, match=f"a float.*{re.escape(lit)}"):
            joyfile.read(text)
    assert joyfile.read("[1 2 3]. 2. 5 .") == [("term", "[1 2 3]"), ("term", "2"), ("term", "5")]
    assert joyfile.read('"2.5" 1e5 .') == [("term", '"2.5" 1e5')]


def test_a_redefinition_holds_from_where_it_is_read():
    """A later DEFINE changes the word, and the words that call it, for
    the terms after it alone; a quoted word reads back by its own name."""
    text = ("DEFINE a == 1 ; b == a 10 + .\nb . [a] first body .\n"
            "DEFINE a == 2 .\nb . [a] first name . [a] first body .\n")
    lines = ["11", "[1]", "12", '"a"', "[2]"]
    assert joyref.Joy().run_file(text) == lines
    assert joyfile.run_file(text) == lines


def test_a_word_defined_later_is_undefined_before():
    """A term sees no definition read after it (the reference errs there
    under usrlib's undeferror 1, and runs nothing under 0, as SKIlark does)."""
    text = "DEFINE f == [g] . f i . DEFINE g == 5 . f i .\n"
    assert joyref.Joy().run_file(text) == ["5"]
    assert joyfile.run_file(text) == ["5"]
    assert joyfile.run_file(text, form="compiled") == ["5"]


def test_epoch_names_meet_no_word_of_the_file():
    """A word named like an epoch's is the file's own (the reference prints
    9 2 9 "a~1"), and a redefined word's name has no epoch, compiled too."""
    text = ("DEFINE a~1 == 9 ; a == 1 . a~1 . DEFINE a == 2 . a . a~1 .\n"
            "[a~1] first name . [a] first name size .\n")
    lines = ["9", "2", "9", '"a~1"', "1"]
    assert joyref.Joy().run_file(text) == lines
    assert joyfile.run_file(text) == lines
    assert joyfile.run_file(text, form="compiled") == lines


def test_a_definition_overwrites_a_builtin():
    """The reference warns "overwriting inbuilt" and runs the definition."""
    text = "DEFINE dup == pop 7 . 1 dup . DEFINE dup == pop 8 . 1 dup .\n"
    assert joyref.Joy().run_file(text) == ["7", "8"]
    assert joyfile.run_file(text) == ["7", "8"]


def test_a_module_s_member_is_refused_by_name():
    """scan.c reads a word, a full stop and a letter, digit or one of -=_ as
    a module's member; SKIlark has no modules."""
    for text, tok in (("[x.5] .", "x.5"), ("-.5 .", "-.5"), ("a.b .", "a.b")):
        with pytest.raises(joyfile.JoyFileError, match=f"module's member.*{re.escape(tok)}"):
            joyfile.read(text)
    assert joyfile.read("foo. 1 .") == [("term", "foo"), ("term", "1")]


def test_the_reference_s_scoping_is_not_skilark_s():
    with pytest.raises(joyfile.JoyFileError, match="HIDE"):
        joyfile.read("HIDE x == 1 IN y == x END .")


def test_values_are_written_as_the_reference_writes_them():
    w = joyfile.write
    assert [w(("N", -3)), w(("B", True)), w(("C", 97)), w(("C", 10)), w(("T", (97, 34))),
            w(("Z", 5)), w(("L", (("N", 1), ("S", "dup"))))] == \
        ["-3", "true", "'a", "'\\n", '"a\\""', "{0 2}", "[1 dup]"]
