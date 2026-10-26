"""Stage 15: a SKIlark program as a kernel whose I/O words are cards
(PLAN.md stage 15; SKIjack ``SPEC.md`` §4.1, Avon ``DESIGN.md`` §9.2).

Stage 14's words stop a run with ``RIO n s q``, and SKIlark's Python host
answers them.  Here the answering is SKI too: a door, ``[[poke [peek
load]] state]``, whose poke runs the program until it needs an answer it
does not hold, and returns the cards gathered on the way.  A runtime with
drivers performs the cards, skijack's reference host or ``avon run
--kernel``, and neither learns Joy.

- **The state** is ``[argv [q s]]``: the arguments, as byte lists, and the
  run to resume, its program and stack.  Before the first poke it holds
  ``nil`` and the program on the empty stack.
- **The first event** is boot's reply, ``[0 [0 [argv bits]]]``: the door
  keeps ``argv`` and runs the program.
- **A run's stop** at ``RIO n s q`` is the word ``n``:
  ``putch`` and ``putchars`` write card 1 and run on in the same poke;
  ``argc`` and ``argv`` push from the state; ``getenv`` sends card 3
  (id 1) and ``clock`` card 4 (id 2), keeping ``q`` and ``s`` for the
  reply; ``abort`` and ``quit`` exit 0.  ``put`` and ``get`` exit 2: their
  writer and reader are not written yet.
- **The end** is an exit card: 0 for ``RVal``, 1 for ``RErr``.

``clock`` pushes the runtime's step count, card 4's answer, not
milliseconds, until binary numerals.  ``getenv`` pushes ``""`` for an
unset variable, as ``getenv.c`` does.
"""

from __future__ import annotations

from typing import Dict

from . import joy
from . import abstraction

#: the I/O words the door answers, each by its RIO number
ANSWERED = ("putch", "putchars", "argc", "argv", "getenv", "clock", "abort", "quit")

DOOR = """
-- the door (skilark.door): a kernel whose I/O words are drivers' cards
doorCode c = c |> {{ Pos k k; Neg m Zero }}
doorByte c = natRem (doorCode c) 256
doorBytes z = z |> {{ TNil nil; TCons c r (cons (doorByte c) (doorBytes r)) }}
doorText bs = bs TNil doorTextC
doorTextC b r = TCons (Pos b) (doorText r)
doorArgvC a r = Then (Lit (Str (doorText a))) (doorArgv r)
doorArgv as = as Done doorArgvC
doorEnvC h r = Str (doorText h)
-- a poke's value from the cards so far and the rest: [cards state].  Each
-- is forced, a pair applied to its continuation, so the poke's weak head
-- normal form is the run to its stop: the run's work is the poke's, and
-- counted, not left for the runtime's probes of the cards
doorWr c p = p (doorWrK c)
doorWrK c cs st = [(cons c cs) st]
doorEnd code = [(cons [5 code] nil) [nil [Done Empty]]]
doorAsk c a q s = [(cons c nil) [a [q s]]]
doorGo r a = r |> {{ RVal s (doorEnd 0); RErr (doorEnd 1); RTime (doorEnd 1); RIO n s q (doorIo n s q a) }}
doorOn q s a = doorGo (execU q s) a
doorPutch s q a = s |> {{ Empty (doorEnd 1); Push x t (x |> {{ Num c (doorWr [1 [1 (cons (doorByte c) nil)]] (doorOn q t a)); Quot p (doorEnd 1); Logical l (doorEnd 1); Sym w (doorEnd 1); Char c (doorWr [1 [1 (cons (doorByte c) nil)]] (doorOn q t a)); Str z (doorEnd 1); Set z (doorEnd 1) }}) }}
doorPutchars s q a = s |> {{ Empty (doorEnd 1); Push x t (x |> {{ Num c (doorEnd 1); Quot p (doorEnd 1); Logical l (doorEnd 1); Sym w (doorEnd 1); Char c (doorEnd 1); Str z (doorWr [1 [1 (doorBytes z)]] (doorOn q t a)); Set z (doorEnd 1) }}) }}
doorGetenv s q a = s |> {{ Empty (doorEnd 1); Push x t (x |> {{ Num c (doorEnd 1); Quot p (doorEnd 1); Logical l (doorEnd 1); Sym w (doorEnd 1); Char c (doorEnd 1); Str z (doorAsk [3 [1 (doorBytes z)]] a q t); Set z (doorEnd 1) }}) }}
doorIo n s q a = natIfEq n {putch} (doorPutch s q a) (natIfEq n {putchars} (doorPutchars s q a) (natIfEq n {argc} (doorOn q (Push (Num (Pos (listLength a))) s) a) (natIfEq n {argv} (doorOn q (Push (Quot (doorArgv a)) s) a) (natIfEq n {getenv} (doorGetenv s q a) (natIfEq n {clock} (doorAsk [4 2] a q s) (natIfEq n {abort} (doorEnd 0) (natIfEq n {quit} (doorEnd 0) (doorEnd 2))))))))
-- a reply: id 0 boot's [argv bits], id 1 getenv's value, id 2 clock's count
doorStart v st = doorOn (6@st) (7@st) (2@v)
doorEnv v st = doorOn (6@st) (Push (v (Str TNil) doorEnvC) (7@st)) (2@st)
doorClock v st = doorOn (6@st) (Push (Num (Pos v)) (7@st)) (2@st)
doorAfter v st p = p (doorEnv v st) (K (doorClock v st))
doorStep id v st = id (doorStart v st) (doorAfter v st)
doorPoke b r = r (doorPokeK b)
doorPokeK b cs st = [cs [b st]]
poke k ev = doorPoke (2@k) (doorStep (6@ev) (7@ev) (3@k))
peek k p = 3@k
load k old = [(2@k) old]
"""


def source(programs: Dict[str, str], defs: Dict[str, str] = joy.DEFINITIONS) -> str:
    """The interpreted kernel with ``programs``, and for each program ``P``
    a door ``kP`` that runs it."""
    codes = {name: joy.IO_CODES[name] for name in ANSWERED}
    out = [joy.interpreted(programs, defs), DOOR.format(**codes)]
    for name in programs:
        out.append(f"k{name} := [[poke [peek load]] [nil [p{name} Empty]]]\n")
    return "".join(out)


def doors(programs: Dict[str, str], defs: Dict[str, str] = joy.DEFINITIONS):
    """Each program's door, compiled: ``{name: kernel term}``.  A card list
    holds cells of different types, which skijack's Stage B has no type
    for, so the source compiles with checking off."""
    e = abstraction.compile(source(programs, defs), check=False)
    return {name: e.terms[f"k{name}"] for name in programs}
