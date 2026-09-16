import pytest

from python_sim import Simulation


@pytest.fixture
def sim():
    return Simulation(seed=42)
