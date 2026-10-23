"""The Joy front end: text to programs, in three forms.

A Joy program is whitespace-separated words, numerals and bracketed
quotations.  Derived words are definitions ``name == body`` and are
inlined at their use, so the program's own names are its dictionary and
nothing is looked up at run time -- except, at level 1, the names the
caller leaves in the namespace, which the program reads by scry.

Three generators take the same parsed program and return SKIjack source:

``interpreted``
    the kernel of ``programs/kernel.ascii.ski`` plus each program as a
    ``prog`` datum, run by ``exec`` (fuel per word) and ``execU``.
``compiled``
    every word a function ``stack -> result``, a program the composition
    of its words, and quotations *defunctionalized*: each static quotation
    is a constructor of a closed sum ``quot`` whose body is its compiled
    composition, and ``cons``, ``unit`` and ``cat`` build ``QCons``,
    ``QUnit`` and ``QThen`` at run time (``[P] [Q] cat`` is ``[[P] i Q]``,
    so no constructor carries two fields of its own type and SKIjack does
    not take ``quot`` for an object type).  ``apply`` is the eliminator,
    so Joy's ``i`` is one case dispatch and every field stays first-order.
``level1``
    the interpreted kernel under ``wfN``: definitions named in
    ``namespace`` become facts ``ns{ /name => <prog> }`` and each use is a
    scry at the position the front end wrote it.
"""

from __future__ import annotations

import pathlib
from typing import Dict, Iterable, List, Optional, Sequence, Union

Token = Union[int, str, List["Token"]]
Program = List[Token]

DIR = pathlib.Path(__file__).parent / "programs"

#: Joy's kernel words and the constructor (interpreted) each compiles to
KERNEL = {
    "dup": "Dup", "swap": "Swap", "pop": "Pop", "cons": "Qcons", "cat": "Cat",
    "unit": "Unit", "dip": "Dip", "i": "Do", "+": "Add", "-": "Sub",
    "*": "Mul", "/": "Div", "rem": "Rem", "=": "Eql", "<": "Lt",
    "branch": "Branch", "ifte": "Ifte",
    "true": "(Truth True)", "false": "(Truth False)",
    "uncons": "Uncons", "null": "Null", "small": "Small",
}

#: ``ifz``, the Scott eliminator of a natural (``n [Z] [S] ifz``: Z at 0,
#: else S with n - 1 pushed), is not Joy and has left the kernel; the
#: compiled form keeps it for natural-number programs, zk's verifiers among
#: them, whose terms lean-ski proves
COMPILED_ONLY = {"ifz"}

#: the words that take a quotation and run it, so their compiled form takes
#: the eliminator
APPLYING = ("i", "dip", "ifz", "branch", "ifte")

#: the words that make or test a truth value; a compiled program carries
#: truth values on its stack only when it uses one
TRUTH_WORDS = {"=", "<", "branch", "ifte", "true", "false", "null", "small"}

#: the words that can make a negative number; a compiled program without
#: one of them or a negative literal computes on naturals, which give it
#: the same answers
SIGNED_WORDS = {"-", "/", "rem"}

#: the words that read a quotation as a list; a compiled program reads its
#: quotations' elements, symbols among them, only when it uses one
LIST_WORDS = {"uncons", "null", "small"}

#: Joy's own definitions of the derived words, and Kerby's k and y
DEFINITIONS = {
    "over": "[dup] dip swap",
    "nip": "[pop] dip",
    "tuck": "dup [swap] dip",
    "rot": "[swap] dip swap",
    "sip": "[dup] dip dip",
    "k": "[pop] dip i",
    "y": "[dup cons] swap cat dup cons i",
    "sumto": "[swap [0 =] [pop pop 0] [dup pred swap [swap i] dip +] ifte] y",
    "neg": "0 swap -",
    "succ": "1 +",
    "pred": "1 -",
    "max": "over over < [swap pop] [pop] branch",
    "min": "over over < [pop] [swap pop] branch",
    "not": "[false] [true] branch",
    "and": "not not swap [] [pop false] branch",
    "or": "not not swap [pop true] [] branch",
    "first": "uncons pop",
    "rest": "uncons swap pop",
    "swons": "swap cons",
    "unswons": "uncons swap",
    "concat": "cat",
    "size": "[swap [null] [pop pop 0] [rest swap i 1 +] ifte] y",
    "drop": "[swap [[pop null] dip 0 = or] [pop pop] [pred swap [[rest] dip] dip i] ifte] y",
    "take": "[swap [[pop null] dip 0 = or] [pop pop pop []] [pred [[uncons] dip] dip swap i cons] ifte] y",
    "at": "drop first",
    "of": "swap at",
    "abs": "dup 0 < [0 swap -] [] branch",
    "sign": "dup 0 < [pop -1] [0 = [0] [1] branch] branch",
    ">": "swap <",
    "<=": "swap < not",
    ">=": "< not",
    "!=": "= not",
    "xor": "!=",
    "fact": "[swap [0 =] [pop pop 1] [dup pred swap [swap i] dip *] ifte] y",
}


