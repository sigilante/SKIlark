"""Stage 15: a SKIlark program or file as a kernel whose I/O words are
cards (PLAN.md stage 15; SKIjack ``SPEC.md`` §4.1, Avon ``DESIGN.md`` §9.2).

Stage 14's words stop a run with ``RIO n s q``, and SKIlark's Python host
answers them.  Here the answering is SKI too: a door, ``[[poke [peek
load]] state]``, whose poke runs the program until it needs an answer it
does not hold, and returns the cards gathered on the way.  A runtime with
drivers performs the cards, skijack's reference host or ``avon run
--kernel``, and neither learns Joy.

- **The state** is ``[e [q [s f]]]``: the world the door holds, the run
  to resume, its program and stack, and the run's context.  ``e`` is
  ``[argv [input eof]]``: the arguments as byte lists, the input read and
  not yet consumed, and whether the input has ended.
- **The context** ``f`` is a program alone, or a file's term with the
  terms after it and the stack the term began on.  A program ends with
  its run: exit 0 for a value, 1 for an error.  A file prints a term's top
  and pops it, as ``joyfile`` does, prints ``run time error`` where a term
  errs and runs the next on the stack the erring term began on, and exits
  0 after its last term.
- **The first event** is boot's reply, ``[0 [0 [argv bits]]]``: the door
  keeps ``argv`` and runs.
- **A run's stop** at ``RIO n s q`` is the word ``n``:
  ``put``, ``putch`` and ``putchars`` write card 1 and run on in the same
  poke; ``argc`` and ``argv`` push from the state; ``getenv`` sends card 3
  (id 1) and ``clock`` card 4 (id 2), keeping ``q`` and ``s`` for the
  reply; ``get`` reads a factor from the input held, or sends card 2 (id
  3) for 256 bytes more when the input holds none whole; ``abort`` ends a
  program with 0 and a file's term with its stack kept; ``quit`` exits 0.

``put``'s writer is ``write.c``'s, as ``joyfile.write`` has it, and
``get``'s reader finds a factor where ``io.factor_end`` does and reads it
as ``joy.parse`` does; a word that is not Joy's own reads as an undefined
symbol, as ``Run.word_term`` makes one.  Both work on bytes: a code past
255 is written modulo 256, and the reader's spaces are Python's ASCII
ones, 9 to 13 and 28 to 32.

A poke is strict: its weak head normal form is the run to its stop, and a
card's bytes are data, the list and each numeral rebuilt, as stage 14's
host normalizes each term's stack.  A runtime reads a card in bounded
probes that share nothing; bytes left as thunks would be recomputed for
every byte, and a long computation's text would pass the bound.

``clock`` pushes the runtime's step count, card 4's answer, not
milliseconds, until binary numerals.  ``getenv`` pushes ``""`` for an
unset variable, as ``getenv.c`` does.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from . import joy
from . import joyfile
from . import abstraction

#: the bytes a read card asks for: 256, a numeral the writer holds anyway,
#: where a larger literal is a longer Scott chain in the kernel
READ_MAX = 256


def _bytes(text: str, tail: str) -> str:
    """``text``'s bytes as a list literal before ``tail``."""
    out = tail
    for b in reversed(text.encode()):
        out = f"(cons {b} {out})"
    return out


