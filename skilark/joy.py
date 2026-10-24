"""The Joy front end: text to programs, in three forms.

A Joy program is whitespace-separated words, numerals, characters
(``'a``), strings (``"ab"``) and bracketed quotations.  Derived words are definitions ``name == body`` and are
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
import re
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

Token = Union[int, str, "Def", Tuple[str, object], List["Token"]]
Program = List[Token]


class Def:
    """A derived word inside a quotation: Joy reads it there as the symbol
    it names, and runs it as its body.  At the top of a program, or of a
    body, a derived word is inlined, since nothing can read it there.
    ``user`` when the program defines it, not Joy: ``typeof`` tells the
    two apart."""

    def __init__(self, name: str, body: "Program", user: bool = False) -> None:
        self.name, self.body, self.user = name, body, user

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Def) and \
            (self.name, self.body, self.user) == (other.name, other.body, other.user)

    def __repr__(self) -> str:
        return f"Def({self.name!r})"

DIR = pathlib.Path(__file__).parent / "programs"

#: Joy's kernel words and the constructor (interpreted) each compiles to
KERNEL = {
    "dup": "Dup", "swap": "Swap", "pop": "Pop", "cons": "Qcons", "cat": "Cat",
    "unit": "Unit", "dip": "Dip", "i": "Do", "+": "Add", "-": "Sub",
    "*": "Mul", "/": "Div", "rem": "Rem", "=": "Eql", "<": "Lt",
    "branch": "Branch", "ifte": "Ifte",
    "true": "(Lit (Logical True))", "false": "(Lit (Logical False))",
    "uncons": "Uncons", "null": "Null", "small": "Small",
    "stack": "Stack", "unstack": "Unstack", "ord": "Ord", "chr": "Chr",
    "typeof": "Typeof", "not": "Not",
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
TRUTH_WORDS = {"=", "<", "branch", "ifte", "true", "false", "null", "small", "not"}

#: the words that can make a negative number; a compiled program without
#: one of them or a negative literal computes on naturals, which give it
#: the same answers
SIGNED_WORDS = {"-", "/", "rem"}

#: the words that read a quotation as a list, or make one of the stack; a
#: compiled program reads its quotations' elements, symbols among them,
#: only when it uses one
LIST_WORDS = {"uncons", "null", "small", "stack", "unstack"}

#: A derived word's check of its arguments, as the reference's runtime.h
#: makes it: ``[] [] +`` errs, since ``+`` takes no quotation, and it needs
#: no list word.  SAME2TYPES: the top two of one type;
#: NUMERICTYPE: a truth value, a character or an integer (types 4 to 6);
#: a truth value as an integer; POSITIVEINDEX: an integer or a truth value
#: (type 4 or 6), not negative, as an integer; a quotation on top.  None
#: subtracts, so a program on naturals compiles on naturals.
_SAME2 = "over typeof over typeof = [] [[] [] +] branch "
_NUMERIC = "dup typeof dup 3 swap < [7 <] [pop false] branch [] [[] [] +] branch "
_TOINT = "dup logical [[1] [0] branch] [] branch "
_INDEX = ("dup typeof dup 4 = [pop true] [6 =] branch [] [[] [] +] branch " + _TOINT
          + "dup 0 < [[] [] +] [] branch ")
_QUOTE = "dup list [] [[] [] +] branch "
_QUOTES = {1: _QUOTE, 2: f"{_QUOTE}[{_QUOTE}] dip ",
           3: f"{_QUOTE}[{_QUOTE}] dip [[{_QUOTE}] dip] dip ",
           4: f"{_QUOTE}[{_QUOTE}] dip [[{_QUOTE}] dip] dip [[[{_QUOTE}] dip] dip] dip "}
#: map's result on a string is P's result as a C char: its code, modulo 256
#: and signed
_CCHAR = "ord 128 + 128 2 * rem 128 2 * + 128 2 * rem 128 - chr"

#: map, with its string and set branches: a string's results become C
#: chars, a set's integers
_MAP = (_QUOTE + "[dup dup cat pop] dip {STRING}{SET}[[stack] dip] dip [swap] dip [infra first] cons "
        "[cons] swap cat cons [i] cons unit [dip] cat [uncons] swap cat [[null] []] dip "
        "[cons] linrec")
_MAP_STRING = "over string [[" + _CCHAR + "] cat] [] branch "
_MAP_SET = "over set [[" + _TOINT + "] cat] [] branch "

#: The derived words that take a set: (their check, the test that sends a
#: set its own way, the set's body, every other value's body).  A set is
#: Joy's: intersection, union, symmetric difference and complement, the
#: member test, and comprel.h's subset order for > and >=.  The kernel's
#: not is the complement, and concat the union, so the intersection is
#: not X or not Y, complemented, and the symmetric difference X - Y or
#: Y - X, each difference not (not X or Y).
_EITHER_SET = "over set over set [pop true] [] branch "
_SETS = {
    "and": (_SAME2, "dup set ", "not swap not concat not",
            _NUMERIC + "[[true] [false] branch] [pop false] branch"),
    "or": (_SAME2, "dup set ", "concat", _NUMERIC + "[pop true] [[true] [false] branch] branch"),
    "xor": (_SAME2, "dup set ", "over over [not] dip concat not rollup not concat not concat",
            _NUMERIC + "!="),
    # a list's member by =; the value goes in as [X] first, so a symbol
    # stays a value and does not run
    "has": ("", "over set ", "over cons =", "unit [first =] cons filter null not"),
    ">": ("", _EITHER_SET, "swap <", "over over < [pop pop false] [!=] branch"),
    ">=": ("", _EITHER_SET, "swap <=", "< not"),
}


def _body(name: str, strings: bool = True, sets: bool = True) -> str:
    """A word's body, with its string and set branches or without."""
    if name == "map":
        return _MAP.format(STRING=_MAP_STRING if strings else "", SET=_MAP_SET if sets else "")
    check, test, set_body, other = _SETS[name]
    return check + (f"{test}[{set_body}] [{other}] branch" if sets else other)


#: N parameters (runtime.h TWOPARAMS ... FIVEPARAMS): words that err on a
#: shorter stack and leave a long enough one as it was
_PARAMS = {2: "swap swap ", 3: "rotate rotate ", 4: "[rotate rotate] dip ",
           5: "[[rotate rotate] dip] dip "}


def _under(n: int, prog: str) -> str:
    """``prog`` run beneath the top ``n`` items."""
    for _ in range(n):
        prog = f"[{prog}] dip"
    return prog


def _unary_n(n: int) -> str:
    """unary2 .. unary4: P on each of X1 .. Xn with the stack below all n
    beneath it (unary2.c ...).  Ri is nullary of a program that drops the
    n - 1 items above Xi (the X's after it and the results before) and the
    i - 1 below it, then runs P; at the end the X's go."""
    out = _QUOTE + _PARAMS[n + 1]
    for i in range(1, n + 1):
        drop = "pop " * (n - 1) + (_under(1, ("pop " * (i - 1)).strip()) if i > 1 else "")
        out += f"dup [{drop.strip()}] swap cat swap [nullary] dip "
    return out + "pop " + _under(n, ("pop " * n).strip())


#: X [T] [E]: T on X when X is of the type, else E (if_type.h)
def _if_type(test: str) -> str:
    return _QUOTES[2] + f"[[dup {test}] dip] dip branch"


