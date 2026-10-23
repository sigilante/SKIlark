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
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

Token = Union[int, str, "Def", List["Token"]]
Program = List[Token]


class Def:
    """A derived word inside a quotation: Joy reads it there as the symbol
    it names, and runs it as its body.  At the top of a program, or of a
    body, a derived word is inlined, since nothing can read it there."""

    def __init__(self, name: str, body: "Program") -> None:
        self.name, self.body = name, body

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Def) and (self.name, self.body) == (other.name, other.body)

    def __repr__(self) -> str:
        return f"Def({self.name!r})"

DIR = pathlib.Path(__file__).parent / "programs"

#: Joy's kernel words and the constructor (interpreted) each compiles to
KERNEL = {
    "dup": "Dup", "swap": "Swap", "pop": "Pop", "cons": "Qcons", "cat": "Cat",
    "unit": "Unit", "dip": "Dip", "i": "Do", "+": "Add", "-": "Sub",
    "*": "Mul", "/": "Div", "rem": "Rem", "=": "Eql", "<": "Lt",
    "branch": "Branch", "ifte": "Ifte",
    "true": "(Truth True)", "false": "(Truth False)",
    "uncons": "Uncons", "null": "Null", "small": "Small",
    "stack": "Stack", "unstack": "Unstack",
}

#: a kernel symbol's Joy name, by its constructor
NAMES = {v: k for k, v in KERNEL.items() if not v.startswith("(")}

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

#: the words that read a quotation as a list, or make one of the stack; a
#: compiled program reads its quotations' elements, symbols among them,
#: only when it uses one
LIST_WORDS = {"uncons", "null", "small", "stack", "unstack"}

