"""Wodan58/Joy's own test suite, ``joy/test2/`` (see ``joy/README.md``), run
by the model and, on the slow job, by SKIlark interpreted.

Each file is run whole, as the reference runs it, with three changes:

- A term with a float literal is dropped (SKIlark has no floats), and so
  is a term that uses a word in ``ABSENT``, a word SKIlark lacks.
- The reference's library words a file uses (``PRELUDE``) are defined
  first.
- ``argv`` is the file's name, as ``joy FILE`` gives it.

Then every line the file prints is ``true``, except in the files whose
lines are values (``OUTPUT``); a term that leaves the stack empty prints
nothing. A file in ``SKIP`` cannot run: it holds a shell transcript or
input for ``get``, or what is left after the drops depends on what was
dropped. A file with every term dropped is skipped with the kinds of words
that dropped it. Each known failure is a strict expected failure with its
reason. A fix turns it into a pass, which fails the test until its entry
is removed.
"""

import re
from pathlib import Path

import pytest

import joyref
from skilark import joy, joyfile
from skilark.io import Host

SUITE = Path(__file__).parent / "joy" / "test2"
FILES = sorted(p.name for p in SUITE.glob("*.joy"))

#: the reference's library words the suite uses, as written at fe9fa0f:
#: inilib.joy's and agglib.joy's, which usrlib.joy loads at startup, and
#: numlib.joy's, which times, unary and while load with libload (dropped)
PRELUDE = {
    "newline": "'\\n putch",
    "putln": "put newline",
    "swoncat": "swap concat",
    "sum": "0 [+] fold",
    "fib": "[1 0] dip [swap [+] unary] times popd",
    "from-to": "[] cons [pop pop] swoncat [>] swap [ [dup succ] dip ] [cons] linrec",
    "from-to-list": "[] from-to",
    "prime": "2 [ [dup * >] nullary [rem 0 >] dip and ] [ succ ] while dup * <",
}

#: the reference's words SKIlark lacks, by kind; a term using one is dropped
ABSENT = {
    "floats": "acos asin atan atan2 ceil cos cosh exp floor frexp ldexp log log10 "
              "modf pow round sin sinh sqrt strtod tan tanh trunc formatf maxint",
    "files": "fopen fclose feof ferror fflush fgetch fgets fput fputch fputchars "
             "fputstring fread fremove frename fseek ftell fwrite filetime finclude "
             "stdin stdout stderr",
    "time": "time localtime gmtime mktime strftime rand srand",
    "settings": "echo setecho autoput setautoput undeferror setundeferror",
    "internals": "__dump __memoryindex __memorymax __settracegc __symtabindex "
                 "__symtabmax __html_manual __latex_manual __manual_list _help help "
                 "manual conts undefs",
    "host": "system libload assign Count",
}
ABSENT_WORDS = {w: kind for kind, ws in ABSENT.items() for w in ws.split()}

#: files that do not read, and why
READER = {f"{n}.joy": "a shell transcript, not Joy" for n in
          "fput fputch fputchars fputstring frename fwrite helpdetail".split()}
READER["get.joy"] = "input for get after the terms, not Joy"
#: files that cannot run, and why
SKIP = dict(READER, **{"frexp.joy": "its integer term pops what its float terms leave"})

#: files whose lines are values, with the lines the reference prints
OUTPUT = {
    "abort.joy": [], "id.joy": [], "quit.joy": [],
    "clock.joy": ["0"],
    "getenv.joy": ['"/bin"', "true"],
    "put.joy": ["pop", "sum", "true", "'A", "10", "{1 2 3}", '"test"', "[1 2 3]"],
    "putch.joy": ["A"],
    "putchars.joy": ["test"],
}

#: the model's known failures
MODEL = {
    "all2.joy": "[] all: the file says false; someall.h and boolean.h at fe9fa0f give true",
    "casting.joy": "casting is modelled for few type pairs",
}

#: SKIlark's known failures, beyond the model's
SKILARK = dict(MODEL, **{
    "casting.joy": "casting is modelled for few type pairs, and 123456789 is unary",
    "body.joy": "body of a DEFINE gives its expansion, not its text",
    "condlinrec.joy": "a recursive DEFINE (ack): the expander does not terminate",
    "condnestrec.joy": "3 4 cnr-ack in unary numerals runs out of fuel",
    **{f: "123456789: a unary literal past Python's recursion limit"
       for f in ("equal.joy", "eql.joy", "geql.joy", "greater.joy", "leql.joy", "less.joy")},
})