#: The derived words: Joy's, as the reference implementation (Wodan58/Joy)
#: behaves, and Kerby's k and y.  A reference builtin derived here checks
#: its arguments where the reference does: the checks above, made of
#: ``typeof``, and the guards ``dup 0 * pop`` (an integer) and ``dup dup
#: cat pop`` (an aggregate) restore checks a definition would otherwise
#: skip, and a combinator checks its quotations before it runs one.  The
#: checks avoid ``ord``, which would give the compiled form of every
#: program using them characters and strings.  The combinators
#: take their quotations into the body ``y`` recurses on, so the stack
#: they run on is the caller's; ``map`` and ``filter`` run each element on
#: the caller's stack with ``infra``.
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
    "rollupd": "[rollup] dip",
    "rolldownd": "[rolldown] dip",
    "rotated": "[rotate] dip",
    "choice": _PARAMS[3] + "rolldown [pop] [swap pop] branch",
    "id": "",
    # Kerby's combinators
    "k": "[pop] dip i",
    "y": "[dup cons] swap cat dup cons i",
    "x": "dup i",
    # arithmetic
    "neg": "0 swap -",
    "succ": _TOINT + "1 +",
    "pred": _TOINT + "1 -",
    "abs": "dup 0 * pop dup 0 < [0 swap -] [] branch",
    "sign": "dup 0 * pop dup 0 < [pop -1] [0 = [0] [1] branch] branch",
    "max": _SAME2 + _NUMERIC + "over over < [swap pop] [pop] branch " + _TOINT,
    "min": _SAME2 + _NUMERIC + "over over < [pop] [swap pop] branch " + _TOINT,
    # comparison: = and < are the kernel's, and the others are what the
    # reference's comparison gives, which orders some values neither way
    ">": _body(">"),
    "<=": "over over < [pop pop true] [=] branch",
    ">=": _body(">="),
    "!=": "= not",
    # truth values: any value is one, zero and empty false; not is the
    # kernel's
    "and": _body("and"),
    "or": _body("or"),
    "xor": _body("xor"),
    # types: Joy's typeof (globals.h), the tests made of it, and the
    # types SKIlark has no value of
    "integer": "typeof 6 =",
    "char": "typeof 5 =",
    "logical": "typeof 4 =",
    "set": "typeof 7 =",
    "string": "typeof 8 =",
    "list": "typeof 9 =",
    "leaf": "typeof 9 = not",
    "user": "typeof 2 =",
    "float": "pop false",
    "file": "pop false",
    # sametype.c: a builtin symbol on top is the same type as the same
    # builtin alone
    "sametype": "dup typeof 3 = [over typeof 3 = [=] [pop pop false] branch] "
                "[typeof swap typeof =] branch",
    # lists
    "first": "uncons pop",
    "rest": "uncons swap pop",
    "swons": "swap cons",
    "unswons": "uncons swap",
    "concat": "cat",
    "size": "dup dup cat pop [swap [null] [pop pop 0] [rest swap i 1 +] ifte] y",
    "drop": _INDEX + "[dup dup cat pop] dip "
            "[swap [[pop null] dip 0 = [pop true] [] branch] [pop pop] [pred swap [[rest] dip] dip i] ifte] y",
    "take": _INDEX + "[dup dup cat pop] dip "
            "[swap [[pop null] dip 0 = [pop true] [] branch] [pop pop dup size drop] [pred [[uncons] dip] dip swap i cons] ifte] y",
    "at": "drop first",
    "of": "swap at",
    "has": _body("has"),
    "in": "swap has",
    "setsize": "64",
    "enconcat": _SAME2 + "swapd cons concat",
    # split, some and all (split.c, someall.h): some stops at the first
    # member that passes, all at the first that fails
    "split": _QUOTE + "over over filter rollup [[false] [true] branch] cat filter",
    "some": _QUOTE + "[dup dup cat pop] dip [over null [pop pop true] [[first] dip i] branch] "
            "[pop null not] [[rest] dip] tailrec",
    "all": _QUOTE + "[dup dup cat pop] dip "
           "[over null [pop pop true] [[first] dip i [false] [true] branch] branch] "
           "[pop null] [[rest] dip] tailrec",
    # equal.c: lists member by member, anything else by =
    "equal": "[[pop over list over list and] "
             "[[pop over null over null or] [pop null swap null and] "
             "[[[uncons] dip uncons] dip [swapd] dip dup rollupd i swap [rollup] dip i and] ifte] "
             "[pop =] ifte] y",
    # the n-ary combinators (n_ary.h, unary2.c ..., app1.c ..., cleave.c,
    # construct.c): P runs on the stack beneath its arguments
    "app1": _QUOTE + _PARAMS[2] + "i",
    "app11": _QUOTE + _PARAMS[3] + "i popd",
    "app12": _PARAMS[4] + "unary2 rolldown pop",
    "unary": _QUOTE + _PARAMS[2] + "nullary popd",
    "binary": _QUOTE + _PARAMS[3] + "nullary popd popd",
    "ternary": _QUOTE + _PARAMS[4] + "nullary popd popd popd",
    "unary2": _unary_n(2),
    "unary3": _unary_n(3),
    "unary4": _unary_n(4),
    "app2": _unary_n(2),
    "app3": _unary_n(3),
    "app4": _unary_n(4),
    "cleave": _QUOTES[2] + _PARAMS[3] + "[nullary] dip [pop] swap cat nullary [popd] dip",
    "construct": _QUOTES[2] + "swap [swap cat] cons map [i] map [] step",
    # the type conditionals (if_type.h)
    "ifinteger": _if_type("integer"),
    "ifchar": _if_type("char"),
    "iflogical": _if_type("logical"),
    "ifset": _if_type("set"),
    "ifstring": _if_type("string"),
    "iflist": _if_type("list"),
    "iffloat": _if_type("float"),
    "iffile": _if_type("file"),
    # cond, case and opcase (cond.c, case.c, opcase.c): a clause's first
    # member is its test, or the value it matches; the last is the default
    "cond": _QUOTE + "dup dup size 1 - take [first list] all [] [[] [] +] branch "
            "[swap [small] [first popd i] [[first first popd i] [first rest popd i] "
            "[rest swap i] ifte] ifte] y",
    "case": _QUOTE + _PARAMS[2] + "[swap [small] [first popd i] [[first first popd =] "
            "[first rest popd popd i] [rest swap i] ifte] ifte] y",
    "opcase": _QUOTE + _PARAMS[2] + "[swap [small] [first popd] [[first first popd sametype] "
              "[first rest popd] [rest swap i] ifte] ifte] y",
    # the stack as data
    "nullary": "[stack] dip infra first",
    "infra": "[[stack] dip] dip [stack] cat rolldown unit cat [cons unstack] cat [unstack] dip i",
    # the recursion combinators
    "times": _QUOTE + "[dup 0 * pop] dip swap "
             "[swap [0 swap <] [1 - [[dup [i] dip] dip] dip swap i] [pop pop pop] ifte] y",
    "while": _QUOTES[2] + "[[pop swap pop i] [swap pop swap [i] dip i] [pop pop pop] ifte] cons cons y",
    "tailrec": _QUOTES[3] + "[[pop pop swap pop i] [pop swap pop swap pop i] "
               "[swap pop swap pop swap [i] dip i] ifte] cons cons cons y",
    "linrec": _QUOTES[4] + "[[pop pop pop swap pop i] [pop pop swap pop swap pop i] "
              "[[[pop pop] dip] dip [i] swap cat [swap] dip cons cat i] ifte] cons cons cons cons y",
    "binrec": _QUOTES[4] + "[[pop pop pop swap pop i] [pop pop swap pop swap pop i] "
              "[[[pop pop] dip] dip [i] swap cat [swap] dip [dup] dip cons [dip] swap cat "
              "swap [i] cons swap cons cat i] ifte] cons cons cons cons y",
    "genrec": _QUOTES[4] + "[[pop pop pop swap pop i] [pop pop swap pop swap pop i] "
              "[[[pop pop] dip] dip rolldown [i] cons swap cons cat i] ifte] cons cons cons cons y",
    # times and primrec count an integer down, by the kernel's < and -;
    # primrec takes an integer or an aggregate, a type above 5
    "primrec": _QUOTES[2] + "[[dup typeof 5 swap < [] [[] [] +] branch] dip] dip "
               "[[pop] swap cat [dup integer [0 swap < not] [null] branch] swap "
               "[dup integer [dup 1 -] [uncons] branch]] dip linrec",
    "map": _body("map"),
    "filter": _QUOTE + "[dup dup cat pop] dip [[stack] dip] dip [swap] dip [infra first] cons [cons] swap cat cons "
              "[i] cons [dup] swap cat unit [dip] cat [uncons] swap cat [[null] []] dip "
              "[swap [cons] [swap pop] branch] linrec",
    "step": _QUOTE + "[dup dup cat pop] dip [pop null] [pop pop] [[uncons] dip swap [dup [i] dip] dip swap] tailrec",
    "fold": "swapd step",
    # the tree combinators (treestep.c, treerec.c, treegenrec.c): a list is a
    # node, anything else a leaf; C gets a quotation that recurses
    "treestep": _QUOTE + "[[pop pop list] [[i] cons cons step] [pop i] ifte] y",
    "treerec": _QUOTES[2] + "cons [[pop pop list] [over [[i] cons cons] dip rest i] "
               "[pop first i] ifte] y",
    "treegenrec": _QUOTES[3] + "cons cons [[pop pop list] [swap dup rest first rotate "
                  "[[i] dip] dip over [[i] cons cons] dip rest rest i] [pop first i] ifte] y",
    # programs
    "sumto": "[swap [0 =] [pop pop 0] [dup pred swap [swap i] dip +] ifte] y",
    "fact": "[swap [0 =] [pop pop 1] [dup pred swap [swap i] dip *] ifte] y",
}


