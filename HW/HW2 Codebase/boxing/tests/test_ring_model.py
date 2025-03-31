from dataclasses import asdict

import pytest
import unittest
from unittest.mock import patch
from pytest_mock import MockerFixture

from boxing.models.ring_model import RingModel
from boxing.models.boxers_model import Boxer

@pytest.fixture()
def ring_model():
    """Fixture to provide a new instance of RingModel for each test."""
    return RingModel()

"""Fixtures providing sample songs for the tests."""
@pytest.fixture
def sample_boxer1():
    return Boxer(1, "Muhammad Ali", 236, 191, 198, 38)

@pytest.fixture
def sample_boxer2():
    return Boxer(2, "Mike Tyson", 220, 178, 180, 22)

@pytest.fixture
def sample_ring(sample_boxer1, sample_boxer2):
    return [sample_boxer1, sample_boxer2]

@pytest.fixture
def mock_update_boxer_stats(mocker):
    """Mock the update_boxer_stats function for testing purposes."""
    return mocker.patch("boxing.models.boxers_model.update_boxer_stats")

##################################################
# Add / Remove Boxer Management Test Cases
##################################################

def test_add_boxer_to_ring(ring_model, sample_boxer1):
    """Test adding a boxer to the ring.

    """
    ring_model.enter_ring(sample_boxer1)
    assert len(ring_model.ring) == 1
    assert ring_model.ring[0].name == 'Muhammad Ali'


def test_add_bad_boxer_to_ring(ring_model, sample_boxer1):
    """Test error when a bad boxer enters the ring.

    """
    with pytest.raises(TypeError, match=f"Invalid type: Expected 'Boxer', got '{type(asdict(sample_boxer1)).__name__}'"):
        ring_model.enter_ring(asdict(sample_boxer1))


def test_full_ring(ring_model, sample_boxer1, sample_boxer2):
    """Test error when a the ring is full and we try to add another boxer.

    """
    ring_model.enter_ring(sample_boxer1)
    ring_model.enter_ring(sample_boxer2)
    assert len(ring_model.ring) == 2
    with pytest.raises(ValueError, match="Ring is full, cannot add more boxers."):
        ring_model.enter_ring(sample_boxer1)


def test_clear_ring(ring_model, sample_boxer1):
    """Test clearing the entire ring.

    """
    ring_model.enter_ring(sample_boxer1)

    ring_model.clear_ring()
    assert len(ring_model.ring) == 0, "Ring should be empty after clearing"

##################################################
# Boxer Retrieval Test Cases
##################################################

def test_get_boxers(ring_model, sample_ring):
    """Test successfully retrieving all boxers from the ring.

    """
    ring_model.ring.extend(sample_ring)

    all_boxers = ring_model.get_boxers()

    assert len(all_boxers) == 2
    assert all_boxers[0].name == 'Muhammad Ali'
    assert all_boxers[1].name == 'Mike Tyson'


def test_get_fighting_skill(ring_model, sample_boxer1):
    """Test successfully retrieving a boxer's fighting skill.
    
    """
    fighting_skill = ring_model.get_fighting_skill(sample_boxer1)

    assert fighting_skill == 2849.8

##################################################
# Fight Test Cases
##################################################

def test_fight_successful(ring_model, sample_ring, sample_boxer1, sample_boxer2, mock_update_boxer_stats):
    """Test starting a fight in the ring successfully.

    """
    ring_model.ring.extend(sample_ring)

    winner = ring_model.fight()

    if winner.id == sample_boxer1.id:
        loser = sample_boxer2
    else:
        loser = sample_boxer1

    calls = [unittest.call.update_boxer_stats(winner.id, 'win'), unittest.call.update_boxer_stats(loser.id, 'loss')]
    mock_update_boxer_stats.assert_has_calls(calls, any_order=False)

    # assert winner in (sample_boxer1.name, sample_boxer2.name)

    all_boxers = ring_model.get_boxers()
    assert len(all_boxers) == 0, "Ring should be cleared once finished"


def test_fight_unsuccessful(ring_model, sample_boxer1):
    """Test starting a fight in the ring with fewer than two boxers.
    
    """
    ring_model.enter_ring(sample_boxer1)

    assert len(ring_model.ring) == 1
    with pytest.raises(ValueError, match="There must be two boxers to start a fight."):
        ring_model.fight()