# ------------------------------------------------------------------ parsing

def parse(text: str) -> Program:
    """``"3 [dup +] i"`` -> ``[3, ['dup', '+'], 'i']``."""
    toks = text.replace("[", " [ ").replace("]", " ] ").split()
    stack: List[Program] = [[]]
    for t in toks:
        if t == "[":
            stack.append([])
        elif t == "]":
            if len(stack) == 1:
                raise ValueError("unbalanced ']'")
            q = stack.pop()
            stack[-1].append(q)
        elif t.isdigit() or (t[0] == "-" and t[1:].isdigit()):
            stack[-1].append(int(t))
        else:
            stack[-1].append(t)
    if len(stack) != 1:
        raise ValueError("unbalanced '['")
    return stack[0]


def parse_definitions(text: str) -> Dict[str, str]:
    """``"over == [dup] dip swap"`` lines -> a definitions table."""
    defs: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        name, body = (s.strip() for s in line.split("==", 1))
        defs[name] = body
    return defs


def expand(prog: Program, defs: Dict[str, str], keep: Iterable[str] = ()
           ) -> Program:
    """Inline every derived word except those in ``keep``."""
    keep = set(keep)
    out: Program = []
    for t in prog:
        if isinstance(t, list):
            out.append(expand(t, defs, keep))
        elif isinstance(t, str) and t in defs and t not in keep:
            out.extend(expand(parse(defs[t]), defs, keep))
        elif (isinstance(t, str) and t not in KERNEL and t not in COMPILED_ONLY
              and t not in keep):
            raise ValueError(f"unknown word {t!r}")
        else:
            out.append(t)
    return out


def words(prog: Program) -> str:
    """A program back as Joy text."""
    return " ".join(f"[{words(t)}]" if isinstance(t, list) else str(t)
                    for t in prog)


# ----------------------------------------------------------------- helpers

def nat(n: int) -> str:
    return "Zero" if n == 0 else f"(Suc {nat(n - 1)})" if n > 1 else "(Suc Zero)"


def integer(n: int) -> str:
    """An integer as the kernel's ``int``: ``Pos m`` is m, ``Neg m`` is -(m+1)."""
    return f"(Pos {nat(n)})" if n >= 0 else f"(Neg {nat(-n - 1)})"


def _walk(progs: Iterable[Program], hit) -> bool:
    """Whether ``hit`` holds of any token of the programs or their quotations."""
    def walk(p: Program) -> bool:
        return any(walk(t) if isinstance(t, list) else hit(t) for t in p)
    return any(walk(p) for p in progs)


def _uses_truth(progs: Iterable[Program]) -> bool:
    """Whether any program, or any quotation in one, uses a truth word."""
    return _walk(progs, lambda t: t in TRUTH_WORDS)


def _uses_lists(progs: Iterable[Program]) -> bool:
    """Whether any program reads a quotation as a list."""
    return _walk(progs, lambda t: t in LIST_WORDS)


def _uses_signs(progs: Iterable[Program]) -> bool:
    """Whether any program can make a negative number: a signed word or a
    negative literal."""
    return _walk(progs, lambda t: t in SIGNED_WORDS or (isinstance(t, int) and t < 0))


def _kernel() -> str:
    return (DIR / "kernel.ascii.ski").read_text(encoding="utf-8")


def _programs(programs: Dict[str, str], defs: Dict[str, str],
              keep: Iterable[str] = ()) -> Dict[str, Program]:
    return {name: expand(parse(src), defs, keep) for name, src in programs.items()}


# ------------------------------------------------------------ interpreted

def datum(prog: Program, basis: bool = False) -> str:
    """A program as a ``prog`` expression; a kept name is a scry.  With
    ``basis``, for the basis kernel (``programs/basis.ascii.ski``): its
    literals are naturals and it has ``Ifz``."""
    if not prog:
        return "Done"
    t, rest = prog[0], datum(prog[1:], basis)
    if isinstance(t, int):
        if basis and t < 0:
            raise ValueError(f"the basis kernel has no negative numbers: {t}")
        return f"Then (Lit {nat(t) if basis else integer(t)}) ({rest})"
    if isinstance(t, list):
        return f"Then (Quote ({datum(t, basis)})) ({rest})"
    if basis and t == "ifz":
        return f"Then Ifz ({rest})"
    if t in COMPILED_ONLY:
        raise ValueError(f"{t!r} is not a Joy word; only the compiled form keeps it")
    if t in KERNEL:
        return f"Then {KERNEL[t]} ({rest})"
    return f"cat ?^/{t} ({rest})"


