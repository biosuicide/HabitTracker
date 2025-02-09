import pytest
import db
from habittracker import Habit
import analysis as analysis

import sqlite3
import os
from datetime import datetime, timedelta 
import time
import gc

database = "test.db"
today = datetime.now()
test_data = {
        "Eat healthy": {
            "description": "Eat less meat and more vegetables",
            "period": "day",
            "active": 1
        },
        "Drink Enough":{
            "description": "Drink at least 2 liters a day",
            "period": "day",
            "active": 1
        },
        "Workout":{
            "description": "Excercise at least 2 hours",
            "period": "week",
            "active": 1
        },
        "Clean Kitchen":{
            "description": "Clean the sink, workspaces, oven and floor in the kitchen",
            "period":"month",
            "active": 0
        },
        "Pay Taxes":{
            "description":"Collect all relevant documents and do the taxes",
            "period": "year",
            "active": 0

        },
    }

##############################
#           Fixtures         #
##############################

# creating test db_instance
@pytest.fixture
def db_instance():
    con = db.connect_db(database)
    yield con
    db.close_db(con)

@pytest.fixture
def habit():

    clean_up_database()
    db_table_only() 
    
    habit = Habit(
        name = "Eat healthy",
        period = "day",
        description = "test description",
        active = True,
        db_name = database
    )
    return habit

@pytest.fixture(scope="session", autouse=True)
def session_cleanup():

    yield  # Runs all tests first

    gc.collect()

    if os.path.exists(database):
        os.remove(database)

##############################
#          Functions         #
##############################

