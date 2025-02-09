import sqlite3
from datetime import datetime 
import pandas as pd

def connect_db(name: str = "main.db") -> sqlite3.Connection:
    """Function connecting to a database

    Parameters
    ----------
    name : str, optional
        The name of the database to connect to. Default is 'main.db'

    Returns
    -------
    sqlite3.Connection
        A connection object to the database with foreign key constraints enabled.

    Raises
    ------
    sqlite3.Error
        If an error occurs while connecting to the database
    """

    try:
        con = sqlite3.connect(name)
        con.execute("PRAGMA foreign_keys = ON;")
        return con
    
    except sqlite3.Error as e:
        raise sqlite3.Error(f"Error connecting to database: {e}") from e

   
def close_db(con: sqlite3.Connection) -> None:
    """Function closing a database connection
    
    Parameters
    ----------
    con : sqlite3.connection
    """

    if con is None:
        raise ValueError("Database connection is None, cannot close.")

    con.close()


def create_tables(db_name: str = "main.db") -> None:
    """Function creating tables in a database
    
    Creates 2 tables in the database:
    - habits: stores information about habits
    - tracking: stores tracking data for habits

    Parameters
    ----------
    db_name : str, optional
        Name of the database file. Default is "main.db"

    """
    with connect_db(db_name) as con:
        cur = con.cursor()
        cur.execute(
            """ CREATE TABLE IF NOT EXISTS habits (
                name TEXT UNIQUE,
                description TEXT,
                period TEXT,
                active BOOLEAN,
                PRIMARY KEY (name)
                )
            """)
        
        
        cur.execute(
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


def _is_in_db(
    name: str, 
    db_name: str = 'main.db'
) -> bool:

    """Helper function checking if a habit is in the database
    
    Parameters
    ----------
    name : str
        The name of the habit to check

    db_name : str
        The database connection object. Default is None

    Returns
    -------
    bool
        True if the habit is in the database, False otherwise
 
    """
    with connect_db(db_name) as con:
        result = con.execute("""SELECT name 
                                FROM habits 
                                WHERE name = ? ;
                                """,
                            (name, ))
        fetched_result = result.fetchone()

        return fetched_result is not None


def add_habit(
    name: str,
    period: str, 
    description: str = None,               
    active: bool = True,
    db_name: str = "main.db"
) -> str:

    """Function adding a habit to the database
    
    This function checks if a connection to a database is given
    and creates one if not. It then checks if the habit is already
    in the database and adds it if not. 

    Parameters
    ----------
    name : str
        The name of the habit

    period : str   
        The period of the habit

    description : str, optional
        A description of the habit. Default is None

    active : bool, optional
        The status of the habit. Default is True

    db_name : str, optional
        Name of the database file. Default is "main.db"
    
    Returns
    -------
    str
        A message indicating the result of adding the habit to the database

    Raises
    ------
    sqlite3.Error
        If an error occurs while adding the habit to the database    
    """
    
    with connect_db(db_name) as con:

        if _is_in_db(name, db_name):
            return f"{name} already in database"
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur = con.cursor()

            status = "active" if active else "inactive"
            description = description or ""

            cur.execute(""" INSERT INTO habits (
                        name, description, period, active) 
                        VALUES (?, ?, ?, ?)
                        """, 
                        (name, description, period, active))
            
            cur.execute(""" INSERT INTO tracking (
                        name, status, current_period, timestamp) 
                        VALUES (?, ?, ?, ?)
                        """, 
                        (name, status, period, timestamp))
            con.commit()
            return f"{name} added"

        except sqlite3.Error as e:
            con.rollback()
            raise


def modify_habit(
    name: str,
    new_name: str = None, 
    description: str = None, 
    period: str = None,
    active: bool = None,
    db_name: str = "main.db"
) -> str:

    """ Function modifying a habit in the database

    This function checks if a connection to a database is given
    and creates one if not. It then checks if the habit is in the
    database and modifies it if it is.

    Parameters
    ----------
    name : str
        The name of the habit to modify

    new_name : str, optional
        The new name of the habit. Default is None

    description : str, optional
        The new description of the habit. Default is None

    period : int, optional
        The new period of the habit. Default is None

    active : bool, optional
        The new status of the habit. Default is None

    db_name : str, optional
        Name of the database file. Default is "main.db"

    Returns
    -------
    str
        A message indicating the result of modifying the habit in the database
    
    Raises
    ------
    sqlite3.Error
        If an error occurs while modifying the habit in the database  
    """
    if new_name is None and description is None and period is None and active is None:
        return "No changes requested"
    
    with connect_db(db_name) as con:
        try:
            cur = con.cursor()

            # build query
            if _is_in_db(name, db_name):
                query = "UPDATE habits SET"
                params =[]
                if new_name is not None:
                    query += " name = ? ,"
                    params.append(new_name)
                if description is not None:
                    query += " description = ? ,"
                    params.append(description)
                if period is not None:
                    query += " period = ? ,"
                    params.append(period)
                if active is not None:
                    query += " active = ? ,"
                    params.append(1 if active else 0)       # as sqlite stores no true bool
        
                query = query.rstrip(",") + " WHERE name = ? ;"
                params.append(name)

                cur.execute(query, params)

                if new_name:
                    cur.execute("""UPDATE tracking 
                                SET name = ? 
                                WHERE name = ? ;
                                """,
                                (new_name, name) )
                con.commit()
               
                return f"{name} updated"

            else:
                return f"{name} not in Database"

        except sqlite3.Error as e:
            con.rollback()
            raise


def delete_habit(
    name: str,
    db_name: str = "main.db"
) -> str:

    """Function deleting a habit from the database
    
    This function checks if a connection to a database is given
    and creates one if not. It then checks if the habit is in the
    database and deletes it if it is.

    Parameters
    ----------
    name : str
        The name of the habit to delete

    db_name : str, optional
        Name of the database file. Default is "main.db"

    Returns
    -------
    str
        A message indicating the result of deleting the habit from the database

    Raises
    ------
    sqlite3.Error
        If an error occurs while deleting the habit from the database
    """

    with connect_db(db_name) as con:
        if not _is_in_db(name, db_name):
            return f"{name} not in database"
        
        cur = con.cursor()
        cur.execute("""DELETE FROM habits 
                    WHERE name = ? ;
                    """,
                    (name, ))

        con.commit()
        return f"{name} deleted"

   
def get_tracking_data(
    name: str = None,
    db_name: str = "main.db"
) -> pd.DataFrame:
    
    """Function getting tracking data for a habit
    
    This function checks if a connection to a database is given
    and creates one if not. It then checks if the habit is in the
    database and gets the tracking data for it.
    
    Parameters
    ----------
    name : str, optional
        The name of the habit to get tracking data for. Default is None

    db_name : str, optional
        Name of the database file. Default is "main.db"

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the tracking data.

    Raises
    ------
    sqlite3.Error
        If an error occurs while getting the tracking data for the habit
    """
    
    with connect_db(db_name) as con:
        if name is not None: 
            if not _is_in_db(name, db_name):
                return pd.DataFrame(columns=[
                    "tracking_id", 
                    "name", 
                    "status", 
                    "current_period", 
                    "timestamp"
                    ]
                )
    
        try:
            cur = con.cursor()
            query = "SELECT * FROM tracking"
            value = []

            if name:
                query += " WHERE name = ?"
                value.append(name)  


            data = cur.execute(query, value)
            col_names = [description[0] for description in cur.description]
            tracking_df = pd.DataFrame(data.fetchall(), columns=col_names)

            return tracking_df
        
        except sqlite3.Error as e:
            raise


def streak_complete(
    name: str,
    period: str,
    date: datetime = None,
    db_name: str = "main.db"
) -> str:

    """Function marking a streak as complete

    This function checks if a connection to a database is given
    and creates one if not. It then checks if the habit is in the
    database and marks the streak as complete.

    Parameters
    ----------
    name : str
        The name of the habit to mark the streak as complete

    period : str
        The period associated with the streak completion.

    date : datetime or str, optional
        The timestamp when the streak was completed (default: current timestamp).

    db_name : str, optional
        Name of the database file. Default is "main.db"

    Returns
    -------
    str
        A message indicating the result of marking the streak as complete 
    
    Raises
    ------
    sqlite3.Error
        If an error occurs while marking the streak as complete
    """

    with connect_db(db_name) as con:

        if not _is_in_db(name, db_name):
            return f"{name} not in database"
        
        try:
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if date:
                timestamp = date if isinstance(date, str) else date.strftime("%Y-%m-%d %H:%M:%S")

            cur = con.cursor()
            cur.execute(
                """ INSERT INTO tracking (name, status, current_period, timestamp) 
                VALUES (?, ?, ?, ?)
                """, 
                (name, "streak complete", period, timestamp)
            )
            con.commit()
            return f"{name} streak completed"

        except sqlite3.Error as e:
            con.rollback()
            raise


def get_active(db_name: str = "main.db") -> list:

    """Function getting active habits from the database
    
    This function checks if a connection to a database is given
    and creates one if not. It then returns a list of active habits.

    Parameters
    ----------
    db_name : str, optional
        Name of the database file. Default is "main.db"

    Returns
    -------
    list
        A list of active habits

    Raises
    ------
    sqlite3.Error
        If an error occurs while getting active habits from the database
    """
    with connect_db(db_name) as con: 
        
        try:
            cur = con.cursor()
            result = cur.execute(
                """SELECT name 
                FROM habits 
                WHERE active = ? ;
                """,
                (1,))
            return [row[0] for row in result.fetchall()]

        except sqlite3.Error as e:
            raise


def get_inactive(db_name: str = "main.db") -> list:

    """Function getting inactive habits from the database
    
    This function checks if a connection to a database is given
    and creates one if not. It then returns a list of inactive habits.
    
    Parameters
    ----------
    db_name : str, optional
        Name of the database file. Default is "main.db"
    
    Returns
    -------
    list   
        A list of inactive habits

    Raises
    ------
    sqlite3.Error
        If an error occurs while getting inactive habits from the database
    """
    with connect_db(db_name) as con:
        try:
            cur = con.cursor()
            result = cur.execute(
                """SELECT name 
                FROM habits 
                WHERE active = ? ;
                """,
                (0,))
            return [row[0] for row in result.fetchall()]

        except sqlite3.Error as e:
            raise e

       
def get_habit_data(
    name: str = None,
    db_name: str = "main.db"
) -> pd.DataFrame:
    
    """Retrieves habit data from the database.

    Parameters
    ----------
    name : str, optional
        The name of the habit to retrieve (default: None, meaning retrieve all habits).

    db_name : str, optional
        The database file where the habits are stored (default: "main.db").

    Returns
    -------
    pd.DataFrame
        A DataFrame containing habit data. If a specific habit is requested and not found, returns an empty DataFrame.

    Raises
    ------
    sqlite3.Error
        If an error occurs while retrieving habits.
    """

    with connect_db(db_name) as con:
        try:
            cur = con.cursor()

            if name:
                result = cur.execute(
                    """SELECT * 
                    FROM habits 
                    WHERE name = ? ;
                    """,
                    (name, ))
                fetched_result = result.fetchone()

                if fetched_result is None:
                    return pd.DataFrame(columns=[
                        "name", 
                        "description", 
                        "period", 
                        "active"
                        ]
                    )
                col_names = [description[0] for description in cur.description]
                return pd.DataFrame([fetched_result], columns=col_names)
            
            result = cur.execute(
                """SELECT * 
                FROM habits ;
                """)
            col_names = [description[0] for description in cur.description]
            return pd.DataFrame(result.fetchall(), columns=col_names)

        except sqlite3.Error as e:
            return pd.DataFrame(columns=[
                "name", 
                "description", 
                "period", 
                "active"
                ]
            )