#: SKIlark's definitions that are not the reference's builtins: Kerby's
#: words and the two programs.  The reference has them as user
#: definitions, so ``typeof`` reads their symbols as user-defined, as it
#: does every definition a program brings
USER_WORDS = {"nip", "tuck", "rot", "sip", "k", "y", "sumto", "fact"}


#: Joy's words with a branch only a string or a set reaches, and the
#: bodies a compiled program set takes: a string literal alone makes a
#: string, and a set literal a set, so without one the branch cannot run
#: and leaves out what it would bring (ord and chr, the list words)
PLAIN = {name: {_body(name, strings, sets) for strings in (False, True) for sets in (False, True)}
         for name in ["map", *_SETS]}


def is_user(name: str, defs: Dict[str, str]) -> bool:
    """Whether a derived word is the program's own: not one of Joy's, or
    one of Joy's names with another body."""
    return name in USER_WORDS or (defs[name] != DEFINITIONS.get(name)
                                  and defs[name] not in PLAIN.get(name, ()))


def _is_string(t) -> bool:
    return isinstance(t, tuple) and t[0] == "T"


def plain(progs: Iterable[Program], defs: Dict[str, str]) -> Dict[str, str]:
    """The definitions a compiled program set takes: Joy's bodies without
    the branches no string or no set of its programs reaches."""
    progs = list(progs)
    strings, sets = _walk(progs, _is_string), _uses_sets(progs)
    return dict(defs, **{k: _body(k, strings, sets) for k in PLAIN
                         if defs.get(k) == DEFINITIONS[k]})


# ------------------------------------------------------------------ parsing

#: the escapes after a backslash in a character or a string, as the
#: reference's scanner reads them (scan.c ``special``); up to three decimal
#: digits are a code
ESCAPES = {"b": 8, "t": 9, "n": 10, "v": 11, "f": 12, "r": 13, '"': 34, "'": 39, "\\": 92}


def _escape(text: str, i: int) -> Tuple[int, int]:
    """The code of the escape after a backslash at ``i``, and its end."""
    if i >= len(text):
        raise ValueError("an escape at the end of the text")
    c = text[i]
    if c in ESCAPES:
        return ESCAPES[c], i + 1
    if c.isdigit():
        j = i + 1
        while j < len(text) and j < i + 3 and text[j].isdigit():
            j += 1
        return int(text[i:j]), j
    return ord(c), i + 1


#: a set's members are the integers 0 to 63 (globals.h SETSIZE)
SETSIZE = 64


def _set_literal(members: Program) -> Tuple[str, Tuple[int, ...]]:
    """A set literal's members, as the reference's reader takes them
    (factor.c ``list2set``): integers or characters, 0 to 63."""
    codes = []
    for t in members:
        if isinstance(t, int):
            code = t
        elif isinstance(t, tuple) and t[0] == "C":
            code = t[1]
        else:
            raise ValueError(f"a set holds integers and characters, not {t!r}")
        if not 0 <= code < SETSIZE:
            raise ValueError(f"a set's member is 0 to {SETSIZE - 1}, not {code}")
        codes.append(code)
    return ("Z", tuple(sorted(set(codes))))


def parse(text: str) -> Program:
    """``"3 [dup +] i"`` -> ``[3, ['dup', '+'], 'i']``; a character
    ``'a`` is ``("C", 97)``, a string ``"ab"`` is ``("T", (97, 98))`` and
    a set ``{2 1}`` is ``("Z", (1, 2))``."""
    stack: List[Program] = [[]]
    opens: List[str] = []
    i = 0
    while i < len(text):
        c = text[i]
        if c.isspace():
            i += 1
        elif c in "[{":
            stack.append([])
            opens.append(c)
            i += 1
        elif c in "]}":
            if not opens or opens[-1] != "[{"["]}".index(c)]:
                raise ValueError(f"unbalanced {c!r}")
            opens.pop()
            q = stack.pop()
            stack[-1].append(q if c == "]" else _set_literal(q))
            i += 1
        elif c == "'":
            if i + 1 >= len(text):
                raise ValueError("a character quote at the end of the text")
            if text[i + 1] == "\\":
                code, i = _escape(text, i + 2)
            else:
                code, i = ord(text[i + 1]), i + 2
            stack[-1].append(("C", code))
        elif c == '"':
            i += 1
            codes = []
            while True:
                if i >= len(text):
                    raise ValueError("an unclosed string")
                if text[i] == '"':
                    break
                if text[i] == "\\":
                    code, i = _escape(text, i + 1)
                else:
                    code, i = ord(text[i]), i + 1
                codes.append(code)
            stack[-1].append(("T", tuple(codes)))
            i += 1
        else:
            j = i
            while j < len(text) and not text[j].isspace() and text[j] not in "[]{}":
                j += 1
            t = text[i:j]
            i = j
            if t.isdigit() or (t[0] == "-" and t[1:].isdigit()):
                stack[-1].append(int(t))
            else:
                stack[-1].append(t)
    if opens:
        raise ValueError(f"unbalanced {opens[-1]!r}")
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
        if isinstance(t, tuple):
            out.append(t)
        elif isinstance(t, list):
            out.append(expand(t, defs, keep, True))
        elif isinstance(t, str) and t in defs and t not in keep:
            body = expand(parse(defs[t]), defs, keep)
            if quoted:
                out.append(Def(t, body, is_user(t, defs)))
            else:
                out.extend(body)
        elif (isinstance(t, str) and t not in KERNEL and t not in COMPILED_ONLY
              and t not in keep):
            raise ValueError(f"unknown word {t!r}")
        else:
            out.append(t)
    return out


