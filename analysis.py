import db
import pandas as pd
from datetime import datetime, timedelta
import calendar
from dateutil.relativedelta import relativedelta

# start of analysis

def _dynamic_periods(
        period: str,
        timestamp: datetime,
        previous_period: bool = True
) -> tuple[datetime, datetime]:

    """ Computes the start and end timestamps for a given period.

    Parameter:
    -----
        period (str): 
            The period type ('day', 'week', 'month', 'quarter', 'year').

        timestamp (datetime): 
            The reference timestamp.

        previous_period (bool, optional): 
            Whether to shift to the previous period. Defaults to True.

    Returns:
    --------
        tuple[datetime, datetime]: 
            Start and end timestamps for the computed period.

    """


    if period == "day":
        start = timestamp.replace(hour=0, minute=0, second=0)
        end = timestamp.replace(hour=23, minute=59, second=59)

        if previous_period:
            start = start - timedelta(days=1)
            end = end - timedelta(days=1)

    elif period == "week":
        weekday = timestamp.weekday()
        start = timestamp - timedelta(days=weekday)
        start = start.replace(hour=0, minute=0, second=0)
        end = timestamp + timedelta(days=(6- weekday))
        end = end.replace(hour=23, minute=59, second=59)

        if previous_period:
            start = start - timedelta(days=7)
            start = start.replace(hour=0, minute=0, second=0)
            end = end - timedelta(days=7)

    elif period == "month":
        start = timestamp.replace(day=1, hour=0, minute=0, second=0)
        last_day = calendar.monthrange(
                timestamp.year, 
                timestamp.month
        )[1] 

        end = timestamp.replace(day=last_day, hour=23, minute=59, second=59)
        
        if previous_period:
            start = start - relativedelta(months=1)
            start.replace(hour=0, minute=0, second=0)
            last_day = calendar.monthrange(
                start.year, 
                start.month
            )[1]

            end = end - relativedelta(months=1)
            end = end.replace(day=last_day, hour=23, minute=59, second=59)

    elif period =="quarter":
        start_quarter = ((timestamp.month - 1) // 3) * 3 + 1
        start = timestamp.replace(month=start_quarter, day=1)
        start.replace(hour=0, minute=0, second=0)
        end_quarter_month = ((timestamp.month - 1) // 3 + 1) * 3 
        end_quarter_day = calendar.monthrange(
            timestamp.year, 
            end_quarter_month
        )[1]

        end = timestamp.replace(
            month=end_quarter_month, 
            day=end_quarter_day, 
            hour=23, 
            minute=59, 
            second=59
        )
        
        if previous_period:
            start = start - relativedelta(months=3)
            start.replace(hour=0, minute=0, second=0)
            end_month = start.month + 2
            end_day = calendar.monthrange(
                start.year, 
                end_month
            )[1]

            end = end.replace(
                month=end_month,
                day=end_day,
                hour=23,
                minute=59,
                second=59
            )      

    if period =="year":
        start = timestamp.replace(day=1, month=1, hour=0, minute=0, second=0)
        end = timestamp.replace(day=31, month=12, hour=23, minute=59, second=59)

        if previous_period:
            start = start.replace(year=start.year-1, hour=0, minute=0, second=0)
            end = end.replace(year=end.year-1)
    
    return start, end
 

def get_current_streak_series(
    name: str,
    db_name: str = "main.db" 
) -> int:

    """
    Calculates the current streak count for a specific habit or all habits.

    Parameter:
    -----
        name (str): 
            Name of the habit.
            
        db_name (str, optional): 
            Database file name. Defaults to "main.db".

    Returns:
    -------
        int: 
            The current streak count.

    """

    start = None
    end = None
    count = 0

    tracking_df = db.get_tracking_data(
        name = name,
        db_name = db_name 
    )

    habit_period = db.get_habit_data(
        name = name,
        db_name = db_name 
    )

    if tracking_df.empty:
        return 0 

    tracking_df["timestamp"] = pd.to_datetime(tracking_df["timestamp"])
    tracking_df.sort_values(
        by="timestamp", 
        ascending=False, 
        inplace=True
    )
    
    today = datetime.now().replace(microsecond=0)
    start, end = _dynamic_periods(
        period = habit_period.iloc[0]["period"],
        timestamp = today,
        previous_period=False
    )
    
    for index, row in tracking_df.iterrows():
        if row["status"] != "streak complete":
            continue

        if row["status"] == "streak complete":
            if start <= row["timestamp"] <= end:
                count += 1
                start, end = _dynamic_periods(
                    period = row["current_period"],
                    timestamp = row["timestamp"],
                    previous_period=True
                )

            else:
                break

    return count


def get_habits_series(
        name: str = "all",
        period: str = None,
        all_series: bool = False,
        db_name: str = "main.db"
) -> pd.DataFrame:

    """ Retrieves habit tracking data with streaks and breaks.

    Parameter:
    -----
        name (str, optional): 
            Name of the habit. Defaults to "all".

        period (str, optional): 
            Specific period to filter habits. Defaults to None.
            
        all_series (bool, optional): 
            Whether to include all streaks and breaks. Defaults to False.

    Returns:
    --------
        pd.DataFrame: 
            DataFrame containing habit streak and break data.

    """

    today = datetime.now().replace(microsecond=0)

    df_all_habits = get_active_habits_for_period(period, db_name)

    if df_all_habits.empty:
        return pd.DataFrame(columns=["name", "streak_series", "break_series"])

    ls_habit_names = [name] if name != "all" and name is not None else list(df_all_habits["name"])
    collector = []

    for habit in ls_habit_names:
        streak_count = 0
        break_count = 0

        habit_data = db.get_habit_data(name=habit, db_name=db_name)
        if habit_data.empty:
            continue  
        
        tracking_df = db.get_tracking_data(name=habit, db_name=db_name)
        if tracking_df.empty:
            continue  

        tracking_df["timestamp"] = pd.to_datetime(tracking_df["timestamp"])
        tracking_df.sort_values(by="timestamp", ascending=False, inplace=True)

        start, end = _dynamic_periods(
            period=habit_data.iloc[0]["period"], 
            timestamp=today, 
            previous_period=False
        )

        for _, row in tracking_df.iterrows():
            if row["status"] != "streak complete":
                continue

            if start <= row["timestamp"] <= end:
                streak_count += 1

                start, end = _dynamic_periods(
                    period=row["current_period"], 
                    timestamp=row["timestamp"], 
                    previous_period=True
                )

                if break_count > 0:
                    collector.append((habit, 0, break_count))    
                    break_count = 0

            else:
                if streak_count > 0:
                    collector.append((habit, streak_count, 0))
                    streak_count = 0

                break_count += 1

                start, end = _dynamic_periods(
                    period=row["current_period"], 
                    timestamp=row["timestamp"], 
                    previous_period=True
                )
            
            collector.append((habit, streak_count, break_count))

    df_result = pd.DataFrame(collector, columns=["name", "streak_series", "break_series"])

    if not all_series:
        max_streak = df_result["streak_series"].max() if not df_result.empty else 0
        return pd.DataFrame([{"name": name, "streak_series": max_streak, "break_series": 0}])

    return df_result


def get_active_habits_for_period(
        period: str = None,
        db_name: str = "main.db"
) -> pd.DataFrame:
    
    """
    Retrieves active habits from the database filtered by a specific period.

    Parameter:
    ----------
        period (str, optional): 
            The period to filter habits by. 
            If None or "all", returns all active habits. Defaults to None.

    Returns:
    --------
        pd.DataFrame: 
            A DataFrame containing habit names and their respective periods.
            Empty DataFrame with columns if no habits are found.
    
    """

    all_habits = db.get_habit_data(db_name=db_name)
    all_habits = all_habits[all_habits["active"] == 1]

    if not isinstance(all_habits, pd.DataFrame) or all_habits.empty:
        return pd.DataFrame(columns=["name", "period"])
    
    if period == None or period == "all":
        df_habit = all_habits.drop(["description", "active"], axis=1)
        return df_habit
    
    else:
        if "period" in all_habits.columns:
            df_habit = all_habits[all_habits["period"].str.contains(period)]
            df_habit = df_habit.drop(["description", "active"], axis=1)
            return df_habit
        
        else:
            return pd.DataFrame(columns=["name", "period"])
