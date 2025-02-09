import db
from datetime import datetime
import pandas as pd
import analysis as a

class Habit:

    """ Represents a habit with tracking and database integration.
    
    Attributes:
    -----------
        name (str): 
            The name of the habit.

        period (str): 
            The tracking frequency.

        description (str, optional): 
            A short description of the habit.

        active (bool): 
            Whether the habit is currently active.

        db_name (str): 
            The name of the database file.

        streak_complete (bool): 
            Tracks whether the habit's streak is currently complete.

    """

    valid_periods = ("day", "week", "month", "quarter", "year")

    def __init__(
        self, 
        name: str, 
        period:str="day", 
        description: str = None, 
        active: bool = True,
        db_name: str = "main.db"
    ):
        
        """ Initializes a Habit instance.

        Parameter:
        ----_
            name (str): 
                The name of the habit.

            period (str, optional): 
                The tracking frequency. Defaults to 'day'.

            description (str, optional):
                A short description of the habit.

            active (bool, optional): 
                Whether the habit is active. Defaults to True.

            db_name (str, optional): 
                Database file name. Defaults to 'main.db'.
        """

        self._set_period(period)
        self.name = name
        self.description = description
        self.active = active
        self.db_name = db_name
        self.streak_complete = False

        if not db._is_in_db(
            name = self.name,
            db_name = self.db_name):
            self.add()
    

    def _set_period(self, period: str):

        """ Checks if the period selected is valid

        Raises:
        -------
            ValueError
                If the choosen period is not a valid period

        """

        if period not in self.valid_periods:
            raise ValueError(f"Invalid period '{period}'. Valid options are: {self.valid_periods}")
        self.period = period


    def add(self) -> str:

        """
        Adds the habit to the database.

        Raises:
        -------
            ValueError: 
                If the habit already exists in the database.

        Returns:
        --------
            str: 
                A confirmation message if the habit is successfully added.

        """

        result = db.add_habit(
            self.name,
            self.period,
            self.description,
            self.active,
            self.db_name
            )

        if result == f"{self.name} already in database":
            raise ValueError(f"A habit with the name '{self.name}' already exists.")
        else:
            return result


    def modify(
        self,
        new_name: str = None,
        description: str = None,
        period: str = None,
        active: bool = None,
    ) -> str:
        
        """ Modifies habit details in the database.

        Parameter:
        -----
            new_name (str, optional): 
                The new name for the habit.

            description (str, optional): 
                The updated description.

            period (str, optional): 
                The new tracking frequency.

            active (bool, optional): 
                Whether the habit is active.

        Returns:
        --------
            str: A confirmation message if modification is successful.

        """

        result = db.modify_habit(
            name = self.name,
            new_name = new_name,
            description = description,
            period = period,
            active = active,
            db_name = self.db_name
        )

        if result: 
            if new_name:
                self.name = new_name
            
            if description:
                self.description = description

            if period:
                self._set_period(period=period)

            if active is not None:
                self.active = active

        return result


    def delete(self):

        """ Deletes the habit from the database. """

        db.delete_habit(
            name=self.name,
            db_name=self.db_name
        )


    def mark_as_complete(self):

        """ Marks the habit as completed for the current period and updates the database. """

        today = datetime.now().replace(microsecond=0)

        db.streak_complete(
            name = self.name,
            period = self.period,
            date = today,
            db_name = self.db_name,
        )


    def check_completion_status(self):

        """ Checks if the habit has been completed within the current tracking period.

        Updates:
        --------
            self.streak_complete (bool): 
                Sets to True if the habit was completed in the current period.

        """

        today = datetime.now().replace(microsecond=0)

        tracking_df = db.get_tracking_data(
            name = self.name,
            db_name= self.db_name
        )

        if tracking_df.empty:
            self.streak_complete = False
            return
        
        tracking_df["timestamp"] = pd.to_datetime(tracking_df["timestamp"])

        last_entry = tracking_df.nlargest(1, "timestamp").iloc[0]

        start, end = a._dynamic_periods(
            period = self.period,
            timestamp = today,
            previous_period = False
        )

        self.streak_complete = (
            start <= last_entry["timestamp"] <= end and last_entry["status"] == "streak complete"
        )


    def get_current_streak(self) -> int:

        """ Retrieves the current streak count for the habit.

        Returns:
        --------
            int: The number of consecutive periods the habit has been completed.

        """

        current = a.get_current_streak_series(
            name = self.name,
            db_name = self.db_name
        )

        return current