from dataclasses import dataclass
import logging
import sqlite3
from typing import Any, List

from boxing.utils.sql_utils import get_db_connection
from boxing.utils.logger import configure_logger


logger = logging.getLogger(__name__)
configure_logger(logger)


@dataclass
class Boxer:
    id: int
    name: str
    weight: int
    height: int
    reach: float
    age: int
    weight_class: str = None

    def __post_init__(self): # DO CHECKS?
    #Docstring
    """Initializes the BoxingModel with a weight and automatically assign weight class

        """
        self.weight_class = get_weight_class(self.weight)  # Automatically assign weight class


def create_boxer(name: str, weight: int, height: int, reach: float, age: int) -> None: # DOCSTRINGS AND LOGGING
    #Docstring 
    """Adds a boxer.

        Args:
            name (str): The name of the boxer. 
            weight (int): The weight of the boxer. 
            height (int): The height of the boxer. 
            reach (float): The length of their arm. 
            age (int): The age of the boxer. 

        Raises:
            ValueError: If a boxer with the same name already exists. Or a 
                boxer has an invalid weight, height, reach or age.

     """
    logger.info("Received request to add a song to the playlist") #logging

    #added logging statements to all if statements 
    #double check logging statements
    if weight < 125:
        logger.error("Invalid weight: Weight must be at least 125")
        raise ValueError(f"Invalid weight: {weight}. Must be at least 125.")
    if height <= 0:
        logger.error("Invalid height: Height must be greater than 0.")
        raise ValueError(f"Invalid height: {height}. Must be greater than 0.")
    if reach <= 0:
        logger.error("Invalid reach: Reach must be greater than 0.")
        raise ValueError(f"Invalid reach: {reach}. Must be greater than 0.")
    if not (18 <= age <= 40):
        logger.error("Invalid age: age must be between 18 and 40.")
        raise ValueError(f"Invalid age: {age}. Must be between 18 and 40.")

    try: 
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Check if the boxer already exists (name must be unique)
            cursor.execute("SELECT 1 FROM boxers WHERE name = ?", (name,))
            if cursor.fetchone():
                logger.error("Invalid name: Boxer with name already exists, and name must be unique.") #logging
                raise ValueError(f"Boxer with name '{name}' already exists")

            cursor.execute("""
                INSERT INTO boxers (name, weight, height, reach, age)
                VALUES (?, ?, ?, ?, ?)
            """, (name, weight, height, reach, age))

            conn.commit()

    except sqlite3.IntegrityError:
        logger.error("Invalid name: Boxer with name already exists") #added logging, double check
        raise ValueError(f"Boxer with name '{name}' already exists")

    except sqlite3.Error as e:
        raise e


def delete_boxer(boxer_id: int) -> None: # DOCSTRINGS AND LOGGING
    #Docstring
     """Removes a boxer by their boxer ID.

        Args:
            boxer_id (int): The ID of the boxer to remove. 

        Raises:
            ValueError: If the boxer ID is not found or is invalid.

        """
    logger.info(f"Received request to remove boxer with ID {boxer_id}") #logging

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM boxers WHERE id = ?", (boxer_id,))
            if cursor.fetchone() is None:
                logger.warning(f"Boxer with ID {boxer_id} not found.") #logging
                raise ValueError(f"Boxer with ID {boxer_id} not found.")

            cursor.execute("DELETE FROM boxers WHERE id = ?", (boxer_id,))
            conn.commit()

    except sqlite3.Error as e:
        raise e

def get_leaderboard(sort_by: str = "wins") -> List[dict[str, Any]]: # DOCSTRINGS AND LOGGING
    #Docstring 
    #double check 
    """Retrieves the leaderboard by the top ratios of wins over fights.

        Args:
            sort_by (str): String sorting the most amout of wins.

        Returns:
            Song: List representing the leaderboard by the amount of wins 

        Raises:
            ValueError: If the sorting is invalid.

        """

    query = """
        SELECT id, name, weight, height, reach, age, fights, wins,
               (wins * 1.0 / fights) AS win_pct
        FROM boxers
        WHERE fights > 0
    """

    if sort_by == "win_pct":
        query += " ORDER BY win_pct DESC"
    elif sort_by == "wins":
        query += " ORDER BY wins DESC"
    else:
        logger.warning(f"Sorting parameter is invalid.") #logging
        raise ValueError(f"Invalid sort_by parameter: {sort_by}")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

        leaderboard = []
        for row in rows:
            boxer = {
                'id': row[0],
                'name': row[1],
                'weight': row[2],
                'height': row[3],
                'reach': row[4],
                'age': row[5],
                'weight_class': get_weight_class(row[2]),  # Calculate weight class
                'fights': row[6],
                'wins': row[7],
                'win_pct': round(row[8] * 100, 1)  # Convert to percentage
            }
            leaderboard.append(boxer)

        logger.info(f"Successfully created and returned leaderboard.") #logging
        return leaderboard

    except sqlite3.Error as e:
        raise e