def interpreted(programs: Dict[str, str], defs: Dict[str, str] = DEFINITIONS
                ) -> str:
    """The kernel plus, for each program ``p``: ``pP``, ``rP`` (fuelled)
    and ``uP`` (unfuelled)."""
    out = [_kernel(), "\n-- programs, from skilark.joy.interpreted\n"]
    for name, prog in _programs(programs, defs).items():
        out.append(f"p{name} := {datum(prog)}\n")
        out.append(f"r{name} := exec fuel p{name} Empty\n")
        out.append(f"u{name} := execU p{name} Empty\n")
    return "".join(out)


# --------------------------------------------------------------- compiled

COMPILED_KERNEL = """\
-- SKIlark, compiled: every word a function stack -> result, a program the
-- composition of its words, quotations defunctionalized (skilark.joy).
nat    === Zero | Suc nat
{INTTYPE}logical === False | True
{SYMTYPE}item   === Num {NUM} | Quot quot{LITEM}
stack  === Empty | Push item stack
quot   === {QUOTS}QCons item quot | QUnit item | QThen quot
result === RVal stack | RErr | RTime

-- composition, threading the result
seq f g s = f s |> {{ RVal t (g t); RErr RErr; RTime RTime }}
idW s = RVal s

wDup s = s |> {{ Empty RErr; Push a t (RVal (Push a (Push a t))) }}
wSwap s = s |> {{ Empty RErr; Push a t (t |> {{ Empty RErr; Push b u (RVal (Push b (Push a u))) }}) }}
wPop s = s |> {{ Empty RErr; Push a t (RVal t) }}
wQcons s = s |> {{ Empty RErr; Push a t (a |> {{ Num n RErr; Quot r (t |> {{ Empty RErr; Push b u (RVal (Push (Quot (QCons b r)) u)) }}){LC} }}) }}
-- [P] [Q] cat == [[P] i Q]: cons the left quotation onto "i then Q"
wCat s = s |> {{ Empty RErr; Push a t (a |> {{ Num n RErr; Quot r (t |> {{ Empty RErr; Push b u (b |> {{ Num m RErr; Quot l (RVal (Push (Quot (QCons (Quot l) (QThen r))) u)){LC} }}) }}){LC} }}) }}
wUnit s = s |> {{ Empty RErr; Push a t (RVal (Push (Quot (QUnit a)) t)) }}
wDip ap s = s |> {{ Empty RErr; Push a t (a |> {{ Num n RErr; Quot r (t |> {{ Empty RErr; Push b u (ap r u |> {{ RVal v (RVal (Push b v)); RErr RErr; RTime RTime }}) }}){LC} }}) }}
wDo ap s = s |> {{ Empty RErr; Push a t (a |> {{ Num n RErr; Quot r (ap r t){LC} }}) }}
wLit n s = RVal (Push (Num n) s)
wQuote r s = RVal (Push (Quot r) s)
{NUMBERS}{TRUTH}{LISTS}
one   := Suc Zero
two   := Suc one
five  := Suc (Suc (Suc two))
-- fuel: Church numerals, f applied n times; fuel is 200
ten f x    = f (f (f (f (f (f (f (f (f (f x)))))))))
twenty f x = ten f (ten f x)
fuel f x   = ten (twenty f) x

-- the eliminator of quot: Joy's i is one case.  Fuel is a Church numeral,
-- one unfolding of applyK per quotation applied, k the next
apply f q s = f applyK timeout q s
applyK k q s = q |> {{ {CASES_F}QCons x r {CONS_F}; QUnit x {UNIT_F}; QThen b (seq (wDo k) (k b) s) }}
timeout q s = RTime
applyU q s = q |> {{ {CASES_U}QCons x r {CONS_U}; QUnit x {UNIT_U}; QThen b (seq (wDo applyU) (applyU b) s) }}
"""