def literal_text(t: Tuple[str, object]) -> str:
    """A character, string or set literal back as Joy text, every
    character a decimal escape."""
    if t[0] == "C":
        return f"'\\{t[1]:03d}"
    if t[0] == "Z":
        return "{" + " ".join(map(str, t[1])) + "}"
    return '"' + "".join(f"\\{c:03d}" for c in t[1]) + '"'


def words(prog: Program) -> str:
    """A program back as Joy text."""
    return " ".join(f"[{words(t)}]" if isinstance(t, list) else
                    t.name if isinstance(t, Def) else
                    literal_text(t) if isinstance(t, tuple) else str(t) for t in prog)


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


#: the words that make a character; with a character or a string literal,
#: a compiled program has characters and strings only when it uses one
TEXT_WORDS = {"chr", "ord"}


def _uses_text(progs: Iterable[Program]) -> bool:
    """Whether any program has a character or a string."""
    return _walk(progs, lambda t: (isinstance(t, tuple) and t[0] in "CT") or t in TEXT_WORDS)


def _uses_sets(progs: Iterable[Program]) -> bool:
    """Whether any program has a set: only a set literal makes one."""
    return _walk(progs, lambda t: isinstance(t, tuple) and t[0] == "Z")


def _uses_signs(progs: Iterable[Program]) -> bool:
    """Whether any program can make a negative number: a signed word or a
    negative literal."""
    return _walk(progs, lambda t: t in SIGNED_WORDS or (isinstance(t, int) and t < 0)
                 or (isinstance(t, tuple) and t[0] == "C" and t[1] < 0))


#: SKIjack refuses an expression whose applications nest more than 256
#: deep, and a program nests about a level a word; past ``SPILL`` levels
#: a subexpression becomes an equation of its own, of the equation's
#: parameters (a datum has none, and costs nothing at run time)
SPILL = 240


def _tree(expr: str) -> list:
    """An expression's tokens, a parenthesized group a list."""
    stack: List[list] = [[]]
    for t in re.findall(r"\(|\)|[^\s()]+", expr):
        if t == "(":
            stack.append([])
        elif t == ")":
            q = stack.pop()
            stack[-1].append(q)
        else:
            stack[-1].append(t)
    return stack[0]


def _app_depth(node, d: int = 0) -> int:
    """How deep the applications of ``node`` nest below depth ``d``, as
    SKIjack counts them: ``f a b`` is ``(f a) b``, ``a`` two levels down."""
    if isinstance(node, str):
        return d
    if len(node) == 1:
        return _app_depth(node[0], d)
    k = len(node) - 1
    return max([_app_depth(node[0], d + k)]
               + [_app_depth(a, d + k - i + 1) for i, a in enumerate(node[1:], 1)])


def _text(node) -> str:
    return node if isinstance(node, str) else "(" + " ".join(map(_text, node)) + ")"


def spill(name: str, params: Sequence[str], expr: str) -> List[str]:
    """``name params = expr`` (``name := expr`` without parameters) as
    equations whose applications nest at most ``SPILL`` deep: on the way
    to the deepest, the group ``SPILL // 2`` down is ``name`` and a
    number, applied to the parameters."""
    head = f"{name} {' '.join(params)} =" if params else f"{name} :="
    root = _tree(expr)
    if _app_depth(root) <= SPILL:
        return [f"{head} {expr}"]
    out: List[str] = []
    n = 0
    while _app_depth(root) > SPILL:
        node, d = root, 0
        while True:                        # down the deepest path
            k = len(node) - 1
            places = [(node[0], d + k)] + [(a, d + k - i + 1) for i, a in enumerate(node[1:], 1)]
            j = max(range(len(places)), key=lambda i: _app_depth(*places[i]))
            child, cd = places[j]
            if isinstance(child, list) and cd >= SPILL // 2:
                break
            node, d = child, cd
        n += 1
        aux = f"{name}Spill{n}"
        out.extend(spill(aux, params, " ".join(map(_text, child))))
        node[j] = [aux, *params] if params else aux
    return [f"{head} {' '.join(map(_text, root))}"] + out


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


def codes_text(codes: Sequence[int]) -> str:
    """A string's codes as the kernel's ``text``."""
    out = "TNil"
    for c in reversed(codes):
        out = f"(TCons {integer(c)} {out})"
    return out


def set_text(members: Sequence[int]) -> str:
    """A set's members, ascending, as the kernel's ``set``."""
    out = "SNil"
    for m in sorted(members, reverse=True):
        out = f"(SCons {nat(m)} {out})"
    return out


