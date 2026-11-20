import pytest

from raq.config import load, world_config
from raq.world.app import AppWorld


@pytest.fixture(scope="session")
def cfg() -> dict:
    c = world_config()
    c["weeks"] = 4
    return c


@pytest.fixture(scope="session")
def world(cfg) -> AppWorld:
    return AppWorld(cfg, 4101)


@pytest.fixture(scope="session")
def platform() -> dict:
    return load("platform")


@pytest.fixture(scope="session")
def value() -> dict:
    return load("value")
