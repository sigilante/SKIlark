"""``--runslow`` runs the level-1 measurements, which take minutes on the
reference reducer; by default they are skipped and their numbers are
pinned from a run recorded in PLAN.md.

``SKILARK_SHARD=k/n`` keeps every n-th test from the k-th on, in the order
collected, so n jobs run the suite between them, each module spread over
all n (CI's reference job)."""

import os

import pytest


def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true", default=False,
                     help="run the slow level-1 measurements")


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: takes minutes on the reference reducer")


def pytest_collection_modifyitems(config, items):
    shard = os.environ.get("SKILARK_SHARD")
    if shard:
        k, n = (int(x) for x in shard.split("/"))
        if not 1 <= k <= n:
            raise pytest.UsageError(f"SKILARK_SHARD={shard}: k must be 1 to n")
        kept = [item for i, item in enumerate(items) if i % n == k - 1]
        config.hook.pytest_deselected(items=[item for item in items if item not in kept])
        items[:] = kept
    if config.getoption("--runslow"):
        return
    skip = pytest.mark.skip(reason="slow; pass --runslow")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip)