#may need to add logger.info to confirm success of method
def get_boxer_by_id(boxer_id: int) -> Boxer: # DOCSTRINGS AND LOGGING
    #Docstring 
    """Retrieves a boxer by their boxer ID.

        Args:
            boxer_id (int): The ID of the boxer to retrieve.

        Returns:
            Boxer: The boxer with the specified ID.

        Raises:
            ValueError: If the boxer is not found.

        """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, weight, height, reach, age
                FROM boxers WHERE id = ?
            """, (boxer_id,))

            row = cursor.fetchone()

            if row:
                boxer = Boxer(
                    id=row[0], name=row[1], weight=row[2], height=row[3],
                    reach=row[4], age=row[5]
                )
                logger.info(f"Successfully retrieved boxer: {boxer_id}") #logging
                return boxer
            else:
                logger.warning(f"Boxer with ID {boxer_id} not found.") #logging
                raise ValueError(f"Boxer with ID {boxer_id} not found.")

    except sqlite3.Error as e:
        raise e
    

def get_boxer_by_name(boxer_name: str) -> Boxer: # DOCSTRINGS AND LOGGING
    #Docstring
    """Retrieves a boxer by its name.

        Args:
            boxer_name (str): The boxer name to retrieve.

        Returns:
            Boxer: The boxer with the boxer name.

        Raises:
            ValueError: If the playlist is empty or the track number is invalid.

        """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, weight, height, reach, age
                FROM boxers WHERE name = ?
            """, (boxer_name,))

            row = cursor.fetchone()

            if row:
                boxer = Boxer(
                    id=row[0], name=row[1], weight=row[2], height=row[3],
                    reach=row[4], age=row[5]
                )
                logger.info(f"Successfully retrieved boxer with name: {boxer_name}") #logging
                return boxer
            else:
                logger.warning(f"Boxer with name {boxer_name} not found.")#logging
                raise ValueError(f"Boxer '{boxer_name}' not found.")

    except sqlite3.Error as e:
        raise e


def get_weight_class(weight: int) -> str: # DOCSTRINGS AND LOGGING
    #Docstring 
    """Retrieves the weight class for a specific weight.

        Args:
            weight (int): The weight of the weight class to retrieve.

        Returns:
            str: The name of the weight class for the weight. 

        Raises:
            ValueError: If the weight is invalid.

        """
    if weight >= 203:
        weight_class = 'HEAVYWEIGHT'
    elif weight >= 166:
        weight_class = 'MIDDLEWEIGHT'
    elif weight >= 133:
        weight_class = 'LIGHTWEIGHT'
    elif weight >= 125:
        weight_class = 'FEATHERWEIGHT'
    else:
        logger.warning(f"Invalid weight: {weight}. Weight must be at least 125.") #logging
        raise ValueError(f"Invalid weight: {weight}. Weight must be at least 125.")

    logger.info(f"Successfully retrieved weight class for weight: {weight}.") #logging
    return weight_class


def update_boxer_stats(boxer_id: int, result: str) -> None: # DOCSTRIGNS AND LOGGING
    #Docstring
    """Updates a boxer's statistics.

        Args:
            boxer_id (int): Boxer with the boxer ID.
            result (str): Result of the updated statistics.

        Raises:
            ValueError: If the result is invalid or the boxer ID is not found.

        """
    if result not in {'win', 'loss'}:
        logger.warning(f"Invalid result: {result}. Expected 'win' or 'loss'.") #logging
        raise ValueError(f"Invalid result: {result}. Expected 'win' or 'loss'.")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM boxers WHERE id = ?", (boxer_id,))
            if cursor.fetchone() is None:
                logger.warning(f"Boxer with ID {boxer_id} not found.") #logging
                raise ValueError(f"Boxer with ID {boxer_id} not found.")

            if result == 'win':
                cursor.execute("UPDATE boxers SET fights = fights + 1, wins = wins + 1 WHERE id = ?", (boxer_id,))
            else:  # result == 'loss'
                cursor.execute("UPDATE boxers SET fights = fights + 1 WHERE id = ?", (boxer_id,))

            conn.commit()

    except sqlite3.Error as e:
        raise e
