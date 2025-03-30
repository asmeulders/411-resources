import logging
import math
from typing import List

from boxing.models.boxers_model import Boxer, update_boxer_stats
from boxing.utils.logger import configure_logger
from boxing.utils.api_utils import get_random


logger = logging.getLogger(__name__)
configure_logger(logger)


class RingModel: # DOCSTRINGS
    """
    A class to manage the ring during a bout.

    Attributes:
        ring (List[Boxer]): The list of boxers in the ring.

    """
    def __init__(self): # DOCSTRINGS
        """Initializes the RingModel with an no boxers in the ring.

        """
        self.ring: List[Boxer] = []

    def fight(self) -> str: # DOCSTRINGS AND LOGGING
        """Starts the fight and clears ring when done.

        Raises:
            ValueError: If the fewer than two boxers.

        """
        if len(self.ring) < 2:
            raise ValueError("There must be two boxers to start a fight.")

        logger.info("Getting 2 boxers.")
        boxer_1, boxer_2 = self.get_boxers()

        logger.info("Getting the boxers' skill levels.")
        skill_1 = self.get_fighting_skill(boxer_1)
        skill_2 = self.get_fighting_skill(boxer_2)

        # Compute the absolute skill difference
        # And normalize using a logistic function for better probability scaling
        logger.info("Computing skill difference.")
        delta = abs(skill_1 - skill_2)
        normalized_delta = 1 / (1 + math.e ** (-delta))

        random_number = get_random()

        logger.info("Determining winner.")
        if random_number < normalized_delta:
            winner = boxer_1
            loser = boxer_2
        else:
            winner = boxer_2
            loser = boxer_1

        logger.info(f"The winner is {winner.name}!")
        update_boxer_stats(winner.id, 'win')
        update_boxer_stats(loser.id, 'loss')

        logger.info("The bout is over, clearing the ring.")
        self.clear_ring()

        return winner.name

    def clear_ring(self): # DOCSTRINGS AND LOGGING
        """Clears all boxers from the ring.

        Clears all boxers from the ring. If the ring is already empty, logs a warning.

        """
        logger.info("Received request to clear the ring")
        
        # try:
        #     if self.check_if_empty():
        #         pass
        # except ValueError:
        #     logger.warning("Clearing an empty playlist")

        # self.ring.clear()
        # logger.info("Successfully cleared the playlist")
        
        if not self.ring: # might need some functionality here. do the warning for empty
            return 
        self.ring.clear()
        logger.info("Successfully cleared the playlist")

    def enter_ring(self, boxer: Boxer): # DOCSTRINGS AND LOGGING
        """Adds a boxer to the ring.

        Args:
            boxer (Boxer): The boxer to enter to the ring.

        Raises:
            TypeError: If the boxer is not a valid Boxer instance.
            ValueError: If the ring is full (already has >= 2 boxers).

        """
        logger.info("Received request to add a boxer to the ring")

        if not isinstance(boxer, Boxer):
            logger.error("Invalid type: Boxer is not a valid Boxer instance")
            raise TypeError(f"Invalid type: Expected 'Boxer', got '{type(boxer).__name__}'")

        if len(self.ring) >= 2:
            logger.error(f"The ring is already full with 2 boxers")
            raise ValueError("Ring is full, cannot add more boxers.")

        self.ring.append(boxer)
        logger.info(f"Successfully added boxer to the ring: {boxer.name}")

    def get_boxers(self) -> List[Boxer]: # DOCSTRINGS AND LOGGING
        """Returns the boxers currently in the ring.

        Returns:
            List[Boxers]: The list of boxers in the ring.

        Raises:
            ValueError: If the ring is empty.

        """
        if not self.ring: # there might need to be some functionality here
            logger.error("Ring is empty") # added these two lines
            raise ValueError("Ring is empty")
        else:
            pass

        return self.ring

    def get_fighting_skill(self, boxer: Boxer) -> float: # DOCSTRINGS AND LOGGING
        """Returns the skill of a boxer.

        Returns:
            float: The calculations of a boxer's skill.

        """
        # Arbitrary calculations
        age_modifier = -1 if boxer.age < 25 else (-2 if boxer.age > 35 else 0)
        fighting_skill = (boxer.weight * len(boxer.name)) + (boxer.reach / 10) + age_modifier
        logger.info(f"Retrieving boxer {boxer.name}'s skill: {fighting_skill}")
        return fighting_skill