def datum(prog: Program, basis: bool = False) -> str:
    """A program as a ``prog`` expression; a kept name is a scry.  A
    literal is ``Lit`` of its item.  With ``basis``, for the basis kernel
    (``programs/basis.ascii.ski``): its literals are ``Lit`` of a natural
    and ``Quote`` of a program, and it has ``Ifz``."""
    if not prog:
        return "Done"
    t, rest = prog[0], datum(prog[1:], basis)
    if isinstance(t, Def):
        if basis:                       # the basis kernel has no symbols
            return datum(flatten(t.body) + list(prog[1:]), basis)
        named = "User" if t.user else "Named"
        return f"Then (Def ({named} {name_text(t.name)} ({datum(t.body)}))) ({rest})"
    if isinstance(t, int):
        if basis and t < 0:
            raise ValueError(f"the basis kernel has no negative numbers: {t}")
        return f"Then (Lit {nat(t)}) ({rest})" if basis else f"Then (Lit (Num {integer(t)})) ({rest})"
    if isinstance(t, list):
        if basis:
            return f"Then (Quote ({datum(t, basis)})) ({rest})"
        return f"Then (Lit (Quot ({datum(t)}))) ({rest})"
    if isinstance(t, tuple):
        if basis:
            raise ValueError("the basis kernel has no characters")
        if t[0] == "C":
            return f"Then (Lit (Char {integer(t[1])})) ({rest})"
        if t[0] == "Z":
            return f"Then (Lit (Set {set_text(t[1])})) ({rest})"
        return f"Then (Lit (Str {codes_text(t[1])})) ({rest})"
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
        out.extend(f"{line}\n" for line in spill(f"p{name}", [], datum(prog)))
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
catEmpty eq x r = r |> {{ {QFALSE}QCons y o False; QUnit y False; QThen b (x |> {{ Num n False; Quot l (both (eq l) (eq b)); Logical c False{SYMFALSE}{TXFALSE} }}) }}
emptyQ q = q |> {{ {EMPTIES}QCons x r (catEmpty emptyQ x r); QUnit x False; QThen b (emptyQ b) }}
nullish x = x |> {{ Num n (zero n); Quot q (emptyQ q); Logical b (negate b){SYMFALSE}{TXNULL} }}
cmpI x y = x |> {{ Num m (y |> {{ Num n (cmpZ m n); Quot q More; Logical c (cmpZ m (boolZ c)){SYMMORE}{TXNUM} }}); Quot q More; Logical b (y |> {{ Num n (cmpZ (boolZ b) n); Quot q More; Logical c (cmpZ (boolZ b) (boolZ c)){SYMMORE}{TXLOG} }}){SYMCMP}{TXCMP} }}
compare x y = both (nullish x) (nullish y) |> {{ True Same; False (cmpI x y) }}
isSame o = o |> {{ Less False; Same True; More False }}
isLess o = o |> {{ Less True; Same False; More False }}
truth x = x |> {{ Num n (negate (zero n)); Quot q (negate (emptyQ q)); Logical b b{SYMTRUE}{TXTRUE} }}{TXDEFS}
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
consRun k x r s = x |> {{ Num n (k r (Push x s)); Quot q (k r (Push x s)); Logical b (k r (Push x s)); Sym y (seq (symRun k y) (k r) s){TXPUSH} }}
catView vq x r = r |> {{ {CATQ}QCons y o (VCons x r); QUnit y (VCons x r); QThen b (x |> {{ Num n (VCons x r); Quot l (vq l |> {{ VEmpty (vq b); VCons y m (VCons y (QCons (Quot m) (QThen b))) }}); Logical c (VCons x r); Sym z (VCons x r){TXVIEW} }}) }}
viewQ q = q |> {{ {VIEWS}QCons x r (catView viewQ x r); QUnit x (VCons x {QE}); QThen b (viewQ b) }}
wUncons s = s |> {{ Empty RErr; Push a t (a |> {{ Num n RErr; Quot r (viewQ r |> {{ VEmpty RErr; VCons x p (RVal (Push (Quot p) (Push x t))) }}); Logical c RErr; Sym y RErr{TXUNCONS} }}) }}
wNull s = s |> {{ Empty RErr; Push a t (RVal (Push (Logical (nullish a)) t)) }}
wSmall s = s |> {{ Empty RErr; Push a t (a |> {{ Num n (RVal (Push (Logical (upToOne n)) t)); Quot r (RVal (Push (Logical (viewQ r |> {{ VEmpty True; VCons x p (viewQ p |> {{ VEmpty True; VCons y o False }}) }})) t)); Logical c (RVal (Push (Logical True) t)); Sym y RErr{TXSMALL} }}) }}
-- the stack as a list, top first, and a list as the stack
toQ s = s |> {{ Empty {QE}; Push a t (QCons a (toQ t)) }}
fromQ r = viewQ r |> {{ VEmpty Empty; VCons x p (Push x (fromQ p)) }}
wStack s = RVal (Push (Quot (toQ s)) s)
wUnstack s = s |> {{ Empty RErr; Push a t (a |> {{ Num n RErr; Quot r (RVal (fromQ r)); Logical c RErr; Sym y RErr{TX} }}) }}
"""


#: a compiled program's characters and strings, present only in a program
#: that has one (``_uses_text``): a character is its code, a string its
#: codes; ``cons``, ``cat``, ``+`` and ``-`` take them, so their lines are
#: replaced (``_TEXT_LINES``)
COMPILED_TEXT = """
-- characters and strings: a character is its code, a string its codes
catT y z = y |> {{ TNil z; TCons c r (TCons c (catT r z)) }}
wGlyph c s = RVal (Push (Char c) s)
wText z s = RVal (Push (Str z) s)
wOrd s = s |> {{ Empty RErr; Push a t (a |> {{ Num n (RVal (Push (Num n) t)); Quot q RErr{ORDLOG}{ORDSYM}; Char c (RVal (Push (Num c) t)); Str xs RErr }}) }}
wChr s = s |> {{ Empty RErr; Push a t (a |> {{ Num n (RVal (Push (Char n) t)); Quot q RErr{CHRLOG}{ORDSYM}; Char c (RVal (Push (Char c) t)); Str xs RErr }}) }}
{NUM2C}{SYMTEXT}"""

#: the lines a program with characters replaces: cons onto a string, cat of
#: two strings, + and - of a character and an integer
_TEXT_LINES = {
    "wQcons s = ": "wQcons s = s |> {{ Empty RErr; Push a t (a |> {{ Num n RErr; Quot r (t |> {{ Empty RErr; Push b u (RVal (Push (Quot (QCons b r)) u)) }}){LCNT}; Char xc RErr; Str z (t |> {{ Empty RErr; Push b u (b |> {{ Num n RErr; Quot q RErr{LCNT}; Char c (RVal (Push (Str (TCons c z)) u)); Str xs RErr }}) }}) }}) }}",
    "wCat s = ": "wCat s = s |> {{ Empty RErr; Push a t (a |> {{ Num n RErr; Quot r (t |> {{ Empty RErr; Push b u (b |> {{ Num m RErr; Quot l (RVal (Push (Quot (QCons (Quot l) (QThen r))) u)){LC} }}) }}){LCNT}; Char xc RErr; Str z (t |> {{ Empty RErr; Push b u (b |> {{ Num m RErr; Quot l RErr{LCNT}; Char xc RErr; Str y (RVal (Push (Str (catT y z)) u)) }}) }}) }}) }}",
}
_TEXT_ADD_NATURALS = "wAdd s = s |> {{ Empty RErr; Push a t (t |> {{ Empty RErr; Push b u (a |> {{ Num m (b |> {{ Num n (RVal (Push (Num (add m n)) u)); Quot r RErr{LCNT}; Char c (RVal (Push (Char (add m c)) u)); Str xs RErr }}); Quot r RErr{LC} }}) }}) }}"
_TEXT_NUM2C = """-- + and -: an integer on top, below it an integer or a character, whose
-- kind the result takes
num2c f s = s |> {{ Empty RErr; Push a t (t |> {{ Empty RErr; Push b u (a |> {{ Num m (b |> {{ Num n (RVal (Push (Num (f n m)) u)); Quot r RErr{LCNT}; Char c (RVal (Push (Char (f c m)) u)); Str xs RErr }}); Quot r RErr{LC} }}) }}) }}
subZ n m = plus n (minus m)
"""


#: a compiled program's not, present only in a program that uses it:
#: logical negation of a number, a character or a truth value, and a
#: set's complement
COMPILED_NOT = """
wNot s = s |> {{ Empty RErr; Push a t (a |> {{ Num n (RVal (Push (Logical (zero n)) t)); Quot q RErr; Logical b (RVal (Push (Logical (negate b)) t)){NOTSYM}{NOTTX}{NOTSET} }}) }}
"""

#: a compiled program's sets, present only in a program with a set
#: literal, which alone makes a set: as the interpreted kernel's, members
#: ascending, and the lines below in place of the kernel's
COMPILED_SETS = """
-- sets: members ascending, 0 to 63; the union and subset order merge the
-- members, the complement counts k to 63, c numbers left
ltN m n = n |> {{ Zero False; Suc j (m |> {{ Zero True; Suc i (ltN i j) }}) }}
eqN m n = m |> {{ Zero (n |> {{ Zero True; Suc j False }}); Suc i (n |> {{ Zero False; Suc j (eqN i j) }}) }}
insS x s = s |> {{ SNil (SCons x SNil); SCons y t (cmpN x y |> {{ Less (SCons x (SCons y t)); Same (SCons y t); More (SCons y (insS x t)) }}) }}
unionS s t = s |> {{ SNil t; SCons x r (t |> {{ SNil (SCons x r); SCons y u (cmpN x y |> {{ Less (SCons x (unionS r (SCons y u))); Same (SCons x (unionS r u)); More (SCons y (unionS (SCons x r) u)) }}) }}) }}
subS s t = s |> {{ SNil True; SCons x r (t |> {{ SNil False; SCons y u (cmpN x y |> {{ Less False; Same (subS r u); More (subS (SCons x r) u) }}) }}) }}
eqS s t = s |> {{ SNil (t |> {{ SNil True; SCons y u False }}); SCons x r (t |> {{ SNil False; SCons y u (eqN x y |> {{ True (eqS r u); False False }}) }}) }}
odd m = m |> {{ Zero False; Suc j (negate (odd j)) }}
half m = m |> {{ Zero Zero; Suc j (j |> {{ Zero Zero; Suc i (Suc (half i)) }}) }}
bitsN k m = m |> {{ Zero SNil; Suc j (odd m |> {{ True (SCons k (bitsN (Suc k) (half m))); False (bitsN (Suc k) (half m)) }}) }}
complS k c s = c |> {{ Zero SNil; Suc d (s |> {{ SNil (SCons k (complS (Suc k) d SNil)); SCons x t (eqN k x |> {{ True (complS (Suc k) d t); False (SCons k (complS (Suc k) d (SCons x t))) }}) }}) }}
eight := Suc (Suc (Suc five))
n64 := mul eight eight
compl s = complS Zero n64 s
{BITSI}
boolS b = b |> {{ False SNil; True (SCons Zero SNil) }}
isSet x = x |> {{ Num n False; Quot q False; Logical b False; Sym y False{ISTX}; Set z True }}
bitsOf x = x |> {{ Num n (bitsI n); Quot q SNil; Logical b (boolS b); Sym y SNil{BITSTX}; Set z z }}
-- a set and a number are the same when the number's 64 bits, two's
-- complement, are the set's members; < is the proper subset of the bits
-- when either is a set (comprel.h SETCMP)
setC x y = eqS (bitsOf x) (bitsOf y) |> {{ True Same; False More }}
lessI x y = (isSet x |> {{ True True; False (isSet y) }}) |> {{ True (both (negate (eqS (bitsOf x) (bitsOf y))) (subS (bitsOf x) (bitsOf y))); False (isLess (compare x y)) }}
{SETCONS}
wSet z s = RVal (Push (Set z) s)
"""

COMPILED_TYPES = """
-- Joy's typeof (globals.h): a user-defined symbol 2, any other 3, a truth
-- value 4, a character 5, an integer 6, a string 8, a list 9
kindOf a = a |> {{ Num n {K6}; Quot q {K9}{KLOG}{KSYM}{KTX} }}
wTypeof s = s |> {{ Empty RErr; Push a t (RVal (Push (Num (kindOf a)) t)) }}
{SYMKIND}"""


def _uses_types(progs: Iterable[Program]) -> bool:
    """Whether any program asks a value's type."""
    return _walk(progs, lambda t: t == "typeof")


