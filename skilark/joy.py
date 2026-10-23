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
from typing import Dict, Iterable, List, Sequence, Union

Token = Union[int, str, List["Token"]]
Program = List[Token]

DIR = pathlib.Path(__file__).parent / "programs"

#: Joy's kernel words and the constructor (interpreted) each compiles to
KERNEL = {
    "dup": "Dup", "swap": "Swap", "pop": "Pop", "cons": "Qcons", "cat": "Cat",
    "unit": "Unit", "dip": "Dip", "i": "Do", "ifz": "Ifz", "+": "Add",
    "*": "Mul", "succ": "Succ", "pred": "Pred", "max": "Max", "min": "Min",
    "=": "Eql", "<": "Lt", "and": "And", "or": "Or", "not": "Not",
    "branch": "Branch", "ifte": "Ifte",
    "true": "(Truth True)", "false": "(Truth False)",
}

#: the words that take a quotation and run it, so their compiled form takes
#: the eliminator
APPLYING = ("i", "dip", "ifz", "branch", "ifte")

#: the words that make or test a truth value; a compiled program carries
#: truth values on its stack only when it uses one
TRUTH_WORDS = {"=", "<", "and", "or", "not", "branch", "ifte", "true", "false"}

#: Joy's own definitions of the derived words, and Kerby's k and y
DEFINITIONS = {
    "over": "[dup] dip swap",
    "nip": "[pop] dip",
    "tuck": "dup [swap] dip",
    "rot": "[swap] dip swap",
    "sip": "[dup] dip dip",
    "k": "[pop] dip i",
    "y": "[dup cons] swap cat dup cons i",
    "sumto": "[swap [pop 0] [dup [swap i] dip 1 + +] ifz] y",
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
        elif t.isdigit():
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
        elif isinstance(t, str) and t not in KERNEL and t not in keep:
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


def _kernel() -> str:
    return (DIR / "kernel.ascii.ski").read_text(encoding="utf-8")


def _programs(programs: Dict[str, str], defs: Dict[str, str],
              keep: Iterable[str] = ()) -> Dict[str, Program]:
    return {name: expand(parse(src), defs, keep) for name, src in programs.items()}


# ------------------------------------------------------------ interpreted

def datum(prog: Program) -> str:
    """A program as a ``prog`` expression; a kept name is a scry."""
    if not prog:
        return "Done"
    t, rest = prog[0], datum(prog[1:])
    if isinstance(t, int):
        return f"Then (Lit {nat(t)}) ({rest})"
    if isinstance(t, list):
        return f"Then (Quote ({datum(t)})) ({rest})"
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
logical === False | True
item   === Num nat | Quot quot{LITEM}
stack  === Empty | Push item stack
quot   === {QUOTS}QCons item quot | QUnit item | QThen quot
result === RVal stack | RErr | RTime

add m n = n |> {{ Zero m; Suc k (Suc (add m k)) }}

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
wIfz ap s = s |> {{ Empty RErr; Push a t (a |> {{ Num n RErr; Quot sc (t |> {{ Empty RErr; Push b u (b |> {{ Num n RErr; Quot z (u |> {{ Empty RErr; Push c v (c |> {{ Num n (n |> {{ Zero (ap z v); Suc m (ap sc (Push (Num m) v)) }}); Quot r RErr{LC} }}) }}){LC} }}) }}){LC} }}) }}
wLit n s = RVal (Push (Num n) s)
wQuote r s = RVal (Push (Quot r) s)
wAdd s = s |> {{ Empty RErr; Push a t (t |> {{ Empty RErr; Push b u (a |> {{ Num m (b |> {{ Num n (RVal (Push (Num (add m n)) u)); Quot r RErr{LC} }}); Quot r RErr{LC} }}) }}) }}

-- numbers, x below y on the stack; pred of 0 is an error until integers
-- are signed
mul m n = n |> {{ Zero Zero; Suc k (add m (mul m k)) }}
less m n = n |> {{ Zero False; Suc j (m |> {{ Zero True; Suc i (less i j) }}) }}
num2 f s = s |> {{ Empty RErr; Push a t (t |> {{ Empty RErr; Push b u (a |> {{ Num m (b |> {{ Num n (RVal (Push (f n m) u)); Quot r RErr{LC} }}); Quot r RErr{LC} }}) }}) }}
mulI n m = Num (mul n m)
maxI n m = Num (less n m |> {{ False n; True m }})
minI n m = Num (less n m |> {{ False m; True n }})
wMul s = num2 mulI s
wMax s = num2 maxI s
wMin s = num2 minI s
wSucc s = s |> {{ Empty RErr; Push a t (a |> {{ Num n (RVal (Push (Num (Suc n)) t)); Quot r RErr{LC} }}) }}
wPred s = s |> {{ Empty RErr; Push a t (a |> {{ Num n (n |> {{ Zero RErr; Suc m (RVal (Push (Num m) t)) }}); Quot r RErr{LC} }}) }}
{TRUTH}
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
applyK k q s = q |> {{ {CASES_F}QCons x r (k r (Push x s)); QUnit x (RVal (Push x s)); QThen b (seq (wDo k) (k b) s) }}
timeout q s = RTime
applyU q s = q |> {{ {CASES_U}QCons x r (applyU r (Push x s)); QUnit x (RVal (Push x s)); QThen b (seq (wDo applyU) (applyU b) s) }}
"""


#: the compiled truth-value words, present only in a program that uses one
#: (``TRUTH_WORDS``): the item constructor ``Logical`` changes every term
#: that cases on an item, so a program without truth values keeps its terms
COMPILED_TRUTH = """
-- truth values
same m n = m |> {{ Zero (n |> {{ Zero True; Suc j False }}); Suc i (n |> {{ Zero False; Suc j (same i j) }}) }}
both a b = a |> {{ False False; True b }}
either a b = a |> {{ False b; True True }}
negate a = a |> {{ False True; True False }}
iff a b = a |> {{ False (negate b); True b }}
lessI n m = Logical (less n m)
bothI b c = Logical (both b c)
eitherI b c = Logical (either b c)
log2 f s = s |> {{ Empty RErr; Push a t (t |> {{ Empty RErr; Push b u (a |> {{ Num m RErr; Quot r RErr; Logical d (b |> {{ Num n RErr; Quot r RErr; Logical c (RVal (Push (f c d) u)) }}) }}) }}) }}
wTruth b s = RVal (Push (Logical b) s)
wLt s = num2 lessI s
wAnd s = log2 bothI s
wOr s = log2 eitherI s
wNot s = s |> {{ Empty RErr; Push a t (a |> {{ Num n RErr; Quot r RErr; Logical b (RVal (Push (Logical (negate b)) t)) }}) }}
wEql s = s |> {{ Empty RErr; Push a t (t |> {{ Empty RErr; Push b u (a |> {{ Num m (b |> {{ Num n (RVal (Push (Logical (same n m)) u)); Quot r RErr; Logical c RErr }}); Quot r RErr; Logical d (b |> {{ Num n RErr; Quot r RErr; Logical c (RVal (Push (Logical (iff c d)) u)) }}) }}) }}) }}
-- x [T] [F] branch: T or F by the truth value x
wBranch ap s = s |> {{ Empty RErr; Push a t (a |> {{ Num n RErr; Quot f (t |> {{ Empty RErr; Push b u (b |> {{ Num n RErr; Quot r (u |> {{ Empty RErr; Push c v (c |> {{ Num n RErr; Quot l RErr; Logical d (d |> {{ True (ap r v); False (ap f v) }}) }}) }}); Logical d RErr }}) }}); Logical d RErr }}) }}
-- [B] [T] [F] ifte: B on the stack, then T or F on the stack as it was
pick r f o = o |> {{ RVal w (w |> {{ Empty RErr; Push a x (a |> {{ Num n RErr; Quot l RErr; Logical d (d |> {{ True r; False f }}) }}) }}); RErr RErr; RTime RTime }}
wIfte ap s = s |> {{ Empty RErr; Push a t (a |> {{ Num n RErr; Quot f (t |> {{ Empty RErr; Push b u (b |> {{ Num n RErr; Quot r (u |> {{ Empty RErr; Push c v (c |> {{ Num n RErr; Quot l (pick (ap r v) (ap f v) (ap l v)); Logical d RErr }}) }}); Logical d RErr }}) }}); Logical d RErr }}) }}
"""


def _uses_truth(progs: Iterable[Program]) -> bool:
    """Whether any program, or any quotation in one, uses a truth word."""
    def walk(p: Program) -> bool:
        return any(walk(t) if isinstance(t, list) else t in TRUTH_WORDS for t in p)
    return any(walk(p) for p in progs)


def _compiled_kernel(n: int, truth: bool) -> str:
    """The compiled kernel for ``n`` static quotations, with truth values
    when ``truth``."""
    lc = "; Logical lg RErr" if truth else ""
    return COMPILED_KERNEL.format(
        QUOTS="".join(f"Q{k} | " for k in range(1, n + 1)),
        CASES_F="".join(f"Q{i} (b{i} k s); " for i in range(1, n + 1)),
        CASES_U="".join(f"Q{k} (b{k} applyU s); " for k in range(1, n + 1)),
        LITEM=" | Logical logical" if truth else "", LC=lc,
        TRUTH=COMPILED_TRUTH.format() if truth else "")


class _Compiler:
    def __init__(self) -> None:
        self.quots: List[Program] = []
        self.index: Dict[str, int] = {}

    def quot(self, q: Program) -> str:
        key = words(q)
        if key not in self.index:
            self.index[key] = len(self.quots) + 1
            self.quots.append(q)
        return f"Q{self.index[key]}"

    def word(self, t: Token, ap: str = "ap", keep: Iterable[str] = ()) -> str:
        if isinstance(t, int):
            return f"(wLit {nat(t)})"
        if isinstance(t, list):
            return f"(wQuote {self.quot(t)})"
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
    c = _Compiler()
    progs = _programs(programs, defs)
    tops = {name: c.body(prog) for name, prog in progs.items()}
    bodies: List[str] = []
    i = 0
    while i < len(c.quots):                 # quot() may append while we walk
        bodies.append(f"b{i + 1} ap = {c.body(c.quots[i])}")
        i += 1
    kernel = _compiled_kernel(len(c.quots), _uses_truth(progs.values()))
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
topIs v r = r |> {{ RVal s (s |> {{ Empty (S S); Push a t (a |> {{ Num n (eqNat n v); Quot q (S K K){LC} }}) }}); RErr (S K); RTime (S I) }}
"""


def level1_reader(truth: bool) -> str:
    """The level-1 reader for a kernel whose items include truth values
    when ``truth``: a truth value on top answers ``S S K``."""
    return _LEVEL1_READER.format(LC="; Logical b (S S K)" if truth else "")


#: the reader for the interpreted kernel, whose items include truth values
LEVEL1_READER = level1_reader(True)


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
        truth = True
        facts = {n: datum(expand(parse(defs[n]), defs)) for n in keep}
        runs = {name: f"execU ({datum(prog)}) Empty" for name, prog in progs.items()}
        hoisted: List[str] = []
    elif form == "compiled":
        c = _Compiler()
        facts = {n: c.body(expand(parse(defs[n]), defs), "applyU") for n in keep}
        runs = {name: f"{c.body(prog, 'applyU', keep)} Empty" for name, prog in progs.items()}
        hoisted = []
        i = 0
        while i < len(c.quots):
            hoisted.append(f"b{i + 1} ap = {c.body(c.quots[i])}")
            i += 1
        facts_progs = [expand(parse(defs[n]), defs) for n in keep]
        truth = _uses_truth(list(progs.values()) + facts_progs)
        kernel = _compiled_kernel(len(c.quots), truth)
    else:
        raise ValueError(f"unknown form {form!r}")
    out = [kernel, "\n".join(hoisted) + ("\n" if hoisted else ""),
           LEVEL1_KERNEL.format(SEGS=" | ".join(segment(n) for n in keep)),
           level1_reader(truth),
           "\ndict := ns{" + ", ".join(f"/{n} => <{v}>" for n, v in facts.items()) + "}\n",
           f"\n-- programs, from skilark.joy.level1 ({form} form)\n"]
    for name, run in runs.items():
        out.append(f"r{name} := wfN dict |- <topIs {nat(value)} ({run})>@{fuel}\n")
        out.append(f"n{name} := wfN dict |- <topIs {nat(value + 1)} ({run})>@{fuel}\n")
    return "".join(out)
