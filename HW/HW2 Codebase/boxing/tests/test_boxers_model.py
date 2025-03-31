from contextlib import contextmanager
import re
import sqlite3

import pytest
from pytest_mock import MockerFixture

import unittest

from unittest.mock import patch
from unittest.mock import MagicMock

from boxing.models.boxers_model import (
    Boxer,
    create_boxer,
    delete_boxer,
    get_leaderboard,
    get_boxer_by_id,
    get_boxer_by_name,
    get_weight_class,
    update_boxer_stats
)

######################################################
#
#    Fixtures
#
######################################################

def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()

@pytest.fixture
def sample_boxer1():
    return Boxer(1, "Boxer 1", 200, 170, 198.5, 30)

@pytest.fixture
def sample_boxer2():
    return Boxer(2, "Boxer 2", 240, 180, 190, 35)

# Mocking the database connection for tests
@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_cursor.commit.return_value = None

    # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn  # Yield the mocked connection object

    mocker.patch("boxing.models.boxers_model.get_db_connection", mock_get_db_connection) #changed 

    return mock_cursor  # Return the mock cursor so we can set expectations per test


######################################################
#
#    Add and delete
#
######################################################


def test_create_boxer(mock_cursor):
    """Test creating a new boxer.

    """
    create_boxer(name="Boxer Name", weight=200, height=170, reach=198.5, age=30)

    expected_query = normalize_whitespace("""
        INSERT INTO boxers (name, weight, height, reach, age)
        VALUES (?, ?, ?, ?, ?)
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call (second element of call_args)
    actual_arguments = mock_cursor.execute.call_args[0][1]
    expected_arguments = ("Boxer Name", 200, 170, 198.5, 30)

    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."


def test_create_boxer_duplicate(mock_cursor):
    """Test creating a boxer with a duplicate boxer name (should raise an error).

    """
    # Simulate that the database will raise an IntegrityError due to a duplicate entry
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: boxers.name,")
    name = 'Boxer 1'
    with pytest.raises(ValueError, match=f"Boxer with name '{name}' already exists"):
        create_boxer(name="Boxer Name", weight=200, height=170, reach=198.5, age=30)


def test_create_boxer_invalid_age():
    """Test error when trying to create a boxer with an invalid age (e.g., less than 18 or greater than 40)

    """
    inv_age = 10
    with pytest.raises(ValueError, match=f"Invalid age: {inv_age}. Must be between 18 and 40."):
        create_boxer(name="Boxer Name", weight=200, height=170, reach=198.5, age=inv_age)
    invalid = "invalid"
    with pytest.raises(ValueError, match=f"Invalid age: {invalid}. Must be between 18 and 40."):
        create_boxer(name="Boxer Name", weight=200, height=170, reach=198.5, age=invalid)


def test_create_boxer_invalid_reach():
    """Test error when trying to create a boxer with an invalid reach (e.g., less than 0)

    """
    inv_reach = -5
    with pytest.raises(ValueError, match=f"Invalid reach: {inv_reach}. Must be greater than 0."):
        create_boxer(name="Boxer Name", weight=200, height=170, reach=inv_reach, age=30)
    invalid = "invalid"
    with pytest.raises(ValueError, match=f"Invalid reach: {invalid}. Must be greater than 0."):
        create_boxer(name="Boxer Name", weight=200, height=170, reach=invalid, age=30)

def test_create_boxer_invalid_height():
    """Test error when trying to create a boxer with an invalid height (e.g., less than 0)

    """
    inv_height = -5
    with pytest.raises(ValueError, match=f"Invalid height: {inv_height}. Must be greater than 0."):
        create_boxer(name="Boxer Name", weight=200, height=inv_height, reach=198.5, age=30)
    invalid = "invalid"
    with pytest.raises(ValueError, match=f"Invalid height: {invalid}. Must be greater than 0."):
        create_boxer(name="Boxer Name", weight=200, height=invalid, reach=198.5, age=30)

def test_create_boxer_invalid_weight():
    """Test error when trying to create a boxer with an invalid weight (e.g., less than 125)

    """
    inv_weight = 120
    with pytest.raises(ValueError, match=f"Invalid weight: {inv_weight}. Must be at least 125."):
        create_boxer(name="Boxer Name", weight=inv_weight, height=170, reach=198.5, age=30)
    invalid = "invalid"
    with pytest.raises(ValueError, match=f"Invalid weight: {invalid}. Must be at least 125."):
        create_boxer(name="Boxer Name", weight=invalid, height=170, reach=198.5, age=30)

def test_delete_boxer(mock_cursor):
    """Test deleting a boxer by boxer ID.

    """
    # Simulate the existence of a boxer w/ id=1
    # We can use any value other than None
    mock_cursor.fetchone.return_value = (True)

    delete_boxer(1)

    expected_select_sql = normalize_whitespace("SELECT id FROM boxers WHERE id = ?")
    expected_delete_sql = normalize_whitespace("DELETE FROM boxers WHERE id = ?")

    # Access both calls to `execute()` using `call_args_list`
    actual_select_sql = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    actual_delete_sql = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    assert actual_select_sql == expected_select_sql, "The SELECT query did not match the expected structure."
    assert actual_delete_sql == expected_delete_sql, "The UPDATE query did not match the expected structure."

    # Ensure the correct arguments were used in both SQL queries
    expected_select_args = (1,)
    expected_delete_args = (1,)

    actual_select_args = mock_cursor.execute.call_args_list[0][0][1]
    actual_delete_args = mock_cursor.execute.call_args_list[1][0][1]

    assert actual_select_args == expected_select_args, f"The SELECT query arguments did not match. Expected {expected_select_args}, got {actual_select_args}."
    assert actual_delete_args == expected_delete_args, f"The UPDATE query arguments did not match. Expected {expected_delete_args}, got {actual_delete_args}."


def test_delete_boxer_bad_id(mock_cursor):
    """Test error when trying to delete a non-existent boxer.

    """
    # Simulate that no boxer exists with the given ID
    mock_cursor.fetchone.return_value = None
    boxer_id = 999
    with pytest.raises(ValueError, match=f"Boxer with ID {boxer_id} not found."):
        delete_boxer(999)


######################################################
#
#    Get Leaderboard
#
######################################################

def test_leaderboard_with_wins(mock_db_connection, mocker):
    """Testing valid leaderboard by wins

    """
    mock_cursor = mocker.MagicMock()
    mock_conn = mock_db_connection.return_value.__enter__.return_value
    mock_conn.cursor.return_value = mock_cursor


    mock_cursor.fetchall.return_value = [
        (1, 'Boxer 1', 200, 170, 198.5, 30, 12, 10, 0.833),
        (2, 'Boxer 2', 150, 175, 190.5, 28, 6, 5, 0.833)
    ]

    leaderboard = get_leaderboard("wins")

    assert len(leaderboard) == 2
    assert leaderboard[0]['name'] == 'Boxer 1'
    assert leaderboard[0]['wins'] == 10
    assert leaderboard[1]['name'] == 'Boxer 2'
    assert leaderboard[0]['wins'] == 5

def test_leaderboard_with_pct(mock_db_connection, mocker):
    """Testing valid leaderboard by winp percentage (wins * 1.0 / fights)

    """
    mock_cursor = mocker.MagicMock()
    mock_conn = mock_db_connection.return_value.__enter__.return_value
    mock_conn.cursor.return_value = mock_cursor


    mock_cursor.fetchall.return_value = [
        (1, 'Boxer 1', 200, 170, 198.5, 30, 12, 10, 0.833),
        (2, 'Boxer 2', 150, 175, 190.5, 28, 6, 5, 0.833)
    ]

    leaderboard = get_leaderboard("win_pct")

    assert len(leaderboard) == 2


def test_invalid_leaderboard(mock_cursor):
    """Testing invalid leaderboard by wins * 1.0 / fights where sorting is invalid

    """
    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match=f"Invalid sort_by parameter: {sort_by}"):
        get_leaderboard("invalid")

######################################################
#
#    Get Boxer
#
######################################################

def test_get_boxer_by_id(mock_cursor):
    """Test getting a boxer by id.

    """
    mock_cursor.fetchone.return_value = (1, "Boxer Name", 200, 170, 198.5, 30, False)

    result = get_boxer_by_id(1)

    expected_result = Boxer(1, "Boxer Name", 200, 170, 198.5, 30)

    assert result == expected_result, f"Expected {expected_result}, got {result}"

    expected_query = normalize_whitespace("SELECT id, name, weight, height, reach, age FROM boxers WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    actual_arguments = mock_cursor.execute.call_args[0][1]
    expected_arguments = (1,)

    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."


def test_get_boxer_by_bad_id(mock_cursor):
    """Test error when getting a non-existent boxer.

    """
    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match=f"Boxer with ID {boxer_id} not found."):
        get_boxer_by_id(999)


def test_get_boxer_by_name(mock_cursor):
    """Test getting a boxer by name.

    """
    mock_cursor.fetchone.return_value = (1, "Boxer Name", 200, 170, 198.5, 30, False)

    result = get_boxer_by_name("Boxer Name")

    expected_result = Boxer(1, "Boxer Name", 200, 170, 198.5, 30)

    assert result == expected_result, f"Expected {expected_result}, got {result}"

    expected_query = normalize_whitespace("SELECT id, name, weight, height, reach, age FROM boxers WHERE name = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    actual_arguments = mock_cursor.execute.call_args[0][1]
    expected_arguments = ("Boxer Name")
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."


def test_get_boxer_by_bad_name(mock_cursor):
    """Test error when getting a non-existent boxer.

    """
    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match=f"Boxer '{boxer_name}' not found."):
        get_boxer_by_name("Boxer Name")

######################################################
#
#    Get Weight
#
######################################################

def get_weight_class_by_weight(mock_cursor):
    """Test getting a weight class by weight.

    """
    mock_cursor.fetchone.return_value = (1, "Boxer Name", 200, 170, 198.5, 30, False)

    result = get_weight_class(mock_cursor.weight) #double check

    expected_result = 'MIDDLEWEIGHT'

    assert result == expected_result, f"Expected {expected_result}, got {result}"

    expected_query = normalize_whitespace("SELECT id, name, weight, height, reach, age FROM boxers WHERE name = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    actual_arguments = mock_cursor.execute.call_args[0][1]
    expected_arguments = (mock_cursor.weight)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_get_weight_class_by_bad_weight(mock_cursor):
    """Test error when getting an invalid weight class via invalid weight.

    """
    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match=f"Invalid weight: {weight}. Weight must be at least 125."):
        get_weight_class_by_weight(mock_cursor.weight)

######################################################
#
#    Update Boxer
#
######################################################


def test_update_boxer_stats(mock_cursor):
    """Test updating the stats of a boxer.

    """
    mock_cursor.fetchone.return_value = True

    boxer_id = 1
    update_boxer_stats(boxer_id)

    expected_query = normalize_whitespace("""
        UPDATE boxers SET boxer_count = boxer_count + 1 WHERE id = ?
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    actual_arguments = mock_cursor.execute.call_args_list[1][0][1]
    expected_arguments = (boxer_id,)

    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."



def test_update_boxer_stats_bad_result(mock_cursor):
    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match=f"Invalid result: {result}. Expected 'win' or 'loss'."):
        get_weight_class_by_weight(mock_cursor.weight)



def test_update_boxer_stats_bad_id(mock_cursor):
    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match=f"Boxer with ID {boxer_id} not found."):
        get_weight_class_by_weight(mock_cursor.weight)