class _Lists:
    """What a list-reading program's compiled kernel needs from its
    compiler: the symbols in the order of their names, their runs, and
    each static quotation's view."""

    def __init__(self, syms: List[str], views: List[str], qe: str,
                 sym_run: List[str], names: Sequence[str] = ()) -> None:
        self.syms, self.views, self.qe, self.sym_run = syms, views, qe, sym_run
        self.names = list(names)                # each symbol's Joy name


#: a derived word's symbol: ``Z`` and its name, an operator's characters
#: spelled out
_MANGLE = {"!": "Bang", "+": "Plus", "-": "Minus", "*": "Star", "/": "Slash",
           "<": "Lt", "=": "Eq", ">": "Gt"}


def def_symbol(name: str, user: bool = False) -> str:
    """A derived word's symbol constructor: ``size`` is ``Zsize``, ``!=``
    is ``ZBangEq``, and a user definition's is ``U`` and its name."""
    return ("U" if user else "Z") + "".join(_MANGLE.get(c, c) for c in name)


def symbol_name(ctor: str) -> str:
    """A compiled symbol's Joy name: ``YDup`` is ``dup``, ``Zsize`` is
    ``size``, ``ZBangEq`` is ``!=``, ``Usq`` is ``sq``."""
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
                     empties: Sequence[bool] = (), text: bool = False,
                     types: bool = False, sets: bool = False, nots: bool = False) -> str:
    """The compiled kernel for ``n`` static quotations (``empties`` says
    which are empty), with truth values when ``truth``, integers when
    ``signs`` (else naturals), the list words when ``lists``, characters
    and strings when ``text``, ``typeof`` when ``types``, sets when
    ``sets`` (which come with lists) and ``not`` when ``nots``."""
    tx = "; Char xc RErr; Str xs RErr" if text else ""
    st = "; Set st RErr" if sets else ""
    lcnt = ("; Logical lg RErr" if truth else "") + ("; Sym sy RErr" if lists else "") + st
    ls = ("; Sym sy RErr" if lists else "") + tx + st
    lc = lcnt + tx
    lit = (lambda k: integer(k)) if signs else nat
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
            QE=lists.qe,
            TXPUSH="; Char c (k r (Push x s)); Str z (k r (Push x s))" if text else "",
            TXVIEW="; Char c (VCons x r); Str w (VCons x r)" if text else "",
            TXUNCONS=("; Char xc RErr; Str z (z |> { TNil RErr; TCons c r "
                      "(RVal (Push (Str r) (Push (Char c) t))) })") if text else "",
            TXSMALL=("; Char c (RVal (Push (Logical (upToOne c)) t)); Str z (RVal (Push "
                     "(Logical (z |> { TNil True; TCons c r (r |> { TNil True; TCons d o False }) })) t))")
            if text else "",
            TX=tx + st)
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
                    "Sym w (cmpN (symNo z) (symNo w))"
                    + ("; Char c More; Str w (cmpT (symText z) w)" if text else "")
                    + " })") if lists else "",
            TXFALSE="; Char c False; Str z False" if text else "",
            TXNULL="; Char c (zero c); Str z (z |> { TNil True; TCons c r False })" if text else "",
            TXTRUE="; Char c (negate (zero c)); Str z (z |> { TNil False; TCons c r True })" if text else "",
            TXNUM="; Char c (cmpZ m c); Str z More" if text else "",
            TXLOG="; Char c (cmpZ (boolZ b) c); Str z More" if text else "",
            TXCMP=("; Char c (y |> { Num n (cmpZ c n); Quot q More; Logical d (cmpZ c (boolZ d))"
                   + ("; Sym w More" if lists else "") + "; Char d (cmpZ c d); Str z More })"
                   "; Str z (y |> { Num n More; Quot q More; Logical c More"
                   + ("; Sym w (cmpT z (symText w))" if lists else "")
                   + "; Char c More; Str w (cmpT z w) })") if text else "",
            TXDEFS=("\n-- strings compare as strcmp does, code by code\n"
                    "cmpT s t = s |> { TNil (t |> { TNil Same; TCons d u Less }); TCons c r "
                    "(t |> { TNil More; TCons d u (cmpZ c d |> { Less Less; Same (cmpT r u); "
                    "More More }) }) }") if text else "")
    text_block = ""
    if text:
        symtext = ""
        if lists and truth:
            symtext = "-- a symbol's name, its codes, to compare with a string\nsymText y = y |> { " + "; ".join(
                f"{y} {_codes(lit, nm)}" for y, nm in zip(lists.syms or ["YNone"], lists.names or [""])) + " }\n"
        text_block = COMPILED_TEXT.format(
            ORDLOG="; Logical b (RVal (Push (Num (boolZ b)) t))" if truth else "",
            CHRLOG="; Logical b (RVal (Push (Char (boolZ b)) t))" if truth else "",
            ORDSYM="; Sym y RErr" if lists else "",
            NUM2C=_TEXT_NUM2C.format(LC=lc, LCNT=lcnt) if signs else "",
            SYMTEXT=symtext)
        symtype = symtype + f"text   === TNil | TCons {'int' if signs else 'nat'} text\n"
    types_block = ""
    if types:
        symkind = ""
        if lists:
            symkind = "symKind y = y |> { " + "; ".join(
                f"{y} {lit(2 if y.startswith('U') else 3)}" for y in (lists.syms or ["YNone"])) + " }\n"
        types_block = COMPILED_TYPES.format(
            K6=lit(6), K9=lit(9),
            KLOG=f"; Logical b {lit(4)}" if truth else "",
            KSYM="; Sym y (symKind y)" if lists else "",
            KTX=f"; Char c {lit(5)}; Str z {lit(8)}" if text else "",
            SYMKIND=symkind)
    not_block = ""
    if nots:
        not_block = COMPILED_NOT.format(
            NOTSYM="; Sym y RErr" if lists else "",
            NOTTX="; Char c (RVal (Push (Logical (zero c)) t)); Str z RErr" if text else "",
            NOTSET="; Set z (RVal (Push (Set (compl z)) t))" if sets else "")
    sets_block = ""
    if sets:
        symtype = symtype + "set    === SNil | SCons nat set\n"
        sets_block = COMPILED_SETS.format(
            BITSI=("bitsI z = z |> { Pos m (bitsN Zero m); Neg m (compl (bitsN Zero m)) }"
                   if signs else "bitsI m = bitsN Zero m"),
            ISTX="; Char c False; Str z False" if text else "",
            BITSTX="; Char c (bitsI c); Str z SNil" if text else "",
            SETCONS=("setCons n z u = n |> { Pos m (ltN m n64 |> { True (RVal (Push (Set (insS m z)) u)); "
                     "False RErr }); Neg m RErr }" if signs else
                     "setCons n z u = ltN n n64 |> { True (RVal (Push (Set (insS n z)) u)); False RErr }"))
    out = COMPILED_KERNEL.format(
        QUOTS="".join(f"Q{k} | " for k in range(1, n + 1)),
        CASES_F="".join(f"Q{i} (b{i} k s); " for i in range(1, n + 1)),
        CASES_U="".join(f"Q{k} (b{k} applyU s); " for k in range(1, n + 1)),
        LITEM=(" | Logical logical" if truth else "") + (" | Sym sym" if lists else "")
        + (f" | Char {'int' if signs else 'nat'} | Str text" if text else "")
        + (" | Set set" if sets else ""),
        LC=lc, SYMTYPE=symtype,
        CONS_F=cons_f, UNIT_F=unit_f, CONS_U=cons_u, UNIT_U=unit_u,
        INTTYPE="int    === Pos nat | Neg nat\n" if signs else "",
        NUM="int" if signs else "nat",
        NUMBERS=numbers.format(LC=lc),
        TRUTH=truth_block,
        LISTS=block + text_block + types_block + not_block + sets_block)
    if text:
        lines = dict(_TEXT_LINES)
        if signs:
            lines["wAdd s = "] = "wAdd s = num2c plus s"
            lines["wSub s = "] = "wSub s = num2c subZ s"
        else:
            lines["wAdd s = "] = _TEXT_ADD_NATURALS
        out = "\n".join(_text_line(line, lines, lc, lcnt) for line in out.split("\n"))
    if sets:
        out = "\n".join(_set_line(line, text, signs) for line in out.split("\n"))
    return out


