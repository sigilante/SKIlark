"""``--runslow`` runs the level-1 measurements, which take minutes on the
reference reducer; by default they are skipped and their numbers are
pinned from a run recorded in PLAN.md."""

import pytest


def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true", default=False,
                     help="run the slow level-1 measurements")


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: takes minutes on the reference reducer")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        return
    skip = pytest.mark.skip(reason="slow; pass --runslow")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip)