#: a compiled program's numbers when none can be negative (``SIGNED_WORDS``):
#: naturals, with ``ifz``
COMPILED_NATURALS = """
-- numbers, naturals: x below y on the stack
add m n = n |> {{ Zero m; Suc k (Suc (add m k)) }}
mul m n = n |> {{ Zero Zero; Suc k (add m (mul m k)) }}
less m n = n |> {{ Zero False; Suc j (m |> {{ Zero True; Suc i (less i j) }}) }}
same m n = m |> {{ Zero (n |> {{ Zero True; Suc j False }}); Suc i (n |> {{ Zero False; Suc j (same i j) }}) }}
num2 f s = s |> {{ Empty RErr; Push a t (t |> {{ Empty RErr; Push b u (a |> {{ Num m (b |> {{ Num n (RVal (Push (f n m) u)); Quot r RErr{LC} }}); Quot r RErr{LC} }}) }}) }}
mulI n m = Num (mul n m)
zero n = n |> {{ Zero True; Suc k False }}
upToOne n = n |> {{ Zero True; Suc k (k |> {{ Zero True; Suc j False }}) }}
wAdd s = s |> {{ Empty RErr; Push a t (t |> {{ Empty RErr; Push b u (a |> {{ Num m (b |> {{ Num n (RVal (Push (Num (add m n)) u)); Quot r RErr{LC} }}); Quot r RErr{LC} }}) }}) }}
wMul s = num2 mulI s
-- n [Z] [S] ifz: Z at 0, else S with n - 1 pushed
wIfz ap s = s |> {{ Empty RErr; Push a t (a |> {{ Num n RErr; Quot sc (t |> {{ Empty RErr; Push b u (b |> {{ Num n RErr; Quot z (u |> {{ Empty RErr; Push c v (c |> {{ Num n (n |> {{ Zero (ap z v); Suc m (ap sc (Push (Num m) v)) }}); Quot r RErr{LC} }}) }}){LC} }}) }}){LC} }}) }}
"""

#: a compiled program's numbers when one can be negative: the kernel's
#: integers, a sign and a magnitude
COMPILED_INTEGERS = """
-- numbers, integers: Pos m is m, Neg m is -(m+1); x below y on the stack
add m n = n |> {{ Zero m; Suc k (Suc (add m k)) }}
mul m n = n |> {{ Zero Zero; Suc k (add m (mul m k)) }}
lessN m n = n |> {{ Zero False; Suc j (m |> {{ Zero True; Suc i (lessN i j) }}) }}
sameN m n = m |> {{ Zero (n |> {{ Zero True; Suc j False }}); Suc i (n |> {{ Zero False; Suc j (sameN i j) }}) }}
monus m n = n |> {{ Zero m; Suc j (m |> {{ Zero Zero; Suc i (monus i j) }}) }}
divN m n = lessN m n |> {{ False (Suc (divN (monus m n) n)); True Zero }}
remN m n = lessN m n |> {{ False (remN (monus m n) n); True m }}
differ a b = a |> {{ False b; True (b |> {{ False True; True False }}) }}
negN k = k |> {{ Zero (Pos Zero); Suc j (Neg j) }}
diff m n = m |> {{ Zero (negN n); Suc i (n |> {{ Zero (Pos m); Suc j (diff i j) }}) }}
mag z = z |> {{ Pos m m; Neg m (Suc m) }}
isNeg z = z |> {{ Pos m False; Neg m True }}
signed s k = s |> {{ False (Pos k); True (negN k) }}
plus a b = a |> {{ Pos m (b |> {{ Pos n (Pos (add m n)); Neg n (diff m (Suc n)) }}); Neg m (b |> {{ Pos n (diff n (Suc m)); Neg n (Neg (Suc (add m n))) }}) }}
minus z = z |> {{ Pos m (negN m); Neg m (Pos (Suc m)) }}
times a b = signed (differ (isNeg a) (isNeg b)) (mul (mag a) (mag b))
divide a b = signed (differ (isNeg a) (isNeg b)) (divN (mag a) (mag b))
modulo a b = signed (isNeg a) (remN (mag a) (mag b))
less a b = a |> {{ Pos m (b |> {{ Pos n (lessN m n); Neg n False }}); Neg m (b |> {{ Pos n True; Neg n (lessN n m) }}) }}
same a b = a |> {{ Pos m (b |> {{ Pos n (sameN m n); Neg n False }}); Neg m (b |> {{ Pos n False; Neg n (sameN m n) }}) }}
num2 f s = s |> {{ Empty RErr; Push a t (t |> {{ Empty RErr; Push b u (a |> {{ Num m (b |> {{ Num n (RVal (Push (f n m) u)); Quot r RErr{LC} }}); Quot r RErr{LC} }}) }}) }}
div2 f s = s |> {{ Empty RErr; Push a t (t |> {{ Empty RErr; Push b u (a |> {{ Num m (b |> {{ Num n (mag m |> {{ Zero RErr; Suc k (RVal (Push (f n m) u)) }}); Quot r RErr{LC} }}); Quot r RErr{LC} }}) }}) }}
zero z = z |> {{ Pos m (m |> {{ Zero True; Suc k False }}); Neg m False }}
upToOne z = z |> {{ Pos m (m |> {{ Zero True; Suc k (k |> {{ Zero True; Suc j False }}) }}); Neg m False }}
addI n m = Num (plus n m)
subI n m = Num (plus n (minus m))
mulI n m = Num (times n m)
divI n m = Num (divide n m)
remI n m = Num (modulo n m)
wAdd s = num2 addI s
wSub s = num2 subI s
wMul s = num2 mulI s
wDiv s = div2 divI s
wRem s = div2 remI s
"""

