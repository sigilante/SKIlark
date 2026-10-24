"""SKIjack's compile, with aviary's bracket abstraction in linear time.

aviary_kernel's ``bracket_abstract`` asks ``free_vars`` of a body at
every level it descends, and ``free_vars`` walks the body whole, so
abstracting a term costs its size times its depth: a compiled SKIlark
program spends 98% of its compile there.  ``compile`` swaps in a
``free_vars`` that answers each node once, keyed by the node itself, for
the length of one compile.  The abstraction is aviary's, unchanged, and
gives the same terms (``tests/test_modes.py`` checks them hash for hash).
"""

from __future__ import annotations

from typing import Dict, FrozenSet, Tuple

import aviary_kernel.abstraction as _abstraction
import skijack
from aviary_kernel.terms import App, Atom

#: id of a node -> (the node, its names); the node is held, so its id is
#: not reused while the entry lives
_Memo = Dict[int, Tuple[object, FrozenSet[str]]]


def _free_vars(memo: _Memo):
    def free_vars(term) -> FrozenSet[str]:
        """The atom names in ``term``, each node's found once."""
        hit = memo.get(id(term))
        if hit is not None and hit[0] is term:
            return hit[1]
        stack, order = [term], []
        while stack:
            t = stack.pop()
            h = memo.get(id(t))
            if h is not None and h[0] is t:
                continue
            order.append(t)
            if isinstance(t, App):
                stack.append(t.fn)
                stack.append(t.arg)
        for t in reversed(order):
            h = memo.get(id(t))
            if h is not None and h[0] is t:
                continue
            names = (frozenset((t.name,)) if isinstance(t, Atom)
                     else memo[id(t.fn)][1] | memo[id(t.arg)][1])
            memo[id(t)] = (t, names)
        return memo[id(term)][1]
    return free_vars


def compile(source: str, **kw):
    """``skijack.compile``, its abstraction's free names found once a
    node; aviary's own ``free_vars`` is back when it returns."""
    original = _abstraction.free_vars
    _abstraction.free_vars = _free_vars({})
    try:
        return skijack.compile(source, **kw)
    finally:
        _abstraction.free_vars = original