DOOR = """
-- the door (skilark.door): a kernel whose I/O words are drivers' cards
doorCode c = c |> { Pos k k; Neg m Zero }
doorByte c = natRem (doorCode c) 256
doorBytes z = z |> { TNil nil; TCons c r (cons (doorByte c) (doorBytes r)) }
doorText bs = bs TNil doorTextC
doorTextC b r = TCons (Pos b) (doorText r)
doorArgvC a r = Then (Lit (Str (doorText a))) (doorArgv r)
doorArgv as = as Done doorArgvC
doorEnvC h r = Str (doorText h)

-- put's writer (write.c writefactor): an item's text, as bytes before acc
wrItem x acc = x |> { Num z (wrInt z acc); Quot p (cons 91 (wrProg p (cons 93 acc))); Logical b (b |> { False @FALSE@; True @TRUE@ }); Sym w (wrText (toCodes (nameOf w)) acc); Char c (cons 39 (nfNat (doorCode c) (wrCharF acc))); Str z (cons 34 (wrStr z (cons 34 acc))); Set z (cons 123 (wrSet z (cons 125 acc))) }
-- a number's digits from its numeral as data, rebuilt first: copy mode
-- shares nothing, and a thunk used at three places a digit is redone at each
wrInt z acc = z |> { Pos m (wrN m acc); Neg m (cons 45 (wrN (Suc m) acc)) }
wrN m acc = nfNat m (wrNatF acc)
wrNatF acc m = wrNat m acc
wrNat m acc = natIfLe 10 m (nfNat (natDiv m 10) (wrNatK m acc)) (cons (natAdd 48 m) acc)
wrNatK m acc q = wrNat q (cons (natAdd 48 (natRem m 10)) acc)
wr3 k acc = cons (natAdd 48 (natRem (natDiv k 100) 10)) (cons (natAdd 48 (natRem (natDiv k 10) 10)) (cons (natAdd 48 (natRem k 10)) acc))
wrEsc k = natIfEq k 8 98 (natIfEq k 9 116 (natIfEq k 10 110 (natIfEq k 11 118 (natIfEq k 12 102 114))))
-- a character: \\b to \\r by letter, other controls, space and DEL by code
wrCharF acc k = wrChar k acc
wrChar k acc = natIfLe 8 k (natIfLe k 13 (cons 92 (cons (wrEsc k) acc)) (natIfLe k 32 (cons 92 (wr3 k acc)) (natIfEq k 127 (cons 92 (wr3 k acc)) (cons (natRem k 256) acc)))) (cons 92 (wr3 k acc))
-- a string's code: the quote escaped, \\b to \\r by letter, other controls and DEL by code
wrStr z acc = z |> { TNil acc; TCons c r (nfNat (doorCode c) (wrStrF (wrStr r acc))) }
wrStrF acc k = wrStrC k acc
wrStrC k acc = natIfEq k 34 (cons 92 (cons 34 acc)) (natIfLe 8 k (natIfLe k 13 (cons 92 (cons (wrEsc k) acc)) (natIfLe k 31 (cons 92 (wr3 k acc)) (natIfEq k 127 (cons 92 (wr3 k acc)) (cons (natRem k 256) acc)))) (cons 92 (wr3 k acc)))
wrSet z acc = z |> { SNil acc; SCons m r (wrN m (wrSetR r acc)) }
wrSetR z acc = z |> { SNil acc; SCons m r (cons 32 (wrN m (wrSetR r acc))) }
wrProg p acc = p |> { Done acc; Then w r (wrItem (itemOf w) (wrProgR r acc)) }
wrProgR p acc = p |> { Done acc; Then w r (cons 32 (wrItem (itemOf w) (wrProgR r acc))) }
wrText z acc = z |> { TNil acc; TCons c r (cons (doorByte c) (wrText r acc)) }

-- the reader's classes: Python's ASCII spaces, brackets, digits
isSp c x y = natIfLe 9 c (natIfLe c 13 x (natIfLe 28 c (natIfLe c 32 x y) y)) y
isBr c x y = natIfEq c 91 x (natIfEq c 93 x (natIfEq c 123 x (natIfEq c 125 x y)))
isDig c x y = natIfLe 48 c (natIfLe c 57 x y) y
dropSp z = z nil (dropSpC z)
dropSpC z c r = isSp c (dropSp r) z

-- where a factor ends (io.factor_end): k n rest, n the bytes it takes at
-- depth d, rest nil where the scan reached the input's end
fe z d n k = z (k n nil) (feC d n k)
feC d n k c r = natIfEq c 34 (feStr r d (Suc n) k) (natIfEq c 39 (feChr r d (Suc n) k) (natIfEq c 91 (fe r (Suc d) (Suc n) k) (natIfEq c 123 (fe r (Suc d) (Suc n) k) (natIfEq c 93 (feShut r d (Suc n) k) (natIfEq c 125 (feShut r d (Suc n) k) (isSp c (feEnd r d (Suc n) k) (feWord r d (Suc n) k)))))))
feShut r d n k = d |> { Zero (k n r); Suc e (feEnd r e n k) }
feEnd r d n k = d |> { Zero (k n r); Suc e (fe r d n k) }
feWord r d n k = d |> { Zero (r (k n r) (feWordC r n k)); Suc e (fe r d n k) }
feWordC r n k c u = isSp c (k n r) (isBr c (k n r) (fe r Zero n k))
feStr r d n k = r (k (Suc n) nil) (feStrC d n k)
feStrC d n k c u = natIfEq c 34 (feEnd u d (Suc n) k) (natIfEq c 92 (feSkip u d (Suc n) k) (feStr u d (Suc n) k))
feSkip u d n k = u (k (Suc n) nil) (feSkipC d n k)
feSkipC d n k c v = feStr v d (Suc n) k
feChr r d n k = r (k (Suc n) nil) (feChrC d n k)
feChrC d n k x u = natIfEq x 92 (feChrE u d (Suc n) k) (feEnd u d (Suc n) k)
feChrE u d n k = u (k (Suc n) nil) (feChrEC d n k)
feChrEC d n k y v = isDig y (feDig v d (Suc n) 2 k) (feEnd v d (Suc n) k)
feDig v d n m k = m |> { Zero (feEnd v d n k); Suc j (v (feEnd v d n k) (feDigC v d n j k)) }
feDigC v d n j k c w = isDig c (feDig w d (Suc n) j k) (feEnd v d n k)

-- a factor read (joy.parse): rd reads items onto acc, the latest on top,
-- until a closer or the end, then k acc w rest, w 0 at the end, 1 for ],
-- 2 for }; anything joy.parse refuses is fail
rdFactor z fail ok = rd z Empty fail (rdTop fail ok)
rdTop fail ok acc w rest = w |> { Zero (acc |> { Empty fail; Push x t (t |> { Empty (ok x); Push y u fail }) }); Suc j fail }
rd z acc fail k = z (k acc 0 nil) (rdC acc fail k)
rdC acc fail k c r = isSp c (rd r acc fail k) (natIfEq c 91 (rd r Empty fail (rdShut acc fail k 1)) (natIfEq c 123 (rd r Empty fail (rdShut acc fail k 2)) (natIfEq c 93 (k acc 1 r) (natIfEq c 125 (k acc 2 r) (natIfEq c 39 (rdChr r acc fail k) (natIfEq c 34 (rdStr r nil acc fail k) (rdTok r (cons c nil) acc fail k)))))))
rdShut acc fail k want inner w rest = natIfEq w want (natIfEq want 1 (rd rest (Push (Quot (rdProg inner Done)) acc) fail k) (rdSet inner SNil fail (rdSetK rest acc fail k))) fail
rdSetK rest acc fail k z = rd rest (Push (Set z) acc) fail k
rdProg acc p = acc |> { Empty p; Push x t (rdProg t (Then (wordOf x) p)) }
-- a set's members (factor.c list2set): integers and characters, 0 to 63
rdSet acc z fail ok = acc |> { Empty (ok z); Push x t (rdMember x fail (rdSetM t z fail ok)) }
rdSetM t z fail ok m = rdSet t (insS m z) fail ok
rdMember x fail ok = x |> { Num i (rdSmall i fail ok); Quot p fail; Logical b fail; Sym w fail; Char i (rdSmall i fail ok); Str t fail; Set t fail }
rdSmall i fail ok = i |> { Pos m (natIfLe 64 m fail (ok m)); Neg m fail }
-- a character, a string, and the escape after a backslash (joy._escape)
rdChr r acc fail k = r fail (rdChrC acc fail k)
rdChrC acc fail k x u = natIfEq x 92 (rdEsc u fail (rdChrK acc fail k)) (rd u (Push (Char (Pos x)) acc) fail k)
rdChrK acc fail k code rest = rd rest (Push (Char (Pos code)) acc) fail k
rdEsc z fail ok = z fail (rdEscC ok)
rdEscC ok c r = isDig c (rdDig r (natSub c 48) 2 ok) (ok (rdLetter c) r)
rdLetter c = natIfEq c 98 8 (natIfEq c 116 9 (natIfEq c 110 10 (natIfEq c 118 11 (natIfEq c 102 12 (natIfEq c 114 13 c)))))
rdDig r v m ok = m |> { Zero (ok v r); Suc j (r (ok v r) (rdDigC r v j ok)) }
rdDigC r v j ok c u = isDig c (rdDig u (natAdd (natMul v 10) (natSub c 48)) j ok) (ok v r)
rdStr r cs acc fail k = r fail (rdStrC cs acc fail k)
rdStrC cs acc fail k c u = natIfEq c 34 (rd u (Push (Str (rdText cs TNil)) acc) fail k) (natIfEq c 92 (rdEsc u fail (rdStrK cs acc fail k)) (rdStr u (cons c cs) acc fail k))
rdStrK cs acc fail k code rest = rdStr rest (cons code cs) acc fail k
rdText cs t = cs t (rdTextC t)
rdTextC t c r = rdText r (TCons (Pos c) t)
-- a token: to a space or a bracket; a number, or a word
rdTok r tr acc fail k = r (rdWord tr nil acc fail k) (rdTokC r tr acc fail k)
rdTokC r tr acc fail k c u = isSp c (rdWord tr r acc fail k) (isBr c (rdWord tr r acc fail k) (rdTok u (cons c tr) acc fail k))
rdWord tr rest acc fail k = rdAtom (rdRev tr nil) (rdWordK rest acc fail k)
rdWordK rest acc fail k x = rd rest (Push x acc) fail k
rdRev z a = z a (rdRevC a)
rdRevC a c r = rdRev r (cons c a)
rdAtom t j = rdDigits t (rdDec t 0 (rdPos j)) (rdNeg t j)
rdPos j m = j (Num (Pos m))
rdNegK j m = j (Num (negN m))
rdNeg t j = t (j (rdName t)) (rdNegC t j)
rdNegC t j c u = natIfEq c 45 (rdDigits u (rdDec u 0 (rdNegK j)) (j (rdName t))) (j (rdName t))
rdDigits t x y = t y (rdDigitsC x y)
rdDigitsC x y c r = isDig c (rdAllDig r x y) y
rdAllDig r x y = r x (rdAllDigC x y)
rdAllDigC x y c u = isDig c (rdAllDig u x y) y
-- a decimal's value, rebuilt as data at each digit
rdDec t v j = t (j v) (rdDecC v j)
rdDecC v j c r = nfNat (natAdd (natMul v 10) (natSub c 48)) (rdDecK r j)
rdDecK r j v = rdDec r v j
-- byte lists in order: lt, eq or gt
cmpB a b lt eq gt = a (b eq (K (K lt))) (cmpBC b lt eq gt)
cmpBC b lt eq gt x u = b gt (cmpBD x u lt eq gt)
cmpBD x u lt eq gt y v = natIfEq x y (cmpB u v lt eq gt) (natIfLe x y lt gt)
rdMiss t = Sym (Def (User (fromCodes (doorText t)) Done))
@NAMES@
-- a poke's value from the cards so far and the rest: [cards state].  Each
-- is forced, a pair applied to its continuation, so the poke's weak head
-- normal form is the run to its stop: the run's work is the poke's, and
-- counted, not left for the runtime's probes of the cards
doorWr c p = p (doorWrK c)
doorWrK c cs st = [(cons c cs) st]
-- a card's bytes are data before it goes out: the list and each numeral
-- rebuilt, so the work that made them is the poke's, where a runtime's
-- probes would redo a thunk's for every byte
doorWrite bs p = nfBytes bs (doorWriteK p)
doorWriteK p bs = doorWr [1 [1 bs]] p
nfBytes bs k = bs (k nil) (nfBytesC k)
nfBytesC k h t = nfNat h (nfBytesH t k)
nfBytesH t k h = nfBytes t (nfBytesT h k)
nfBytesT h k t = k (cons h t)
nfNat n k = n |> { Zero (k 0); Suc m (nfNat m (nfNatS k)) }
nfNatS k m = k (Suc m)
doorEnd code = [(cons [5 code] nil) [[nil [nil K]] [Done [Empty ctxProg]]]]
doorAsk c e q s f = [(cons c nil) [e [q [s f]]]]
doorAskEnv e q s f bs = doorAsk [3 [1 bs]] e q s f
-- a run's context: a program alone, or a file's term, the terms after it
-- and the stack it began on
ctxProg p g = p
ctxFile ts s0 p g = g ts s0
doorGo r e f = r |> { RVal s (f (doorEnd 0) (doorNext s e)); RErr (doorFail e f); RTime (f (doorEnd 1) (doorSay @FUEL@ e)); RIO n s q (doorIo n s q e f) }
doorOn q s e f = doorGo (execU q s) e f
doorFail e f = f (doorEnd 1) (doorSay @ERROR@ e)
doorSay msg e ts s0 = doorWrite msg (doorTerm ts s0 e)
doorNext s e ts s0 = s |> { Empty (doorTerm ts Empty e); Push x t (doorWrite (wrItem x (cons 10 nil)) (doorTerm ts t e)) }
doorAbort s e ts s0 = doorTerm ts s e
doorTerm ts s e = ts (doorEnd 0) (doorTermC s e)
doorTermC s e p r = doorOn p s e (ctxFile r s)
doorPut s q e f = s |> { Empty (doorFail e f); Push x t (doorWrite (wrItem x nil) (doorOn q t e f)) }
doorPutch s q e f = s |> { Empty (doorFail e f); Push x t (x |> { Num c (doorWrite (cons (doorByte c) nil) (doorOn q t e f)); Quot p (doorFail e f); Logical l (doorFail e f); Sym w (doorFail e f); Char c (doorWrite (cons (doorByte c) nil) (doorOn q t e f)); Str z (doorFail e f); Set z (doorFail e f) }) }
doorPutchars s q e f = s |> { Empty (doorFail e f); Push x t (x |> { Num c (doorFail e f); Quot p (doorFail e f); Logical l (doorFail e f); Sym w (doorFail e f); Char c (doorFail e f); Str z (doorWrite (doorBytes z) (doorOn q t e f)); Set z (doorFail e f) }) }
doorGetenv s q e f = s |> { Empty (doorFail e f); Push x t (x |> { Num c (doorFail e f); Quot p (doorFail e f); Logical l (doorFail e f); Sym w (doorFail e f); Char c (doorFail e f); Str z (nfBytes (doorBytes z) (doorAskEnv e q t f)); Set z (doorFail e f) }) }
-- get: a factor from the input held, the input consumed to its end even
-- where it does not read; more input asked for where none is whole
doorGet s q e f = doorGetZ (dropSp (6@e)) s q e f
doorGetZ z s q e f = z ((7@e) (doorFail e f) (doorMore s q e f)) (doorGetC z s q e f)
doorGetC z s q e f c r = fe z 0 0 (doorGot z s q e f)
doorGot z s q e f n rest = rest ((7@e) (doorRead (listTake z n) rest s q e f) (doorMore s q e f)) (doorGotC (listTake z n) rest s q e f)
doorGotC fz rest s q e f h t = doorRead fz rest s q e f
doorRead fz rest s q e f = rdFactor fz (doorFail [(2@e) [rest (7@e)]] f) (doorPushed s q [(2@e) [rest (7@e)]] f)
doorPushed s q e f x = doorOn q (Push x s) e f
doorMore s q e f = doorAsk [2 [3 [0 @MAX@]]] e q s f
doorIo n s q e f = natIfEq n @put@ (doorPut s q e f) (natIfEq n @putch@ (doorPutch s q e f) (natIfEq n @putchars@ (doorPutchars s q e f) (natIfEq n @get@ (doorGet s q e f) (natIfEq n @argc@ (doorOn q (Push (Num (Pos (listLength (2@e)))) s) e f) (natIfEq n @argv@ (doorOn q (Push (Quot (doorArgv (2@e))) s) e f) (natIfEq n @getenv@ (doorGetenv s q e f) (natIfEq n @clock@ (doorAsk [4 2] e q s f) (natIfEq n @abort@ (f (doorEnd 0) (doorAbort s e)) (natIfEq n @quit@ (doorEnd 0) (doorEnd 2))))))))))
-- a reply: id 0 boot's [argv bits], 1 getenv's value, 2 clock's count, 3 a read's bytes
doorStart v st = doorOn (6@st) (14@st) [(2@v) [nil (K I)]] (15@st)
doorEnv v st = doorOn (6@st) (Push (v (Str TNil) doorEnvC) (14@st)) (2@st) (15@st)
doorClock v st = doorOn (6@st) (Push (Num (Pos v)) (14@st)) (2@st) (15@st)
-- the bytes read join the input held as data, rebuilt once, where an
-- append left as a thunk would be redone by every get after it
doorFed v st = nfBytes (listAppend (6@(2@st)) v) (doorFedK v st)
doorFedK v st z = doorGet (14@st) (6@st) [(2@(2@st)) [z (v K (K (K (K I))))]] (15@st)
doorStep id v st = natIfEq id 0 (doorStart v st) (natIfEq id 1 (doorEnv v st) (natIfEq id 2 (doorClock v st) (doorFed v st)))
doorPoke b r = r (doorPokeK b)
doorPokeK b cs st = [cs [b st]]
poke k ev = doorPoke (2@k) (doorStep (6@ev) (7@ev) (3@k))
peek k p = 3@k
load k old = [(2@k) old]
"""