#: the compiled truth-value words, present only in a program that uses one
#: (``TRUTH_WORDS``): the item constructor ``Logical`` changes every term
#: that cases on an item, so a program without truth values keeps its terms
COMPILED_TRUTH = """
-- truth values
negate a = a |> {{ False True; True False }}
iff a b = a |> {{ False (negate b); True b }}
lessI n m = Logical (less n m)
wTruth b s = RVal (Push (Logical b) s)
wLt s = num2 lessI s
wEql s = s |> {{ Empty RErr; Push a t (t |> {{ Empty RErr; Push b u (a |> {{ Num m (b |> {{ Num n (RVal (Push (Logical (same n m)) u)); Quot r RErr; Logical c RErr{LS} }}); Quot r RErr; Logical d (b |> {{ Num n RErr; Quot r RErr; Logical c (RVal (Push (Logical (iff c d)) u)){LS} }}){SYMEQ} }}) }}) }}
-- x [T] [F] branch: T or F by the truth value x
wBranch ap s = s |> {{ Empty RErr; Push a t (a |> {{ Num n RErr; Quot f (t |> {{ Empty RErr; Push b u (b |> {{ Num n RErr; Quot r (u |> {{ Empty RErr; Push c v (c |> {{ Num n RErr; Quot l RErr; Logical d (d |> {{ True (ap r v); False (ap f v) }}){LS} }}) }}); Logical d RErr{LS} }}) }}); Logical d RErr{LS} }}) }}
-- [B] [T] [F] ifte: B on the stack, then T or F on the stack as it was
pick r f o = o |> {{ RVal w (w |> {{ Empty RErr; Push a x (a |> {{ Num n RErr; Quot l RErr; Logical d (d |> {{ True r; False f }}){LS} }}) }}); RErr RErr; RTime RTime }}
wIfte ap s = s |> {{ Empty RErr; Push a t (a |> {{ Num n RErr; Quot f (t |> {{ Empty RErr; Push b u (b |> {{ Num n RErr; Quot r (u |> {{ Empty RErr; Push c v (c |> {{ Num n RErr; Quot l (pick (ap r v) (ap f v) (ap l v)); Logical d RErr{LS} }}) }}); Logical d RErr{LS} }}) }}); Logical d RErr{LS} }}) }}
"""


#: a compiled program's list words, present only in a program that reads a
#: quotation as a list (``LIST_WORDS``): ``Sym`` items, each static
#: quotation's first element and rest (``viewQ``), and the dispatch that runs
#: a symbol consed back into a quotation
COMPILED_LISTS = """
-- quotations as lists.  [P] [Q] cat is [[P] i Q], so a cons of a quotation
-- onto QThen is P's elements, then Q's
view === VEmpty | VCons item quot
natEq m n = m |> {{ Zero (n |> {{ Zero True; Suc j False }}); Suc i (n |> {{ Zero False; Suc j (natEq i j) }}) }}
symNo y = y |> {{ {SYMNO} }}
symRun ap y = y |> {{ {SYMRUN} }}
consRun k x r s = x |> {{ Num n (k r (Push x s)); Quot q (k r (Push x s)); Logical b (k r (Push x s)); Sym y (seq (symRun k y) (k r) s) }}
catView vq x r = r |> {{ {CATQ}QCons y o (VCons x r); QUnit y (VCons x r); QThen b (x |> {{ Num n (VCons x r); Quot l (vq l |> {{ VEmpty (vq b); VCons y m (VCons y (QCons (Quot m) (QThen b))) }}); Logical c (VCons x r); Sym z (VCons x r) }}) }}
viewQ q = q |> {{ {VIEWS}QCons x r (catView viewQ x r); QUnit x (VCons x {QE}); QThen b (viewQ b) }}
wUncons s = s |> {{ Empty RErr; Push a t (a |> {{ Num n RErr; Quot r (viewQ r |> {{ VEmpty RErr; VCons x p (RVal (Push (Quot p) (Push x t))) }}); Logical c RErr; Sym y RErr }}) }}
wNull s = s |> {{ Empty RErr; Push a t (a |> {{ Num n (RVal (Push (Logical (zero n)) t)); Quot r (RVal (Push (Logical (viewQ r |> {{ VEmpty True; VCons x p False }})) t)); Logical c RErr; Sym y RErr }}) }}
wSmall s = s |> {{ Empty RErr; Push a t (a |> {{ Num n (RVal (Push (Logical (upToOne n)) t)); Quot r (RVal (Push (Logical (viewQ r |> {{ VEmpty True; VCons x p (viewQ p |> {{ VEmpty True; VCons y o False }}) }})) t)); Logical c RErr; Sym y RErr }}) }}
"""