#: the compiled kernel's lines a program with sets extends: a set's
#: branch, put in before the line's closing braces
_SET_BRANCHES = {
    "nullish x = ": ("; Set z (z |> { SNil True; SCons m r False })", " }"),
    "truth x = ": ("; Set z (z |> { SNil False; SCons m r True })", " }"),
    "catEmpty eq x r = ": ("; Set z False", " }) }"),
    "consRun k x r s = ": ("; Set z (k r (Push x s))", " }"),
    "catView vq x r = ": ("; Set z (VCons x r)", " }) }"),
    "wSmall s = ": ("; Set z (RVal (Push (Logical (z |> { SNil True; SCons m r "
                    "(r |> { SNil True; SCons k o False }) })) t))", " }) }"),
    "wOrd s = ": ("; Set st RErr", " }) }"),
    "wChr s = ": ("; Set st RErr", " }) }"),
    "kindOf a = ": ("; Set z {K7}", " }"),
}


def _cmp_line(text: bool) -> str:
    """The comparison of two items, sets among them (compare.h): as the
    kernel's without sets, and a set the same as a number or a set whose
    bits are its members."""
    kinds = ["Num", "Quot", "Logical", "Sym"] + (["Char", "Str"] if text else []) + ["Set"]
    xv = {"Num": "xm", "Quot": "xq", "Logical": "xb", "Sym": "xz", "Char": "xc", "Str": "xs", "Set": "xe"}
    yv = {"Num": "yn", "Quot": "yq", "Logical": "yb", "Sym": "yw", "Char": "yc", "Str": "ys", "Set": "ye"}
    num = {"Num": lambda v: v, "Logical": lambda v: f"(boolZ {v})", "Char": lambda v: v}

    def cmp(a: str, b: str) -> str:
        x, y = xv[a], yv[b]
        if "Set" in (a, b) and {a, b} <= {"Num", "Logical", "Char", "Set"}:
            return "(setC x y)"
        if a in num and b in num:
            return f"(cmpZ {num[a](x)} {num[b](y)})"
        if a == b == "Sym":
            return f"(cmpN (symNo {x}) (symNo {y}))"
        if (a, b) == ("Sym", "Str"):
            return f"(cmpT (symText {x}) {y})"
        if (a, b) == ("Str", "Sym"):
            return f"(cmpT {x} (symText {y}))"
        if a == b == "Str":
            return f"(cmpT {x} {y})"
        return "More"

    def case(a: str) -> str:
        if a == "Quot":
            return "Quot xq More"
        ys = "; ".join(f"{b} {yv[b]} {cmp(a, b)}" for b in kinds)
        return f"{a} {xv[a]} (y |> {{ {ys} }})"
    return "cmpI x y = x |> { " + "; ".join(case(a) for a in kinds) + " }"


def _set_line(line: str, text: bool, signs: bool) -> str:
    """A compiled kernel line, or its form in a program with sets."""
    tx = "; Char xc RErr; Str xs RErr" if text else ""
    m = "(Pos m)" if signs else "m"
    if line.startswith("wQcons s = "):
        onto_str = ("; Char xc RErr; Str z (t |> { Empty RErr; Push b u (b |> { Num n RErr; Quot q RErr; "
                    "Logical lg RErr; Sym sy RErr; Char c (RVal (Push (Str (TCons c z)) u)); Str xs RErr; "
                    "Set st RErr }) })") if text else ""
        return ("wQcons s = s |> { Empty RErr; Push a t (a |> { Num n RErr; Quot r (t |> { Empty RErr; "
                "Push b u (RVal (Push (Quot (QCons b r)) u)) }); Logical lg RErr; Sym sy RErr" + onto_str
                + "; Set z (t |> { Empty RErr; Push b u (b |> { Num n (setCons n z u); Quot q RErr; "
                "Logical lg RErr; Sym sy RErr" + ("; Char c (setCons c z u); Str xs RErr" if text else "")
                + "; Set st RErr }) }) }) }")
    if line.startswith("wCat s = "):
        strings = ("; Char xc RErr; Str z (t |> { Empty RErr; Push b u (b |> { Num m RErr; Quot l RErr; "
                   "Logical lg RErr; Sym sy RErr; Char xc RErr; Str y (RVal (Push (Str (catT y z)) u)); "
                   "Set st RErr }) })") if text else ""
        return ("wCat s = s |> { Empty RErr; Push a t (a |> { Num n RErr; Quot r (t |> { Empty RErr; "
                "Push b u (b |> { Num m RErr; Quot l (RVal (Push (Quot (QCons (Quot l) (QThen r))) u)); "
                "Logical lg RErr; Sym sy RErr" + tx + "; Set st RErr }) }); Logical lg RErr; Sym sy RErr"
                + strings + "; Set z (t |> { Empty RErr; Push b u (b |> { Num m RErr; Quot l RErr; "
                "Logical lg RErr; Sym sy RErr" + tx + "; Set y (RVal (Push (Set (unionS y z)) u)) }) }) }) }")
    if line.startswith("cmpI x y = "):
        return _cmp_line(text)
    if line.startswith("wLt s = "):
        assert line.count("(isLess (compare b a))") == 1
        return line.replace("(isLess (compare b a))", "(lessI b a)")
    if line.startswith("wUncons s = "):
        return _set_branch(line, f"; Set z (z |> {{ SNil RErr; SCons m r (RVal (Push (Set r) (Push (Num {m}) t))) }})",
                           " }) }")
    for prefix, (branch, end) in _SET_BRANCHES.items():
        if line.startswith(prefix):
            return _set_branch(line, branch.replace("{K7}", integer(7) if signs else nat(7)), end)
    return line