#: The derived words: Joy's, as the reference implementation (Wodan58/Joy)
#: behaves, and Kerby's k and y.  A reference builtin derived here checks
#: its arguments where the kernel words it is made of check them: the
#: guards ``dup 0 * pop`` (an integer) and ``dup dup cat pop`` (an
#: aggregate) restore checks a definition would otherwise skip.  The
#: combinators take their quotations into the body ``y`` recurses on, so
#: the stack they run on is the caller's; ``map`` and ``filter`` run each
#: element on the caller's stack with ``infra``.
DEFINITIONS = {
    # stack words
    "over": "[dup] dip swap",
    "nip": "[pop] dip",
    "tuck": "dup [swap] dip",
    "rot": "[swap] dip swap",
    "sip": "[dup] dip dip",
    "dupd": "[dup] dip",
    "swapd": "[swap] dip",
    "popd": "[pop] dip",
    "rollup": "swap [swap] dip",
    "rolldown": "[swap] dip swap",
    "rotate": "swap [swap] dip swap",
    "id": "",
    # Kerby's combinators
    "k": "[pop] dip i",
    "y": "[dup cons] swap cat dup cons i",
    "x": "dup i",
    # arithmetic
    "neg": "0 swap -",
    "succ": "1 +",
    "pred": "1 -",
    "abs": "dup 0 * pop dup 0 < [0 swap -] [] branch",
    "sign": "dup 0 * pop dup 0 < [pop -1] [0 = [0] [1] branch] branch",
    "max": "over over < [swap pop] [pop] branch",
    "min": "over over < [pop] [swap pop] branch",
    # comparison: = and < are the kernel's, and the others are what the
    # reference's comparison gives, which orders some values neither way
    ">": "over over < [pop pop false] [!=] branch",
    "<=": "over over < [pop pop true] [=] branch",
    ">=": "< not",
    "!=": "= not",
    # truth values: any value is one, zero and empty false
    "not": "[false] [true] branch",
    "and": "not not swap not not [] [pop false] branch",
    "or": "not not swap not not [pop true] [] branch",
    "xor": "!=",
    # lists
    "first": "uncons pop",
    "rest": "uncons swap pop",
    "swons": "swap cons",
    "unswons": "uncons swap",
    "concat": "cat",
    "size": "dup dup cat pop [swap [null] [pop pop 0] [rest swap i 1 +] ifte] y",
    "drop": "dup 0 < [[] first] [] branch [dup dup cat pop] dip "
            "[swap [[pop null] dip 0 = or] [pop pop] [pred swap [[rest] dip] dip i] ifte] y",
    "take": "dup 0 < [[] first] [] branch [dup dup cat pop] dip "
            "[swap [[pop null] dip 0 = or] [pop pop pop []] [pred [[uncons] dip] dip swap i cons] ifte] y",
    "at": "drop first",
    "of": "swap at",
    # the stack as data
    "nullary": "[stack] dip infra first",
    "infra": "[[stack] dip] dip [stack] cat rolldown unit cat [cons unstack] cat [unstack] dip i",
    # the recursion combinators
    "times": "[dup 0 * pop] dip swap "
             "[swap [0 >] [pred [[dup [i] dip] dip] dip swap i] [pop pop pop] ifte] y",
    "while": "[[pop swap pop i] [swap pop swap [i] dip i] [pop pop pop] ifte] cons cons y",
    "tailrec": "[[pop pop swap pop i] [pop swap pop swap pop i] "
               "[swap pop swap pop swap [i] dip i] ifte] cons cons cons y",
    "linrec": "[[pop pop pop swap pop i] [pop pop swap pop swap pop i] "
              "[[[pop pop] dip] dip [i] swap cat [swap] dip cons cat i] ifte] cons cons cons cons y",
    "binrec": "[[pop pop pop swap pop i] [pop pop swap pop swap pop i] "
              "[[[pop pop] dip] dip [i] swap cat [swap] dip [dup] dip cons [dip] swap cat "
              "swap [i] cons swap cons cat i] ifte] cons cons cons cons y",
    "genrec": "[[pop pop pop swap pop i] [pop pop swap pop swap pop i] "
              "[[[pop pop] dip] dip rolldown [i] cons swap cons cat i] ifte] cons cons cons cons y",
    "primrec": "[[pop] swap cat [0 > not] swap [dup dup = [dup pred] [uncons] branch]] dip linrec",
    "map": "[dup dup cat pop] dip [[stack] dip] dip [swap] dip [infra first] cons [cons] swap cat cons "
           "[i] cons unit [dip] cat [uncons] swap cat [[null] []] dip [cons] linrec",
    "filter": "[dup dup cat pop] dip [[stack] dip] dip [swap] dip [infra first] cons [cons] swap cat cons "
              "[i] cons [dup] swap cat unit [dip] cat [uncons] swap cat [[null] []] dip "
              "[swap [cons] [swap pop] branch] linrec",
    "step": "[dup dup cat pop] dip [pop null] [pop pop] [[uncons] dip swap [dup [i] dip] dip swap] tailrec",
    "fold": "swapd step",
    # programs
    "sumto": "[swap [0 =] [pop pop 0] [dup pred swap [swap i] dip +] ifte] y",
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


def expand(prog: Program, defs: Dict[str, str], keep: Iterable[str] = (),
           quoted: bool = False) -> Program:
    """Inline every derived word except those in ``keep``; inside a
    quotation (``quoted``) a derived word is a ``Def`` of its expansion."""
    keep = set(keep)
    out: Program = []
    for t in prog:
        if isinstance(t, list):
            out.append(expand(t, defs, keep, True))
        elif isinstance(t, str) and t in defs and t not in keep:
            body = expand(parse(defs[t]), defs, keep)
            if quoted:
                out.append(Def(t, body))
            else:
                out.extend(body)
        elif (isinstance(t, str) and t not in KERNEL and t not in COMPILED_ONLY
              and t not in keep):
            raise ValueError(f"unknown word {t!r}")
        else:
            out.append(t)
    return out


def words(prog: Program) -> str:
    """A program back as Joy text."""
    return " ".join(f"[{words(t)}]" if isinstance(t, list) else
                    t.name if isinstance(t, Def) else str(t) for t in prog)


def flatten(prog: Program) -> Program:
    """A program with every ``Def`` replaced by its body: Joy's runs
    without its reading of a derived word as a symbol."""
    out: Program = []
    for t in prog:
        if isinstance(t, Def):
            out.extend(flatten(t.body))
        elif isinstance(t, list):
            out.append(flatten(t))
        else:
            out.append(t)
    return out


def splice(prog: Program) -> Program:
    """A program's own words with each ``Def`` replaced by its body, its
    quotations kept as they are: what runs."""
    out: Program = []
    for t in prog:
        if isinstance(t, Def):
            out.extend(splice(t.body))
        else:
            out.append(t)
    return out


# ----------------------------------------------------------------- helpers

def nat(n: int) -> str:
    return "Zero" if n == 0 else f"(Suc {nat(n - 1)})" if n > 1 else "(Suc Zero)"


def integer(n: int) -> str:
    """An integer as the kernel's ``int``: ``Pos m`` is m, ``Neg m`` is -(m+1)."""
    return f"(Pos {nat(n)})" if n >= 0 else f"(Neg {nat(-n - 1)})"


def _walk(progs: Iterable[Program], hit) -> bool:
    """Whether ``hit`` holds of any token of the programs, their quotations
    or the bodies of their ``Def``s."""
    def walk(p: Program) -> bool:
        return any(walk(t) if isinstance(t, list) else
                   walk(t.body) if isinstance(t, Def) else hit(t) for t in p)
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

#: the kernel's constants for the characters of a name
_CHARS = {"!": "cBang", "+": "cPlus", "-": "cMinus", "*": "cStar", "/": "cSlash",
          "<": "cLt", "=": "cEq", ">": "cGt"}


def name_text(name: str) -> str:
    """A name as the kernel's ``text``, its characters the kernel's
    constants (``ca`` .. ``cz`` and the operators')."""
    out = "TNil"
    for c in reversed(name):
        if c in _CHARS:
            k = _CHARS[c]
        elif "a" <= c <= "z":
            k = "c" + c
        else:
            raise ValueError(f"no character constant for {c!r} in {name!r}")
        out = f"(TCons {k} {out})"
    return out


def datum(prog: Program, basis: bool = False) -> str:
    """A program as a ``prog`` expression; a kept name is a scry.  With
    ``basis``, for the basis kernel (``programs/basis.ascii.ski``): its
    literals are naturals and it has ``Ifz``."""
    if not prog:
        return "Done"
    t, rest = prog[0], datum(prog[1:], basis)
    if isinstance(t, Def):
        if basis:                       # the basis kernel has no symbols
            return datum(flatten(t.body) + list(prog[1:]), basis)
        return f"Then (Def (Named {name_text(t.name)} ({datum(t.body)}))) ({rest})"
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
upToOne z = z |> {{ Pos m (m |> {{ Zero True; Suc k (k |> {{ Zero True; Suc j False }}) }}); Neg m True }}
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
-- truth values, and the reference's comparison and truth value of any
-- value (compare.h, boolean.h): two null values are the same; numbers and
-- truth values by value; symbols by name; anything else is More
order  === Less | Same | More
negate a = a |> {{ False True; True False }}
both a b = a |> {{ False False; True b }}
cmpN m n = m |> {{ Zero (n |> {{ Zero Same; Suc j Less }}); Suc i (n |> {{ Zero More; Suc j (cmpN i j) }}) }}
{CMPZ}
-- a quotation is empty when it is a static empty one, or [P] [Q] cat of
-- two empty ones; QThen stands only as the tail of a cat
catEmpty eq x r = r |> {{ {QFALSE}QCons y o False; QUnit y False; QThen b (x |> {{ Num n False; Quot l (both (eq l) (eq b)); Logical c False{SYMFALSE} }}) }}
emptyQ q = q |> {{ {EMPTIES}QCons x r (catEmpty emptyQ x r); QUnit x False; QThen b (emptyQ b) }}
nullish x = x |> {{ Num n (zero n); Quot q (emptyQ q); Logical b (negate b){SYMFALSE} }}
cmpI x y = x |> {{ Num m (y |> {{ Num n (cmpZ m n); Quot q More; Logical c (cmpZ m (boolZ c)){SYMMORE} }}); Quot q More; Logical b (y |> {{ Num n (cmpZ (boolZ b) n); Quot q More; Logical c (cmpZ (boolZ b) (boolZ c)){SYMMORE} }}){SYMCMP} }}
compare x y = both (nullish x) (nullish y) |> {{ True Same; False (cmpI x y) }}
isSame o = o |> {{ Less False; Same True; More False }}
isLess o = o |> {{ Less True; Same False; More False }}
truth x = x |> {{ Num n (negate (zero n)); Quot q (negate (emptyQ q)); Logical b b{SYMTRUE} }}
wTruth b s = RVal (Push (Logical b) s)
wEql s = s |> {{ Empty RErr; Push a t (t |> {{ Empty RErr; Push b u (RVal (Push (Logical (isSame (compare b a))) u)) }}) }}
wLt s = s |> {{ Empty RErr; Push a t (t |> {{ Empty RErr; Push b u (RVal (Push (Logical (isLess (compare b a))) u)) }}) }}
-- x [T] [F] branch: T or F by x as a truth value
wBranch ap s = s |> {{ Empty RErr; Push a t (a |> {{ Num n RErr; Quot f (t |> {{ Empty RErr; Push b u (b |> {{ Num n RErr; Quot r (u |> {{ Empty RErr; Push c v (truth c |> {{ True (ap r v); False (ap f v) }}) }}); Logical d RErr{LS} }}) }}); Logical d RErr{LS} }}) }}
-- [B] [T] [F] ifte: B on the stack, then T or F on the stack as it was
pick r f o = o |> {{ RVal w (w |> {{ Empty RErr; Push a x (truth a |> {{ True r; False f }}) }}); RErr RErr; RTime RTime }}
wIfte ap s = s |> {{ Empty RErr; Push a t (a |> {{ Num n RErr; Quot f (t |> {{ Empty RErr; Push b u (b |> {{ Num n RErr; Quot r (u |> {{ Empty RErr; Push c v (c |> {{ Num n RErr; Quot l (pick (ap r v) (ap f v) (ap l v)); Logical d RErr{LS} }}) }}); Logical d RErr{LS} }}) }}); Logical d RErr{LS} }}) }}
"""

#: the comparison of two numbers, naturals or integers
CMPZ_NATURALS = """boolZ b = b |> {{ False Zero; True (Suc Zero) }}
cmpZ m n = cmpN m n"""
CMPZ_INTEGERS = """boolZ b = b |> {{ False (Pos Zero); True (Pos (Suc Zero)) }}
cmpZ a b = a |> {{ Pos m (b |> {{ Pos n (cmpN m n); Neg n More }}); Neg m (b |> {{ Pos n Less; Neg n (cmpN n m) }}) }}"""


#: a compiled program's list words, present only in a program that reads a
#: quotation as a list (``LIST_WORDS``): ``Sym`` items, each static
#: quotation's first element and rest (``viewQ``), and the dispatch that runs
#: a symbol consed back into a quotation
COMPILED_LISTS = """
-- quotations as lists.  [P] [Q] cat is [[P] i Q], so a cons of a quotation
-- onto QThen is P's elements, then Q's
view === VEmpty | VCons item quot
-- a symbol's place among the program's symbols in the order of their
-- names, so that = and < compare symbols by name
symNo y = y |> {{ {SYMNO} }}
symRun ap y = y |> {{ {SYMRUN} }}
consRun k x r s = x |> {{ Num n (k r (Push x s)); Quot q (k r (Push x s)); Logical b (k r (Push x s)); Sym y (seq (symRun k y) (k r) s) }}
catView vq x r = r |> {{ {CATQ}QCons y o (VCons x r); QUnit y (VCons x r); QThen b (x |> {{ Num n (VCons x r); Quot l (vq l |> {{ VEmpty (vq b); VCons y m (VCons y (QCons (Quot m) (QThen b))) }}); Logical c (VCons x r); Sym z (VCons x r) }}) }}
viewQ q = q |> {{ {VIEWS}QCons x r (catView viewQ x r); QUnit x (VCons x {QE}); QThen b (viewQ b) }}
wUncons s = s |> {{ Empty RErr; Push a t (a |> {{ Num n RErr; Quot r (viewQ r |> {{ VEmpty RErr; VCons x p (RVal (Push (Quot p) (Push x t))) }}); Logical c RErr; Sym y RErr }}) }}
wNull s = s |> {{ Empty RErr; Push a t (RVal (Push (Logical (nullish a)) t)) }}
wSmall s = s |> {{ Empty RErr; Push a t (a |> {{ Num n (RVal (Push (Logical (upToOne n)) t)); Quot r (RVal (Push (Logical (viewQ r |> {{ VEmpty True; VCons x p (viewQ p |> {{ VEmpty True; VCons y o False }}) }})) t)); Logical c (RVal (Push (Logical True) t)); Sym y RErr }}) }}
-- the stack as a list, top first, and a list as the stack
toQ s = s |> {{ Empty {QE}; Push a t (QCons a (toQ t)) }}
fromQ r = viewQ r |> {{ VEmpty Empty; VCons x p (Push x (fromQ p)) }}
wStack s = RVal (Push (Quot (toQ s)) s)
wUnstack s = s |> {{ Empty RErr; Push a t (a |> {{ Num n RErr; Quot r (RVal (fromQ r)); Logical c RErr; Sym y RErr }}) }}
"""


class _Lists:
    """What a list-reading program's compiled kernel needs from its
    compiler: the symbols in the order of their names, their runs, and
    each static quotation's view."""

    def __init__(self, syms: List[str], views: List[str], qe: str,
                 sym_run: List[str]) -> None:
        self.syms, self.views, self.qe, self.sym_run = syms, views, qe, sym_run


#: a derived word's symbol: ``Z`` and its name, an operator's characters
#: spelled out
_MANGLE = {"!": "Bang", "+": "Plus", "-": "Minus", "*": "Star", "/": "Slash",
           "<": "Lt", "=": "Eq", ">": "Gt"}


def def_symbol(name: str) -> str:
    """A derived word's symbol constructor: ``size`` is ``Zsize``, ``!=``
    is ``ZBangEq``."""
    return "Z" + "".join(_MANGLE.get(c, c) for c in name)


def symbol_name(ctor: str) -> str:
    """A compiled symbol's Joy name: ``YDup`` is ``dup``, ``Zsize`` is
    ``size``, ``ZBangEq`` is ``!=``."""
    if ctor.startswith("Y"):
        return "ifz" if ctor == "YIfz" else NAMES[ctor[1:]]
    out, rest = [], ctor[1:]
    back = {v: k for k, v in _MANGLE.items()}
    while rest:
        for spelled, c in back.items():
            if rest.startswith(spelled):
                out.append(c); rest = rest[len(spelled):]
                break
        else:
            out.append(rest[0]); rest = rest[1:]
    return "".join(out)


def _compiled_kernel(n: int, truth: bool, signs: bool,
                     lists: "Optional[_Lists]" = None,
                     empties: Sequence[bool] = ()) -> str:
    """The compiled kernel for ``n`` static quotations (``empties`` says
    which are empty), with truth values when ``truth``, integers when
    ``signs`` (else naturals), and the list words when ``lists``."""
    ls = "; Sym sy RErr" if lists else ""
    lc = ("; Logical lg RErr" if truth else "") + ls
    numbers = COMPILED_INTEGERS if signs else COMPILED_NATURALS
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
    truth_block = ""
    if truth:
        truth_block = COMPILED_TRUTH.format(
            LS=ls,
            CMPZ=(CMPZ_INTEGERS if signs else CMPZ_NATURALS).format(),
            QFALSE="".join(f"Q{k} False; " for k in range(1, n + 1)),
            EMPTIES="".join(f"Q{k} {'True' if e else 'False'}; "
                            for k, e in enumerate(empties, start=1)),
            SYMFALSE="; Sym z False" if lists else "",
            SYMTRUE="; Sym z True" if lists else "",
            SYMMORE="; Sym z More" if lists else "",
            SYMCMP=("; Sym z (y |> { Num n More; Quot q More; Logical c More; "
                    "Sym w (cmpN (symNo z) (symNo w)) })") if lists else "")
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
        TRUTH=truth_block,
        LISTS=block)


