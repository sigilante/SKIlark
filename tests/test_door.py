"""Stage 15 (a): the door, a program as a kernel whose I/O words are
drivers' cards (``skilark.door``).  Each stage-14 program the door answers
runs here under skijack's reference drivers in stage 14's world, and must
write what stage 14's host writes and end as it ends: status 0 for a value,
abort or quit, 1 for an error.  The reference drivers are skijack's from
0.2.5; with an earlier skijack these tests skip."""

import pytest

drivers = pytest.importorskip("skijack.drivers")

from skilark import door
from test_io import INTERPRETED, PROGRAMS, world

ANSWERED = ["o2", "o3", "o11", "o12", "o13", "o14", "o15", "o17", "o18", "o19"]

#: name -> (status, pokes, contractions): the pokes' reductions, the run
#: included, as the door forces each poke to the run's stop
DOOR = {
    "o2": (0, 1, 7_084),
    "o3": (0, 1, 3_670),
    "o11": (0, 1, 7_173),
    "o12": (0, 3, 12_333),
    "o13": (0, 2, 6_509),
    "o14": (0, 1, 8_652),
    "o15": (0, 1, 8_282),
    "o17": (1, 1, 3_245),
    "o18": (1, 1, 3_520),
    "o19": (1, 1, 5_726),
}

STATUS = {"RVal": 0, "RAbort": 0, "RQuit": 0, "RErr": 1}


@pytest.fixture(scope="module")
def kernels():
    return door.doors({n: PROGRAMS[n] for n in ANSWERED})


def the_world():
    h = world()
    return drivers.World(argv=[a.encode() for a in h.argv],
                         env={k.encode(): v.encode() for k, v in h.env.items()})


@pytest.mark.parametrize("name", ANSWERED)
def test_the_door_writes_and_ends_as_stage_14s_host(kernels, name):
    r = drivers.run_kernel(kernels[name], the_world())
    outcome, _, _, text = INTERPRETED[name]
    assert r.stdout.decode() == text and r.stderr == b""
    assert r.status == STATUS[outcome[0]]
    assert (r.status, r.pokes, r.steps) == DOOR[name]


def test_a_word_the_door_does_not_answer_yet_exits_2():
    k = door.doors({"o1": PROGRAMS["o1"]})["o1"]
    assert drivers.run_kernel(k, the_world()).status == 2