def _set_branch(line: str, branch: str, end: str) -> str:
    """A line's case with a set's branch put in before ``end``."""
    if not line.endswith(end):
        raise AssertionError(f"a set line does not end as expected: {line[:60]!r}")
    return line[:-len(end)] + branch + end


def _text_line(line: str, lines: Dict[str, str], lc: str, lcnt: str) -> str:
    """A kernel line, or its replacement in a program with characters."""
    for prefix, new in lines.items():
        if line.startswith(prefix):
            return new.format(LC=lc, LCNT=lcnt)
    return line


def _codes(lit, name: str) -> str:
    """A name's characters' codes as a ``text`` of the program's numbers."""
    out = "TNil"
    for c in reversed(name):
        out = f"(TCons {lit(ord(c))} {out})"
    return out


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

    def text(self, codes: Sequence[int]) -> str:
        """A string's codes as a ``text`` of the program's numbers."""
        out = "TNil"
        for c in reversed(codes):
            out = f"(TCons {self.literal(c)} {out})"
        return out

    def item(self, t: Token) -> str:
        """A static quotation's element as an item: a literal its value, a
        word a symbol."""
        if isinstance(t, int):
            return f"(Num {self.literal(t)})"
        if isinstance(t, list):
            return f"(Quot {self.quot(t)})"
        if t in ("true", "false"):
            return f"(Logical {t.capitalize()})"
        if isinstance(t, tuple):
            if t[0] == "Z":
                return f"(Set {set_text(t[1])})"
            return f"(Char {self.literal(t[1])})" if t[0] == "C" else f"(Str {self.text(t[1])})"
        if isinstance(t, Def):
            ctor = def_symbol(t.name, t.user)
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
        return _Lists(order, views, qe, [self.syms[k][1] for k in order],
                      [self.syms[k][0] for k in order])

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
        if isinstance(t, tuple):
            if t[0] == "Z":
                return f"(wSet {set_text(t[1])})"
            return f"(wGlyph {self.literal(t[1])})" if t[0] == "C" else f"(wText {self.text(t[1])})"
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
    integers, whether it reads lists, whether it uses truth values (a
    program reading lists does), characters, ``typeof``, sets (which bring
    the list words) and ``not``.  Without lists nothing reads a derived
    word as a symbol, so its programs are flattened: they compile as they
    did before ``Def``."""
    signs, sets = _uses_signs(progs), _uses_sets(progs)
    lists = sets or _uses_lists(progs)
    return (signs, lists, lists or _uses_truth(progs), _uses_text(progs), _uses_types(progs),
            sets, _walk(progs, lambda t: t == "not"))


def compiled(programs: Dict[str, str], defs: Dict[str, str] = DEFINITIONS
             ) -> str:
    """For each program ``p``: ``cP`` (its body, taking the eliminator),
    ``rP`` (under ``apply fuel``, ``fuel`` a Church numeral) and ``uP``
    (under ``applyU``)."""
    progs = _programs(programs, defs)
    progs = _programs(programs, plain(progs.values(), defs))
    signs, lists, truth, text, types, sets, nots = _compile_set(list(progs.values()))
    if not lists:
        progs = {name: flatten(prog) for name, prog in progs.items()}
    c = _Compiler(signs, lists)
    tops = {name: c.body(prog) for name, prog in progs.items()}
    if lists:
        c.quot([])
    bodies = c.hoist()
    info = c.list_info()
    kernel = _compiled_kernel(len(c.quots), truth, signs, info, c.empties(), text, types, sets, nots)
    out = [kernel, "\n-- static quotations, hoisted\n"]
    for b in bodies:
        name, body = b.split(" ap = ", 1)
        out.extend(f"{line}\n" for line in spill(name, ["ap"], body))
    out.append("\n-- programs, from skilark.joy.compiled\n")
    for name, body in tops.items():
        out.extend(f"{line}\n" for line in spill(f"c{name}", ["ap"], body))
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


def level1_reader(truth: bool, signs: bool, lists: bool = False, text: bool = False,
                  sets: bool = False) -> str:
    """The level-1 reader for a kernel whose items include truth values
    when ``truth`` (a truth value on top answers ``S S K``), whose numbers
    are integers when ``signs`` (a negative is not the natural asked for),
    whose items include symbols when ``lists`` (``S S I``), characters
    and strings when ``text`` (``S K S`` and ``S S S``), and sets when
    ``sets`` (``S I K``)."""
    test = "(n |> {{ Pos m (eqNat m v); Neg m (K I) }})" if signs else "(eqNat n v)"
    lc = (("; Logical b (S S K)" if truth else "") + ("; Sym y (S S I)" if lists else "")
          + ("; Char c (S K S); Str z (S S S)" if text else "") + ("; Set z (S I K)" if sets else ""))
    return _LEVEL1_READER.format(LC=lc, TEST=test.format())


#: the reader for the interpreted kernel: truth values, integers, symbols,
#: characters, strings and sets
LEVEL1_READER = level1_reader(True, True, True, True, True)


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
        truth = signs = lists = text = sets = True
        facts = {n: datum(expand(parse(defs[n]), defs)) for n in keep}
        runs = {name: f"execU ({datum(prog)}) Empty" for name, prog in progs.items()}
        hoisted: List[str] = []
    elif form == "compiled":
        facts_progs = {n: expand(parse(defs[n]), defs) for n in keep}
        defs = plain(list(_programs(programs, defs, keep).values()) + list(facts_progs.values()), defs)
        progs = _programs(programs, defs, keep)
        facts_progs = {n: expand(parse(defs[n]), defs) for n in keep}
        signs, lists, truth, text, types, sets, nots = _compile_set(
            list(progs.values()) + list(facts_progs.values()))
        if not lists:
            progs = {name: flatten(prog) for name, prog in progs.items()}
            facts_progs = {n: flatten(prog) for n, prog in facts_progs.items()}
        c = _Compiler(signs, lists)
        facts = {n: c.body(prog, "applyU") for n, prog in facts_progs.items()}
        runs = {name: f"{c.body(prog, 'applyU', keep)} Empty" for name, prog in progs.items()}
        if lists:
            c.quot([])
        hoisted = c.hoist()
        kernel = _compiled_kernel(len(c.quots), truth, signs, c.list_info(), c.empties(), text, types,
                                  sets, nots)
    else:
        raise ValueError(f"unknown form {form!r}")
    out = [kernel, "\n".join(hoisted) + ("\n" if hoisted else ""),
           LEVEL1_KERNEL.format(SEGS=" | ".join(segment(n) for n in keep)),
           level1_reader(truth, signs, lists, text, sets),
           "\ndict := ns{" + ", ".join(f"/{n} => <{v}>" for n, v in facts.items()) + "}\n",
           f"\n-- programs, from skilark.joy.level1 ({form} form)\n"]
    for name, run in runs.items():
        out.append(f"r{name} := wfN dict |- <topIs {nat(value)} ({run})>@{fuel}\n")
        out.append(f"n{name} := wfN dict |- <topIs {nat(value + 1)} ({run})>@{fuel}\n")
    return "".join(out)
