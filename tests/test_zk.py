"""skilark.zk: over literal bits, ``vsplitB`` accepts exactly the bits of
two numbers adding up to ``x`` (every bit pattern at k = 2 and 3, samples
at k = 8).  Over a hidden term, ``vsplit`` can be fooled: a term that is
no stack passes (pinned below), which is why lean-ski proves ``vsplitB``,
as a predicate over literal bits."""

import itertools
import random

import pytest

from skilark import zk


@pytest.fixture(scope="module")
def t2():
    return zk.Terms(2)


def test_true_is_K(t2):
    assert repr(t2.t["T"]) == "Atom('K')"


def test_exhaustive_k2(t2):
    for a, b, x in itertools.product(range(4), repeat=3):
        assert t2.verify(t2.x(x), t2.w(a, b))[0] == (a + b == x), (a, b, x)


def test_non_bits_rejected(t2):
    # a digit 2 stands for a carry the range does not allow
    assert not t2.verify(t2.x(2), t2.w(0, 0, [2, 0], [0, 0]))[0]
    assert not t2.verify(t2.x(2), t2.w(0, 0, [0, 1], [0, 2]))[0]


def test_short_witness_rejected(t2):
    assert not t2.verify(t2.x(0), t2.stack([t2.num(0)]))[0]
    assert not t2.verify(t2.x(0), t2.stack([]))[0]


def test_quotation_in_witness_rejected(t2):
    q = t2.quot([t2.num(0)])
    assert not t2.verify(t2.x(0), t2.stack([q, t2.num(0), t2.num(0), t2.num(0)]))[0]


def test_random_k8():
    t = zk.Terms(8)
    rng = random.Random(8)
    for _ in range(4):
        a, b = rng.randrange(256), rng.randrange(256)
        x = a + b if a + b < 256 else rng.randrange(256)
        assert t.verify(t.x(x), t.w(a, b))[0] == (a + b == x), (a, b, x)
    assert not t.verify(t.x(200), t.w(123, 78))[0]
    assert t.verify(t.x(200), t.w(123, 77))[0]


@pytest.mark.parametrize("k", [2, 8])
def test_forged_term_passes(k):
    """The known limit: a term that answers the first match with a
    ready-made result, ``K (K (RVal R))`` with ``R`` a stack of ``2k - 1``
    zeros, is no stack and passes at x = 0 and x = 1.  A hidden term is
    not data; literal bits the circuit constrains are."""
    from aviary_kernel.terms import App, Atom
    t = zk.Terms(k)
    r = t.app("RVal", t.stack([t.num(0)] * (2 * k - 1)))
    forged = App(Atom("K"), App(Atom("K"), r))
    for x in (0, 1):
        assert t.verify(t.x(x), forged)[0], (k, x)


# ---------------------------------------------------------------- literal bits

@pytest.mark.parametrize("k", [2, 3])
def test_bits_exhaustive(k):
    t = zk.Terms(k)
    for a, b, x in itertools.product(range(2 ** k), repeat=3):
        assert t.verify_bits(t.x(x), t.bits(a, b))[0] == (a + b == x), (k, a, b, x)


def test_bits_k8():
    t = zk.Terms(8)
    rng = random.Random(88)
    for _ in range(4):
        a, b = rng.randrange(256), rng.randrange(256)
        x = a + b if a + b < 256 else rng.randrange(256)
        assert t.verify_bits(t.x(x), t.bits(a, b))[0] == (a + b == x), (a, b, x)
    assert t.verify_bits(t.x(200), t.bits(123, 77))[0]
    assert not t.verify_bits(t.x(200), t.bits(123, 78))[0]
    assert not t.verify_bits(t.x(200), t.bits(0, 0))[0]


def test_decoder_shape():
    assert zk.decoder(1) == "decBits qr0 = Push (bitNum qr0) Empty\n"
    assert zk.decoder(2) == ("decBits qr0 = qr0 (\\qb0. \\qr1. Push (bitNum qb0) "
                             "(Push (bitNum qr1) Empty))\n")