def create_tracking_data():
    now = datetime.now()
    past_1_day = (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    past_2_day = (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
    past_3_day = (now - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
    past_4_day = (now - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S")
    past_1_week = (now - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")

    return [
        {"habit": "Eat healthy" , "period" : "day", "timestamp": past_1_day},
        {"habit": "Eat healthy" , "period" : "day", "timestamp": past_2_day,},
        {"habit": "Eat healthy" , "period" : "day", "timestamp": past_3_day,},
        {"habit": "Eat healthy" , "period" : "day", "timestamp": past_4_day,},
        {"habit": "Eat healthy" , "period" : "day", "timestamp": now,},
        {"habit": "Workout", "period": "week", "timestamp": past_1_week},
        {"habit": "Workout", "period": "week", "timestamp": now}
    ]

tracking_data = create_tracking_data()

def remove_db(db_name=database):
    if os.path.exists(db_name):
        os.remove(db_name)


def clean_up_database(db_name=database):
    with db.connect_db(db_name) as con:
        con.execute("DROP TABLE IF EXISTS habits")
        con.execute("DROP TABLE IF EXISTS tracking")


def db_table_only(db_name=database):

    with db.connect_db(db_name) as con:
        con.execute("DROP TABLE IF EXISTS habits")
        con.execute("DROP TABLE IF EXISTS tracking")

        con.execute(
            """ CREATE TABLE IF NOT EXISTS habits (
                    name TEXT PRIMARY KEY,
                    description TEXT,
                    period TEXT,
                    active BOOLEAN
                )
            """
        )
        con.execute(
            """CREATE TABLE IF NOT EXISTS tracking (
                tracking_id Integer PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                status TEXT,
                current_period TEXT,
                timestamp DATETIME,
                FOREIGN KEY (name) 
                REFERENCES habits(name) ON DELETE CASCADE ON UPDATE CASCADE
                )
            """
        )
        
        con.commit() 

        habit_table = con.execute(
            """SELECT name 
            FROM sqlite_master 
            WHERE name='habits';
            """
        ).fetchone()

        assert habit_table is not None, "Failed to create 'habits' table."

        tracking_table = con.execute(
            """SELECT name 
            FROM sqlite_master 
            WHERE name='tracking';
            """
        ).fetchone()

        assert tracking_table is not None, "Failed to create 'tracking' table."


def create_db_with_habit_data(test_data=test_data, db_name=database):
    db_table_only()
    for habit, attribute in test_data.items():
        db.add_habit(
            name = habit,
            description = attribute.get("description"),
            period = attribute.get("period"),
            active = attribute.get("active"),
            db_name = db_name
        )


def create_complete_db(tracking_data = tracking_data):
    create_db_with_habit_data()

    for habit in tracking_data:
        db.streak_complete(
            name = habit["habit"], 
            db_name = database,
            period = habit["period"],
            date = habit["timestamp"]
        )

##############################
#       Database TESTS       #
##############################

def test_db_connection():

    con = db.connect_db(":memory:")
    assert con is not None
    result = con.execute("PRAGMA foreign_keys;").fetchone()
    assert result == (1,), "Foreign key constraint is not enabled!"

    db.close_db(con)
    with pytest.raises(sqlite3.ProgrammingError):
        con.execute("SELECT 1")


def test_create_db_table():

    db.create_tables(database)

    with db.connect_db(database) as con:
        cur = con.cursor()
        tables = cur.execute("""SELECT name 
                            FROM sqlite_master 
                            WHERE type='table';
                            """).fetchall()
        
        assert ("habits",) in tables
        assert ("tracking",) in tables

        clean_up_database(database)


def test_is_in_db_exists():

    db.create_tables(database)

    assert db._is_in_db("test_habit", database) == False

    with db.connect_db(database) as con:
        cur = con.cursor()
        cur.execute("""INSERT INTO habits (name, description, period, active) 
                    VALUES ('test_habit', 'Test desc', 'daily', 1);
                    """)
        con.commit()

    assert db._is_in_db("test_habit", database) == True


def test_add_habit():

    db_table_only()

    with db.connect_db(database) as con:

        for habit, attribute in test_data.items():

            assert db._is_in_db(habit, database) == False

            result = db.add_habit(
                        name = habit,
                        period = attribute.get("period"),
                        description = attribute.get("description"),
                        active = True,
                        db_name = database
            )
            
            assert result == f"{habit} added"
            assert db._is_in_db(habit, database) == True

            duplicate_result = db.add_habit(
                        name = habit,
                        period = attribute.get("period"),
                        description = attribute.get("description"),
                        active = True,
                        db_name = database
            )
            assert duplicate_result == f"{habit} already in database"

        clean_up_database()


@pytest.mark.parametrize(
        "name, new_name, description, period, active, expected_result",
        [
            ("Eat healthy", 
             "Eat really healthy", 
             "Eat more vegetables and no meat",
              "year", 
              True, 
              "Eat healthy updated"
            ),
            ("Nonexistent", 
             "Still nonexistent", 
             None, 
             None, 
             None, 
             "Nonexistent not in Database"
            ),
            ("Drink Enough", 
             None, 
             None, 
             None, 
             None, 
             "No changes requested"
            ),
        ]
)
def test_modify_habit(
    name, 
    new_name, 
    description, 
    period, 
    active, 
    expected_result, 
):  

    create_db_with_habit_data()

    with db.connect_db(database) as con:
        result = db.modify_habit(
            name=name,
            new_name=new_name,
            description=description,
            period=period,
            active=active,
            db_name=database
        )
        
        assert result == expected_result, f"unexpected result: {result}"

        if result is None and new_name:
            result = con.execute(
                """SELECT name, description, period 
                    FROM habits 
                    WHERE name = ? ;
                """,
                (new_name,)
            ).fetchone()
            
            assert result is not None, "Updated habit not found in the database"
            assert result[0] == new_name, f"Unexpected name: {result[0]}"

            if description:
                assert result[1] == description, f"Unexpected description: {result[1]}"

            if period is not None:
                assert result[2] == period, f"Unexpected period: {result[2]}"


        clean_up_database()


@pytest.mark.parametrize(
    "habit, expected_result",
    [
        ("Eat healthy", "Eat healthy deleted"),
        ("Nonexistent", "Nonexistent not in database")
    ]
)
def test_delete_habit(habit, expected_result, db_name=database):
    create_db_with_habit_data()

    result = db.delete_habit(
        name=habit, 
        db_name=db_name)
    
    assert result == expected_result, f"{habit} was not deleted"

    clean_up_database()


def test_get_active_habits(db_name=database):

    create_db_with_habit_data()

    result = db.get_active(db_name)
    assert len(result) == 3, f"Expected 5 active habits, got {len(result)}"

    db.modify_habit(
        name= "Eat healthy",
        active=False,
        db_name=db_name
    )

    result = db.get_active(db_name)
    assert len(result) == 2, f"Unexpected result: {result}"
    clean_up_database()


def test_get_inactive_habits(db_name=database):
    create_db_with_habit_data()

    with db.connect_db(db_name) as con:
        result = db.get_inactive(db_name)
        assert len(result) == 2, f"Expected 5 active habits, got {len(result)}"

        db.modify_habit(
            name= "Eat healthy",
            active=False,
            db_name=db_name
        )
        result = db.get_inactive(db_name)
        assert len(result) == 3, f"Unexpected result: {result}"

        clean_up_database()


def test_insert_tracking_data(db_name=database):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 

    create_db_with_habit_data() 

    db.streak_complete(
        name="Eat healthy",
        period="day",
        date=now,
        db_name=db_name
    )

    with db.connect_db(db_name) as con: 
        result = con.execute(
            """SELECT * 
            FROM tracking 
            WHERE name = ? 
            AND status = ?
            ORDER BY timestamp DESC
            LIMIT 1;
            """,
            ("Eat healthy", "streak complete")
        )
        row = result.fetchone()

    assert row is not None, "No tracking data found in the database"
    assert row[1] == "Eat healthy"
    assert row[2] == "streak complete"
    assert row[3] == "day"
    assert row[4] == now 

    clean_up_database()


@pytest.mark.parametrize(
    "name, expected_result",
    [
        ("Eat healthy", 6),
        (None, 12),
    ]
)
def test_get_tracking_data(
    name,
    expected_result, 
):

    create_complete_db()
    try:
        result = db.get_tracking_data(
            name = name,
            db_name = database
        )

        assert len(result) == expected_result, f"Expected {expected_result} rows, but got {len(result)}. Data: {result}"
        assert set(result.columns) == {
            "tracking_id", 
            "name", 
            "status", 
            "current_period", 
            "timestamp"
            }, "Unexpected columns"

    finally:
        clean_up_database()


def test_get_habit_data():
    create_db_with_habit_data()

    for habit_name, expected_values in test_data.items():

        result = db.get_habit_data(
            name = habit_name, 
            db_name = database
        )

        assert not result.empty, "Expected non-empty DataFrame"
        assert result.iloc[0]["name"] == habit_name
        assert result.iloc[0]["description"] == expected_values["description"]
        assert result.iloc[0]["period"] ==  expected_values["period"]
        assert result.iloc[0]["active"] == expected_values["active"]

##############################
#     habit class TESTS      #
##############################

def test_class_habit_init():

    clean_up_database()
    db_table_only() 

    habit = Habit(
        name="test habit",
        period="day",
        description="test description",
        active=True,
        db_name=database
        )
    
    assert habit.name == "test habit"
    assert habit.period == "day"
    assert habit.description == "test description"
    assert habit.active == True


def test_add_habit(habit):

    db_table_only()

    result = habit.add()
    assert result == f"{habit.name} added"

    # clean up 
    db.delete_habit(habit.name, database)


@pytest.mark.parametrize(
        "new_name, description, period, active",
        [
            ("new_habit", 
             "a new description", 
             "week",
             False, 
            ),
        ]
)
def test_class_modification( 
    new_name,
    description,
    period,
    active,
    db_name = database
):

    clean_up_database()
    db_table_only()

    habit = Habit(
        name = "test habit",
        period = "day",
        description = "test description",
        active = True,
        db_name = database
    )

    old_name = habit.name
    old_description = habit.description
    old_period = habit.period
    old_active = habit.active

    with db.connect_db(db_name) as con:
        result = con.execute(
                """SELECT * 
                FROM habits 
                WHERE name = ? ;
                """, 
                (habit.name,)
            ).fetchone()

        old_db_name = result[0]
        old_db_description = result[1]
        old_db_period = result[2]
        old_db_status = result[3]

    habit.modify(new_name, description, period, active)

    with db.connect_db(db_name) as con:
        result = con.execute(
                """SELECT * 
                FROM habits 
                WHERE name = ? ;
                """, 
                (new_name,)
            ).fetchone()
        new_db_name = result[0]
        new_db_description = result[1]
        new_db_period = result[2]
        new_db_status = result[3]

    if new_name != None:
        assert old_name != habit.name
        assert new_name == habit.name
        assert old_db_name != new_db_name
    
    if description != None:
        assert old_description != habit.description
        assert description == habit.description
        assert old_db_description != new_db_description
    
    if period != None:
        assert old_period != habit.period
        assert period == habit.period
        assert old_db_period != new_db_period
    
    if active != None:
        assert old_active != habit.active
        assert active == habit.active
        assert old_db_status != new_db_status

    clean_up_database()


def test_delete_habit(habit):

    db_table_only()

    habit.add()
    name = habit.name

    is_in_db = db._is_in_db(name, database)

    assert is_in_db == True

    habit.delete()

    is_in_db = db._is_in_db(name, database)

    assert is_in_db == False

    clean_up_database()


def test_mark_as_complete(habit):

    clean_up_database()
    db_table_only()

    habit.add()    
    habit.mark_as_complete()

    with db.connect_db(database) as con:
        result = con.execute(
                """SELECT * 
                FROM tracking 
                WHERE name = ? ;
                """, 
                (habit.name,)
            ).fetchall()
        
    assert len(result) == 2
    assert result[0][2] == "active"
    assert result[1][2] == "streak complete"

    clean_up_database()


def test_check_completion_status(habit):

    clean_up_database()
    db_table_only()

    habit.add()
    habit.check_completion_status()
       
    assert habit.streak_complete is False
    time.sleep(1)

    habit.mark_as_complete()

    habit.check_completion_status()
    assert habit.streak_complete is True

    clean_up_database()


def test_current_streak(habit):

    clean_up_database()
    create_complete_db()

    result = habit.get_current_streak()
    assert result == 5
   

##############################
#     Analysis TESTS         #
##############################

@pytest.mark.parametrize("period, timestamp, previous_period, expected", [

    ("day", datetime(2025, 2, 9, 14, 30), False, 
     (datetime(2025, 2, 9, 0, 0, 0), datetime(2025, 2, 9, 23, 59, 59))),
    ("day", datetime(2025, 2, 9, 14, 30), True,  
     (datetime(2025, 2, 8, 0, 0, 0), datetime(2025, 2, 8, 23, 59, 59))),

    ("week", datetime(2025, 2, 9), False, 
     (datetime(2025, 2, 3), datetime(2025, 2, 9, 23, 59, 59))),
    ("week", datetime(2025, 2, 9), True,  
     (datetime(2025, 1, 27), datetime(2025, 2, 2, 23, 59, 59))),

    ("month", datetime(2025, 2, 15), False, 
     (datetime(2025, 2, 1), datetime(2025, 2, 28, 23, 59, 59))),
    ("month", datetime(2024, 3, 20), True,  
     (datetime(2024, 2, 1), datetime(2024, 2, 29, 23, 59, 59))),  # Leap year case

    ("quarter", datetime(2025, 5, 10), False,  
     (datetime(2025, 4, 1), datetime(2025, 6, 30, 23, 59, 59))),
    ("quarter", datetime(2025, 5, 10), True,  
     (datetime(2025, 1, 1), datetime(2025, 3, 31, 23, 59, 59))),

    ("year", datetime(2025, 7, 10), False,  
     (datetime(2025, 1, 1), datetime(2025, 12, 31, 23, 59, 59))),
    ("year", datetime(2025, 7, 10), True,  
     (datetime(2024, 1, 1), datetime(2024, 12, 31, 23, 59, 59))),
])
def test_dynamic_periods(period, timestamp, previous_period, expected):

    start, end = analysis._dynamic_periods(period, timestamp, previous_period)
    assert start == expected[0], f"Expected start {expected[0]}, got {start}"
    assert end == expected[1], f"Expected end {expected[1]}, got {end}"

@pytest.mark.parametrize("habit_name, expected_streak", [
    ("Eat healthy", 5),
    ("Drink Enough", 0), 
    ("Workout", 2),       
])
def test_current_streak_series(habit_name, expected_streak):

    clean_up_database()
    create_complete_db()
    
    streak_count = analysis.get_current_streak_series(
        name = habit_name, 
        db_name = database
    )

    assert streak_count == expected_streak

    clean_up_database()


@pytest.mark.parametrize("habit_name, period, expected_streak, expected_break", [
    ("Eat healthy", "day", 2, 0),
    ("Workout", "week", 1, 0),
    ("Drink Enough", "day", 0, 0),
    ("all", "all", 3, 0),
])
def test_get_habits_series(habit_name, period, expected_streak, expected_break):

    clean_up_database()
    create_complete_db()

    result = analysis.get_habits_series(
        name=habit_name, 
        period=period, 
        all_series=True,
        db_name=database
    )

    if result is not None:
        streak_count = result
        break_count = result

    elif result.empty:
        assert expected_streak == 0 and expected_break == 0, f"For habit '{habit_name}', expected empty DataFrame."


        assert streak_count == expected_streak, f"For habit '{habit_name}', expected streak {expected_streak}, got {streak_count}"
        assert break_count == expected_break, f"For habit '{habit_name}', expected break {expected_break}, got {break_count}"
    clean_up_database()


@pytest.mark.parametrize("period, expected_habits", [
    ("day", ["Eat healthy", "Drink Enough"]),
    ("week", ["Workout"]), 
    ("month", [] ),
    (None, ["Eat healthy", "Drink Enough", "Workout"]),  
])
def test_get_active_habits_for_period(period, expected_habits):

    clean_up_database()
    create_complete_db()

    result_df = analysis.get_active_habits_for_period(period, db_name="test.db")

    result_habits = result_df["name"].tolist() if not result_df.empty else []

    assert result_habits == expected_habits, f"Expected {expected_habits}, got {result_habits}"

    clean_up_database()

@pytest.hookimpl(tryfirst=True)
def pytest_sessionfinish(session, exitstatus):
    """Hook to run a function after all tests are executed."""
    print("\n[pytest] All tests finished. Running final cleanup...")
    remove_db()