def _names() -> str:
    """``rdName``, the reader's table: a word's item for every name Joy
    has as its own (``Run.word_term``), ``true`` and ``false`` truth
    values, any other name an undefined symbol; a binary search over the
    names' bytes, one equation a node."""
    entries: List[Tuple[str, str]] = [("true", "(Logical True)"), ("false", "(Logical False)")]
    entries += [(nm, f"(Sym {w})") for nm, w in joy.KERNEL.items() if not w.startswith("(")]
    entries += [(nm, f"(Sym (Ext {c}))") for nm, c in joy.EXT.items()]
    entries += [(nm, f"(Sym (Ext (Io {joy.nat(joy.IO_CODES[nm])})))") for nm in joy.IO]
    entries.sort(key=lambda e: e[0].encode())
    lines: List[str] = []

    def node(lo: int, hi: int) -> str:
        if lo >= hi:
            return "(rdMiss t)"
        mid = (lo + hi) // 2
        k = len(lines)
        lines.append("")
        nm, item = entries[mid]
        lines[k] = (f"rn{k} t = cmpB t {_bytes(nm, 'nil')} "
                    f"{node(lo, mid)} {item} {node(mid + 1, hi)}")
        return f"(rn{k} t)"
    root = node(0, len(entries))
    return "".join(f"{ln}\n" for ln in lines) + f"rdName t = {root}\n"