class _Lists:
    """What a list-reading program's compiled kernel needs from its
    compiler: the symbols, and each static quotation's view."""

    def __init__(self, syms: List[str], views: List[str], qe: str,
                 sym_run: List[str]) -> None:
        self.syms, self.views, self.qe, self.sym_run = syms, views, qe, sym_run


def _compiled_kernel(n: int, truth: bool, signs: bool,
                     lists: "Optional[_Lists]" = None) -> str:
    """The compiled kernel for ``n`` static quotations, with truth values
    when ``truth``, integers when ``signs`` (else naturals), and the list
    words when ``lists``."""
    ls = "; Sym sy RErr" if lists else ""
    lc = ("; Logical lg RErr" if truth else "") + ls
    numbers = COMPILED_INTEGERS if signs else COMPILED_NATURALS
    symeq = ("; Sym y (b |> { Num n RErr; Quot r RErr; Logical c RErr; Sym z "
             "(RVal (Push (Logical (natEq (symNo z) (symNo y))) u)) })") if lists else ""
    if lists:
        syms = lists.syms or ["YNone"]
        cons_f, unit_f = "(consRun k x r s)", f"(consRun k x {lists.qe} s)"
        cons_u, unit_u = "(consRun applyU x r s)", f"(consRun applyU x {lists.qe} s)"
        block = COMPILED_LISTS.format(
            SYMNO="; ".join(f"{y} {nat(i)}" for i, y in enumerate(syms)),
            SYMRUN="; ".join(lists.sym_run or ["YNone idW"]),
            CATQ="".join(f"Q{k} (VCons x r); " for k in range(1, n + 1)),
            VIEWS="".join(f"Q{k} {v}; " for k, v in enumerate(lists.views, start=1)),
            QE=lists.qe)
        symtype = f"sym    === {' | '.join(syms)}\n"
    else:
        cons_f, unit_f = "(k r (Push x s))", "(RVal (Push x s))"
        cons_u, unit_u = "(applyU r (Push x s))", "(RVal (Push x s))"
        block, symtype = "", ""
    return COMPILED_KERNEL.format(
        QUOTS="".join(f"Q{k} | " for k in range(1, n + 1)),
        CASES_F="".join(f"Q{i} (b{i} k s); " for i in range(1, n + 1)),
        CASES_U="".join(f"Q{k} (b{k} applyU s); " for k in range(1, n + 1)),
        LITEM=(" | Logical logical" if truth else "") + (" | Sym sym" if lists else ""),
        LC=lc, SYMTYPE=symtype,
        CONS_F=cons_f, UNIT_F=unit_f, CONS_U=cons_u, UNIT_U=unit_u,
        INTTYPE="int    === Pos nat | Neg nat\n" if signs else "",
        NUM="int" if signs else "nat",
        NUMBERS=numbers.format(LC=lc),
        TRUTH=COMPILED_TRUTH.format(LS=ls, SYMEQ=symeq) if truth else "",
        LISTS=block)


