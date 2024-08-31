from enum import Enum

class Trend(Enum):
    """
    Enum representing different trends with associated integer values.
    """
    DOWN = -1
    STABLE = 0
    UP = 1

    @staticmethod
    def get_value(trend_str):
        """
        Convert a trend string to its corresponding enum value.

        Args:
            trend_str (str): The trend string to convert (e.g., 'up', 'stable', 'down').

        Returns:
            int: The corresponding enum value.

        Raises:
            KeyError: If the trend string is not a valid enum member.
        """
        return Trend[trend_str.upper()].value

    @staticmethod
    def get_name(trend_value):
        """
        Convert a trend value to its corresponding string name.

        Args:
            trend_value (int): The trend value to convert (e.g., 1, 0, -1).

        Returns:
            str: The corresponding string name in lowercase.

        Raises:
            ValueError: If the trend value is not a valid enum value.
        """
        return Trend(trend_value).name.lower()