class _Compiler:
    """Bodies for one program set; ``signs`` when its numbers are integers,
    ``lists`` when it reads quotations as lists."""

    def __init__(self, signs: bool, lists: bool = False) -> None:
        self.quots: List[Program] = []
        self.index: Dict[str, int] = {}
        self.signs, self.lists = signs, lists
        self.syms: Dict[str, Tuple[str, str]] = {}  # constructor -> (name, run)

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
        if isinstance(t, Def):
            ctor = def_symbol(t.name)
            if ctor not in self.syms:
                self.syms[ctor] = (t.name, "")
                self.syms[ctor] = (t.name, f"{ctor} ({self.body(t.body, 'ap')})")
            return f"(Sym {ctor})"
        ctor = "Y" + ("Ifz" if t == "ifz" else KERNEL[t])
        self.syms.setdefault(ctor, (t, f"{ctor} {self.word(t, 'ap')}"))
        return f"(Sym {ctor})"

    def hoist(self) -> List[str]:
        """Every static quotation's body; with lists, also every suffix of
        one, so that a quotation's rest is a static quotation too, and the
        symbol of every element."""
        bodies: List[str] = []
        i = 0
        while i < len(self.quots):          # quot() may append while we walk
            q = self.quots[i]
            if self.lists and q:
                self.item(q[0])
                self.quot(q[1:])
            bodies.append(f"b{i + 1} ap = {self.body(q)}")
            i += 1
        return bodies

    def empties(self) -> List[bool]:
        """Which static quotations are empty."""
        return [not q for q in self.quots]

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
        order = sorted(self.syms, key=lambda k: self.syms[k][0])
        return _Lists(order, views, qe, [self.syms[k][1] for k in order])

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
        """A program's composition, each ``Def`` spliced as its body."""
        prog = splice(prog)
        if not prog:
            return "idW"
        ws = [self.word(t, ap, keep) for t in prog]
        out = ws[-1]
        for w in reversed(ws[:-1]):
            out = f"seq {w} ({out})"
        return out