class _Compiler:
    """Bodies for one program set; ``signs`` when its numbers are integers."""

    def __init__(self, signs: bool, lists: bool = False) -> None:
        self.quots: List[Program] = []
        self.index: Dict[str, int] = {}
        self.signs, self.lists = signs, lists
        self.syms: Dict[str, str] = {}          # symbol constructor -> its run

    def literal(self, n: int) -> str:
        return integer(n) if self.signs else nat(n)

    def item(self, t: Token) -> str:
        """A static quotation's element as an item: a literal its value, a
        word a symbol."""
        if isinstance(t, int):
            return f"(Num {self.literal(t)})"
        if isinstance(t, list):
            return f"(Quot {self.quot(t)})"
        if t in ("true", "false"):
            return f"(Logical {t.capitalize()})"
        name = "Y" + ("Ifz" if t == "ifz" else KERNEL[t])
        self.syms.setdefault(name, f"{name} {self.word(t, 'ap')}")
        return f"(Sym {name})"

    def hoist(self) -> List[str]:
        """Every static quotation's body; with lists, also every suffix of
        one, so that a quotation's rest is a static quotation too."""
        bodies: List[str] = []
        i = 0
        while i < len(self.quots):          # quot() may append while we walk
            q = self.quots[i]
            if self.lists and q:
                self.quot(q[1:])
            bodies.append(f"b{i + 1} ap = {self.body(q)}")
            i += 1
        return bodies

    def list_info(self) -> "Optional[_Lists]":
        """The views of the static quotations, once they are all hoisted."""
        if not self.lists:
            return None
        qe = self.quot([])
        views = []
        for q in list(self.quots):
            views.append("VEmpty" if not q else
                         f"(VCons {self.item(q[0])} {self.quot(q[1:])})")
        if len(views) != len(self.quots):
            raise AssertionError("a view added a quotation after hoisting")
        return _Lists(sorted(self.syms), views, qe,
                      [self.syms[k] for k in sorted(self.syms)])

    def quot(self, q: Program) -> str:
        key = words(q)
        if key not in self.index:
            self.index[key] = len(self.quots) + 1
            self.quots.append(q)
        return f"Q{self.index[key]}"

    def word(self, t: Token, ap: str = "ap", keep: Iterable[str] = ()) -> str:
        if isinstance(t, int):
            return f"(wLit {self.literal(t)})"
        if isinstance(t, list):
            return f"(wQuote {self.quot(t)})"
        if t == "ifz":
            if self.signs:
                raise ValueError("ifz takes naturals; this program's numbers are integers")
            return f"(wIfz {ap})"
        if t in ("true", "false"):
            return f"(wTruth {t.capitalize()})"
        if t in APPLYING:
            return f"(w{KERNEL[t]} {ap})"
        if t in KERNEL:
            return f"w{KERNEL[t]}"
        if t in keep:
            return f"?^/{t}"
        raise ValueError(f"no compiled form for {t!r}")

    def body(self, prog: Program, ap: str = "ap", keep: Iterable[str] = ()
             ) -> str:
        if not prog:
            return "idW"
        ws = [self.word(t, ap, keep) for t in prog]
        out = ws[-1]
        for w in reversed(ws[:-1]):
            out = f"seq {w} ({out})"
        return out


def compiled(programs: Dict[str, str], defs: Dict[str, str] = DEFINITIONS
             ) -> str:
    """For each program ``p``: ``cP`` (its body, taking the eliminator),
    ``rP`` (under ``apply fuel``, ``fuel`` a Church numeral) and ``uP``
    (under ``applyU``)."""
    progs = _programs(programs, defs)
    signs = _uses_signs(progs.values())
    lists = _uses_lists(progs.values())
    c = _Compiler(signs, lists)
    tops = {name: c.body(prog) for name, prog in progs.items()}
    if lists:
        c.quot([])
    bodies = c.hoist()
    info = c.list_info()
    kernel = _compiled_kernel(len(c.quots), _uses_truth(progs.values()), signs, info)
    out = [kernel, "\n-- static quotations, hoisted\n"]
    out.extend(f"{b}\n" for b in bodies)
    out.append("\n-- programs, from skilark.joy.compiled\n")
    for name, body in tops.items():
        out.append(f"c{name} ap = {body}\n")
        out.append(f"r{name} := c{name} (apply fuel) Empty\n")
        out.append(f"u{name} := c{name} applyU Empty\n")
    return "".join(out)


# ---------------------------------------------------------------- level 1

LEVEL1_KERNEL = """
-- the object type, typed paths and the blocking interpreter (SKIjack's
-- scry-ns.ski); a segment is a definition's name, capitalized
term5 === S | K | I | App term5 term5 | Scry
seg === {SEGS}
path === Nil | Cons seg path
bool === PTrue | PFalse

oanswer === OJust term5 | ONothing | ONotYet
outcome === SteppedN term5 | DoneN | ErrdN | PendingN term5
result5 === RValN term5 | RErrN | RTimeN | RBlockN term5

pAnd p q = p q PFalse
pKKF = K (K PFalse)
eqApp2P e t u t2 u2 = pAnd (e t t2) (e u u2)
eqApp1P e n t u = n PFalse PFalse PFalse (eqApp2P e t u) PFalse
eqNP e m n = (m (n PTrue  PFalse PFalse pKKF PFalse)
                (n PFalse PTrue  PFalse pKKF PFalse)
                (n PFalse PFalse PTrue  pKKF PFalse)
                (eqApp1P e n)
                (n PFalse PFalse PFalse pKKF PTrue))
EQ5 m = eqNP EQ5 m

scHitN rest v = SteppedN (rb v rest)

wfN e := {{
  stepScry1 p rest = e p (scHitN rest) ErrdN (PendingN p)
  stepScry args    = args DoneN (stepScry1 e)
}}
"""


