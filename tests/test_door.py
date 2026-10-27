"""Stage 15: the door, a program or a file as a kernel whose I/O words are
drivers' cards (``skilark.door``).  A door must write what stage 14's host
writes, in the same world, and end as it ends: status 0 for a value,
abort or quit, 1 for an error.

Two runtimes perform the cards.  skijack's reference drivers, in Python,
run the cheap programs, with their pokes and contractions pinned; they
spend minutes on a program that reads or writes much, as each byte is a
unary numeral read a successor at a time.  ``avon run --kernel`` runs the
rest, in copy and share mode: every stage-14 program, each but the clock
again with its stack written after it, so what ``get`` read shows, the
reader's hard cases, and, slow for the compiling, every example file.
The Avon tests skip without ``AVON``, an avon binary."""

import os
import pathlib
import subprocess

import pytest

from skijack import drivers
from skijack.avon import _encode
from skilark import door, interpreted, joyfile
from skilark.io import Host
from test_io import PROGRAMS, STDIN, world

AVON = os.environ.get("AVON")
needs_avon = pytest.mark.skipif(not AVON, reason="needs AVON, an avon binary")

EXAMPLES = sorted((pathlib.Path(__file__).parent.parent / "examples").glob("*.joy"))

STATUS = {"RVal": 0, "RAbort": 0, "RQuit": 0, "RErr": 1}

#: name -> (status, pokes, contractions) under the reference drivers: the
#: pokes' reductions, the run included, as the door forces each poke to
#: the run's stop and each card's bytes to data
REFERENCE = {
    "o1": (0, 1, 33_001),
    "o3": (0, 1, 60_489),
    "o11": (0, 1, 38_028),
    "o13": (0, 2, 26_537),
    "o14": (0, 1, 20_609),
    "o15": (0, 1, 20_135),
    "o17": (1, 1, 22_010),
    "o18": (1, 1, 22_332),
    "o19": (1, 1, 25_287),
}

#: the reader's hard cases: numbers, words, escapes, nesting, sets, a word
#: that runs into a string, a stray bracket, a set member past 63, an
#: unclosed list at the input's end, and a term after the errors
READS = (
    "1 2 + put 32 putch get stack put 32 putch get stack put 32 putch get stack put"
    " 32 putch get put 32 putch get put 32 putch get put .\n"
    + "get put 32 putch get put 32 putch get put 32 putch get put .\n" * 2
    + "get put 32 putch get put 32 putch get put .\n"
    "get put 32 putch get put .\n"
    "get put .\nget .\nget put .\n\"after\" .\n")
READS_IN = ("  -12 0 007 abc\n\"a\\\"b\\n\\065\" '\\t 'x '\\101 [1 [2 \"x y\"] {3 1 2} 'z] {} [] -\n"
            "true false [true put] 12abc ab\"c d\" ] {64} '\\0 \"tab\\there\" [1 2")

#: factors across the 256-byte reads: numbers, a 152-byte string, and a
#: 60-number list the third read completes
BIG = "DEFINE g == get put 32 putch .\n" + " ".join(["g"] * 40) + " .\n" + " ".join(["g"] * 72) + " .\n"
BIG_IN = (" ".join(map(str, range(60))) + ' "' + "x" * 150 + '" ['
          + " ".join(map(str, range(100, 160))) + "] 77 " + " ".join(map(str, range(200, 240))))


def stage14(programs):
    """What stage 14's host writes running each program, and its status."""
    from aviary_kernel.terms import App
    run = interpreted(programs)
    out = {}
    for name in programs:
        h = world()
        term = App(App(run.e.terms["execU"], run.e.terms["p" + name]), run.e.terms["Empty"])
        ctor, _, _ = run.drive(term, h)
        out[name] = (h.text(), STATUS[ctor])
    return out


def avon(kernel, tmp_path, strategy, stdin="", args=("-v",)):
    """``avon run --kernel`` on a door saved as ``joy``, so its argv[0] is
    stage 14's; its output and status."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "joy").write_text(_encode(kernel)[0])
    p = subprocess.run([AVON, "run", "--kernel", f"--strategy={strategy}", "--", "joy", *args],
                       cwd=tmp_path, input=stdin.encode(), capture_output=True, timeout=600,
                       env={"USER": "joy", "PATH": os.environ.get("PATH", "")})
    assert p.stderr == b""
    return p.stdout.decode(), p.returncode


# ------------------------------------------------- the reference drivers

@pytest.fixture(scope="module")
def reference_kernels():
    return door.doors({n: PROGRAMS[n] for n in REFERENCE})


@pytest.mark.parametrize("name", list(REFERENCE))
def test_the_door_under_the_reference_drivers(reference_kernels, name):
    h = world()
    w = drivers.World(stdin=STDIN.encode(), argv=[a.encode() for a in h.argv],
                      env={k.encode(): v.encode() for k, v in h.env.items()})
    r = drivers.run_kernel(reference_kernels[name], w)
    assert (r.stdout.decode(), r.status) == stage14({name: PROGRAMS[name]})[name] and r.stderr == b""
    assert (r.status, r.pokes, r.steps) == REFERENCE[name]


# ------------------------------------------------------------- on Avon

#: every stage-14 program, and each again writing its stack after it, but
#: o13: its clock is the step count here and 12 in stage 14's world
ON_AVON = dict(PROGRAMS, **{f"{n}s": f"{p} stack put" for n, p in PROGRAMS.items() if n != "o13"})


@pytest.fixture(scope="module")
def kernels():
    return door.doors(ON_AVON)


@pytest.fixture(scope="module")
def wanted():
    return stage14(ON_AVON)


@needs_avon
@pytest.mark.parametrize("strategy", ["copy", "share"])
@pytest.mark.parametrize("name", list(ON_AVON))
def test_the_door_on_avon_writes_and_ends_as_stage_14s_host(kernels, wanted, tmp_path, name, strategy):
    assert avon(kernels[name], tmp_path, strategy, STDIN) == wanted[name]


@needs_avon
@pytest.mark.parametrize("strategy", ["copy", "share"])
@pytest.mark.parametrize("text, stdin", [(READS, READS_IN), (BIG, BIG_IN)], ids=["reads", "big"])
def test_a_file_s_door_reads_as_stage_14s_host(tmp_path, text, stdin, strategy):
    want = joyfile.run_text(text, host=Host(stdin=stdin, argv=["joy", "-v"], env={"USER": "joy"}))
    assert avon(door.file_door(text), tmp_path, strategy, stdin) == (want, 0)


@needs_avon
@pytest.mark.slow
@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.stem)
def test_each_example_s_door_prints_what_the_example_says(tmp_path, path):
    """Slow: a file's door compiles in about ten seconds."""
    want = path.with_suffix(".out").read_text(encoding="utf-8")
    k = door.file_door(path.read_text(encoding="utf-8"))
    for strategy in ("copy", "share"):
        assert avon(k, tmp_path / strategy, strategy, args=()) == (want, 0)


# ------------------------------------------------------------ the source

def test_a_word_the_reader_does_not_know_is_an_undefined_symbol():
    src = door.source({"p": "get"})
    assert "rdMiss t = Sym (Def (User" in src
    for name in ("dup", "true", "putchars", "strtol"):
        assert door._bytes(name, "nil") in src


def test_a_read_asks_for_256_bytes():
    assert f"[2 [3 [0 {door.READ_MAX}]]]" in door.source({"p": "get"}) and door.READ_MAX == 256