def _door() -> str:
    fills = {"FALSE": _bytes("false", "acc"), "TRUE": _bytes("true", "acc"),
             "FUEL": _bytes("out of fuel\n", "nil"), "ERROR": _bytes("run time error\n", "nil"),
             "MAX": str(READ_MAX), "NAMES": _names()}
    fills.update({name: str(code) for name, code in joy.IO_CODES.items()})
    out = DOOR
    for k, v in fills.items():
        out = out.replace(f"@{k}@", v)
    return out


def source(programs: Dict[str, str], defs: Dict[str, str] = joy.DEFINITIONS) -> str:
    """The interpreted kernel with ``programs``, and for each program ``P``
    a door ``kP`` that runs it."""
    out = [joy.interpreted(programs, defs, io_named=True), _door()]
    for name in programs:
        out.append(f"k{name} := [[poke [peek load]] [[nil [nil K]] [p{name} [Empty ctxProg]]]]\n")
    return "".join(out)


def file_source(text: str) -> str:
    """The interpreted kernel with a Joy file's terms, and ``kfile``, the
    door that runs them in order as ``joyfile.run_text`` does."""
    own, terms = joyfile._terms(text)
    programs = {f"t{i}": t for i, t in enumerate(terms)}
    rest = "nil"
    for name in reversed(list(programs)):
        rest = f"(cons p{name} {rest})"
    return (joy.interpreted(programs, dict(joy.DEFINITIONS, **own), io_named=True) + _door()
            + f"kfile := [[poke [peek load]] [[nil [nil K]] [Done [Empty (ctxFile {rest} Empty)]]]]\n")


# A card list holds cells of different types, which skijack's Stage B has
# no type for, so a door compiles with checking off.

def doors(programs: Dict[str, str], defs: Dict[str, str] = joy.DEFINITIONS):
    """Each program's door, compiled: ``{name: kernel term}``."""
    e = abstraction.compile(source(programs, defs), check=False)
    return {name: e.terms[f"k{name}"] for name in programs}


def file_door(text: str):
    """A Joy file's door, compiled."""
    return abstraction.compile(file_source(text), check=False).terms["kfile"]


def main(argv=None) -> int:
    """``python -m skilark.door FILE.joy``: the file's door on standard
    output, as Avon's DAG text, for ``avon run --kernel``."""
    import sys
    from skijack.avon import _encode
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: python -m skilark.door FILE.joy > DOOR", file=sys.stderr)
        return 2
    with open(args[0], encoding="utf-8") as f:
        sys.stdout.write(_encode(file_door(f.read()))[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