STRING = r'"(?:\\.|[^"\\])*"'
SCAN = re.compile(STRING + r"|'\\?.|"
                  r"(?<![\w'])(-?(?:\d+\.\d+(?:[eE][-+]?\d+)?|\d+[eE][-+]?\d+))(?![\w])")


def words(text):
    return set(re.findall(r"[^\s\[\]{}]+", re.sub(STRING, " ", text)))


def prepared(name):
    """The file as run, its terms, and the kinds of words that dropped each
    dropped item."""
    raw = (SUITE / name).read_text(encoding="utf-8", errors="replace")
    raw = SCAN.sub(lambda m: "FLOATLIT" if m.group(1) else m.group(0), raw)
    kept, dropped = [], []
    for kind, item in joyfile.read(raw):
        text = item if kind == "term" else " ".join(item.values())
        used = words(text)
        kinds = {"floats"} if "FLOATLIT" in used else set()
        kinds |= {ABSENT_WORDS[w] for w in used & ABSENT_WORDS.keys()}
        if kinds:
            dropped.append(kinds)
        else:
            kept.append((kind, item))
    used = words(" ".join(i if k == "term" else " ".join(i.values()) for k, i in kept)
                 + " " + " ".join(PRELUDE.values()))
    pre = {n: b for n, b in PRELUDE.items() if n in used and n not in joy.DEFINITIONS}
    lines = []
    if pre:
        lines.append("DEFINE " + " ; ".join(f"{n} == {b}" for n, b in pre.items()) + " .")
    for kind, item in kept:
        lines.append("DEFINE " + " ; ".join(f"{n} == {b}" for n, b in item.items()) + " ."
                     if kind == "define" else item + " .")
    return "\n".join(lines) + "\n", [i for k, i in kept if k == "term"], dropped


def host(name):
    return Host(argv=[name], env={"PATH": "/bin"}, clock=lambda: 0)


def passes(name, lines):
    """The lines are the file's OUTPUT, or some lines and every one true."""
    if name in OUTPUT:
        return lines == OUTPUT[name]
    return bool(lines) and all(line == "true" for line in lines)


def case(name, failures):
    marks = []
    if name in SKIP:
        marks.append(pytest.mark.skip(reason=SKIP[name]))
    elif not prepared(name)[1]:
        kinds = sorted(set().union(*prepared(name)[2]))
        marks.append(pytest.mark.skip(reason="every term uses " + ", ".join(kinds)))
    elif name in failures:
        marks.append(pytest.mark.xfail(reason=failures[name], strict=True))
    return pytest.param(name, marks=marks, id=name[:-4])


@pytest.mark.parametrize("name", [case(n, MODEL) for n in FILES])
def test_model(name):
    lines = joyref.Joy(host=host(name)).run_file(prepared(name)[0])
    assert passes(name, lines), lines


@pytest.mark.slow
@pytest.mark.parametrize("name", [case(n, SKILARK) for n in FILES])
def test_skilark(name):
    lines = joyfile.run_file(prepared(name)[0], host=host(name))
    assert passes(name, lines), lines


def test_accounted():
    """Every file runs a term or is dropped whole for words ABSENT lists."""
    assert len(FILES) == 225
    for name in FILES:
        if name in READER:
            continue
        _, terms, dropped = prepared(name)
        assert terms or dropped, name


def test_absent_are_absent():
    """A word ABSENT lists is in neither SKIlark nor its model: one added
    must leave the list, so its terms run."""
    model = set(joyref.Joy().b) | set(joyref.Joy().defs)
    ours = set(joy.KERNEL) | set(joy.DEFINITIONS) | set(joy.EXT) | set(joy.IO) | set(joy.COMPILED_ONLY)
    assert not ABSENT_WORDS.keys() & (model | ours)


def test_reader_refuses():
    """The files READER lists still do not read."""
    for name in READER:
        with pytest.raises(joyfile.JoyFileError):
            joyfile.read((SUITE / name).read_text(encoding="utf-8"))