def _compile_set(progs: List[Program]):
    """What one program set compiles with: whether its numbers are
    integers, whether it reads lists and whether it uses truth values (a
    program reading lists does).  Without lists nothing reads a derived
    word as a symbol, so its programs are flattened: they compile as they
    did before ``Def``."""
    signs, lists = _uses_signs(progs), _uses_lists(progs)
    return signs, lists, lists or _uses_truth(progs)


def compiled(programs: Dict[str, str], defs: Dict[str, str] = DEFINITIONS
             ) -> str:
    """For each program ``p``: ``cP`` (its body, taking the eliminator),
    ``rP`` (under ``apply fuel``, ``fuel`` a Church numeral) and ``uP``
    (under ``applyU``)."""
    progs = _programs(programs, defs)
    signs, lists, truth = _compile_set(list(progs.values()))
    if not lists:
        progs = {name: flatten(prog) for name, prog in progs.items()}
    c = _Compiler(signs, lists)
    tops = {name: c.body(prog) for name, prog in progs.items()}
    if lists:
        c.quot([])
    bodies = c.hoist()
    info = c.list_info()
    kernel = _compiled_kernel(len(c.quots), truth, signs, info, c.empties())
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
        facts_progs = {n: expand(parse(defs[n]), defs) for n in keep}
        signs, lists, truth = _compile_set(list(progs.values()) + list(facts_progs.values()))
        if not lists:
            progs = {name: flatten(prog) for name, prog in progs.items()}
            facts_progs = {n: flatten(prog) for n, prog in facts_progs.items()}
        c = _Compiler(signs, lists)
        facts = {n: c.body(prog, "applyU") for n, prog in facts_progs.items()}
        runs = {name: f"{c.body(prog, 'applyU', keep)} Empty" for name, prog in progs.items()}
        if lists:
            c.quot([])
        hoisted = c.hoist()
        kernel = _compiled_kernel(len(c.quots), truth, signs, c.list_info(), c.empties())
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