def segment(name: str) -> str:
    if not name.isalpha():
        raise ValueError(f"a namespace name must be alphabetic: {name!r}")
    return name[0].upper() + name[1:]


_LEVEL1_READER = """
-- the answer, read inside the run.  A level-1 result is a term in weak
-- head normal form, so anything it carries as an argument is an unreduced
-- closure, and the encoded closure has lost its sharing: decoding a
-- numeral n this way costs 2^n nodes.  So the run answers a question
-- instead -- is the top of the stack this numeral? -- with the ABI's
-- booleans, K for yes and K I for no, which are atoms alone; the other
-- outcomes are S applied to atoms.
eqNat a b = a |> {{ Zero (b |> {{ Zero K; Suc n (K I) }}); Suc m (b |> {{ Zero (K I); Suc n (eqNat m n) }}) }}
topIs v r = r |> {{ RVal s (s |> {{ Empty (S S); Push a t (a |> {{ Num n {TEST}; Quot q (S K K){LC} }}) }}); RErr (S K); RTime (S I) }}
"""


def level1_reader(truth: bool, signs: bool, lists: bool = False) -> str:
    """The level-1 reader for a kernel whose items include truth values
    when ``truth`` (a truth value on top answers ``S S K``), whose numbers
    are integers when ``signs`` (a negative is not the natural asked for),
    and whose items include symbols when ``lists`` (``S S I``)."""
    test = "(n |> {{ Pos m (eqNat m v); Neg m (K I) }})" if signs else "(eqNat n v)"
    lc = ("; Logical b (S S K)" if truth else "") + ("; Sym y (S S I)" if lists else "")
    return _LEVEL1_READER.format(LC=lc, TEST=test.format())


#: the reader for the interpreted kernel: truth values, integers, symbols
LEVEL1_READER = level1_reader(True, True, True)


def level1(programs: Dict[str, str], namespace: Sequence[str],
           fuel: int, defs: Dict[str, str] = DEFINITIONS,
           form: str = "interpreted", value: int = 0) -> str:
    """The kernel of ``form`` under ``wfN``.  Each name in ``namespace``
    is a fact whose value is its (inlined) definition -- a ``prog`` datum
    in the interpreted form, a compiled body in the compiled form -- and
    each program is asked whether its final top of stack is ``value``:
    ``rP := wfN dict |- <topIs <value> (...)>@fuel``, and ``nP`` the same
    for ``value + 1`` as the control, with the namespace's names left in
    as scries at the positions they occur (``LEVEL1_READER``).

    In the compiled form a namespace name may occur only at the top
    level of a program, since a scry compiles only inside the quotation
    and a static quotation's body is an equation outside it."""
    keep = list(namespace)
    progs = _programs(programs, defs, keep)
    if form == "interpreted":
        kernel = _kernel()
        truth = signs = lists = True
        facts = {n: datum(expand(parse(defs[n]), defs)) for n in keep}
        runs = {name: f"execU ({datum(prog)}) Empty" for name, prog in progs.items()}
        hoisted: List[str] = []
    elif form == "compiled":
        facts_progs = [expand(parse(defs[n]), defs) for n in keep]
        every = list(progs.values()) + facts_progs
        signs, lists = _uses_signs(every), _uses_lists(every)
        c = _Compiler(signs, lists)
        facts = {n: c.body(expand(parse(defs[n]), defs), "applyU") for n in keep}
        runs = {name: f"{c.body(prog, 'applyU', keep)} Empty" for name, prog in progs.items()}
        if lists:
            c.quot([])
        hoisted = c.hoist()
        truth = _uses_truth(every)
        kernel = _compiled_kernel(len(c.quots), truth, signs, c.list_info())
    else:
        raise ValueError(f"unknown form {form!r}")
    out = [kernel, "\n".join(hoisted) + ("\n" if hoisted else ""),
           LEVEL1_KERNEL.format(SEGS=" | ".join(segment(n) for n in keep)),
           level1_reader(truth, signs, lists),
           "\ndict := ns{" + ", ".join(f"/{n} => <{v}>" for n, v in facts.items()) + "}\n",
           f"\n-- programs, from skilark.joy.level1 ({form} form)\n"]
    for name, run in runs.items():
        out.append(f"r{name} := wfN dict |- <topIs {nat(value)} ({run})>@{fuel}\n")
        out.append(f"n{name} := wfN dict |- <topIs {nat(value + 1)} ({run})>@{fuel}\n")
    return "".join(out)
