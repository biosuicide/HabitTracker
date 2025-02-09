import streamlit as st

from habittracker import Habit
import db
import analysis

from datetime import datetime, timedelta

st.set_page_config(layout="wide")

# Create an instance of the database with tables 
# if not already created
db.create_tables()

st.title("Track your habits!")

# some motivation for a completed habit ;) 
if "show_balloons" in st.session_state and st.session_state["show_balloons"]:
    st.balloons()
    del st.session_state["show_balloons"] 

# define tabs
tab_active_habits, tab_analysis, tab_inactive = st.tabs(
    ["Your active Habits", 
     "Analyze your habits",
     "Inactive Habits"
    ]
)

# set dialog boxes for buttons
@st.dialog("Modify Habit")
def modify_button(habit):
    # preselect current period
    if habit.period == 'day':
        index_period = 0
    if habit.period == 'week':
        index_period = 1
    if habit.period == 'month':
        index_period = 2
    if habit.period == 'quarter':
        index_period = 3
    if habit.period == 'year':
        index_period = 4
    
    #preselect current satus
    if habit.active == True:
        index_status = 0
    else:
        index_status = 1

    # create dialogue box
    new_habit_name = st.text_input(
        label="Re-name your habit",
        value=habit.name)
    new_habit_description = st.text_input(
        label="A new Description of your habit",
        value=habit.description)
    new_habit_period = st.selectbox(
            label="Period",
            options = ("day", "week", "month", "quarter", "year"),
            index=index_period
        )
    new_status = st.selectbox(
        label ="New Status",
        options = ("active", "inactive"),
        index=index_status
    )
    if new_status == "active":
        new_status = True
    else:
        new_status = False

    #
    if st.button("Save Changes", 1):
        habit.modify(
            new_name = new_habit_name,
            description = new_habit_description,
            period = new_habit_period,
            active = new_status
        )
        st.rerun()

@st.dialog("Are you sure?")
def delete_button(habit):
    st.text("The habit will be deleted permanently!")
    if st.button("Delete Habit", 2):
        habit.delete()
        st.rerun()

@st.dialog("Fake Data")
def add_fake_data_button(habit):
    now = datetime.now()
    new_date = st.date_input(
            "New Date",
            now
    )

    dt = datetime.combine(new_date, datetime.min.time())    
    date = dt.replace(                    
        hour=12,
        minute=00,
        second=00
    )

    if st.button("Add fake data", 5):
        db.streak_complete(
            name = habit.name,
            period = habit.period,
            date = date
        )
        st.rerun()

@st.dialog("Create your new habit")
def Add_habit_button():
    habit_name = st.text_input("Name of the habit *")
    habit_description = st.text_input("Description of your habit")
    habit_period = st.selectbox(
        label = "Choose a period of completion",
        options = ("day", "week", "month", "quarter", "year")
        )
    if st.button("Create Habit", 3):
        if habit_name == "":
            st.text("Please enter a name")
        else:    
            result = db.add_habit(
                name = habit_name,
                period = habit_period,
                description = habit_description
            )
            if result == f"{habit_name} already in database":
                st.text(f"{habit_name} already exists")
            
            else:
                st.rerun()

# Test data, if db is empty
def add_test_data():
    now = datetime.now()
    test_habits = [
        ("Morning Exercise", "day", "A short morning workout routine"),
        ("Read a Book", "day", "Read at least 10 pages of a book"),
        ("Weekly Review", "week", "Reflect on the past week and plan ahead"),
        ("Grocery Shopping", "week", "Buy essential groceries"),
        ("Monthly Budgeting", "month", "Review and adjust monthly budget")
    ]
    day_breaks = [3,4,5,10,17,25,30]

    for name, period, description in test_habits:
        habit = Habit(name=name, period=period, description=description)
        if period == "day":
            for i in range(1,35): 
                date = now - timedelta(days=i)
                if i not in day_breaks:
                    db.streak_complete(
                        name = habit.name,
                        period = habit.period,
                        date = date
                    )
        
        elif period == "week":
            for i in range(1, 5):
                date = now - timedelta(weeks=i)
                if i != 3:
                    db.streak_complete(
                        name=habit.name,
                        period=habit.period,
                        date=date
                    )

        elif period == "month":
            for i in range(1, 6):
                date = now - timedelta(weeks=i * 4)
                db.streak_complete(
                    name=habit.name,
                    period=habit.period,
                    date=date
                )

    


# tab with all active habits
with tab_active_habits:
    active_habits = db.get_active()
    inactive_habits = db.get_inactive()
    st.subheader("Create your first habit")
    if st.button(label="Create Habit", key=4):
        Add_habit_button()
    if active_habits == [] and inactive_habits == []:
        if st.button("Add Test Data"):
            add_test_data()
            st.rerun()

        
    else:
        st.subheader("📌 Habits Not Completed This Period")

        # create an object for every active habit
        for habit_entry in active_habits:
            habit_name = habit_entry
            habit_data = db.get_habit_data(habit_name)
            habit = Habit(
                name = habit_data.iloc[0]["name"],
                description = habit_data.iloc[0]["description"],
                period = habit_data.iloc[0]["period"],
                active = habit_data.iloc[0]["active"]
            )

            habit.check_completion_status()
            if habit.streak_complete == False:
                with st.container(border=True):
                    col_1, col_2 = st.columns(2)

                    # col_1 contains information about the habit
                    with col_1:
                        st.header(body = habit.name, divider='blue')
                        st.subheader(habit.description) 
                        st.text(f"Period: {habit.period}")

                        # col_2 with current streak series and button
                        with col_2:
                            # if habit.get_current_streak() > 0:
                            #     st.markdown(f"Current Streak series: :green[{habit.get_current_streak()}]")
                            # else:
                            #     st.markdown(f"Current Streak series: :red[{habit.get_current_streak()}]")
                            if st.button("Mark completed", key=habit.name+"2"):
                                habit.mark_as_complete()
                                st.session_state["show_balloons"] = True
                                st.rerun()
                            if st.button("Modify Habit", key=habit.name):
                                modify_button(habit)
                            if st.button("Delete Habit", key=habit.name+"1"):
                                delete_button(habit)
                            
                            # uncomment, to activate cheating
                            # if st.button(label="Add Fake Data", key=habit.name+"3"):
                            #     add_fake_data_button(habit)


        st.subheader("✅ Habits Already Completed This Period")

        # create an object for every active habit
        for habit_entry in active_habits:
            habit_name = habit_entry
            habit_data = db.get_habit_data(habit_name)
            habit = Habit(
                name = habit_data.iloc[0]["name"],
                description = habit_data.iloc[0]["description"],
                period = habit_data.iloc[0]["period"],
                active = habit_data.iloc[0]["active"]
            )
            habit.check_completion_status()
            # show only the ones which are already completed
            if habit.streak_complete == True:

                # expander to save space, rest same as above 
                # w/o mark complete button
                with st.expander(label=habit.name):
                    longest_streak = analysis.get_habits_series(
                        name = habit, 
                        all_series = False,
                        period = habit.period
                    )
                    
                    col_1, col_2 = st.columns(2)
                    with col_1:
                        st.header(body = habit.name, divider='blue')
                        st.subheader(habit.description) 
                        st.text(f"Period: {habit.period}")
                    with col_2:
                        if habit.get_current_streak() > 0:
                            st.markdown(f"Current Streak series: :green[{habit.get_current_streak()}]")
                        else:
                            st.markdown(f"Current Streak series: :red[{habit.get_current_streak()}]")

                    # Buttons for habits
                        if st.button("Modify Habit", key=habit.name):
                            modify_button(habit)
                        if st.button("Delete Habit", key=habit.name+"1"):
                            delete_button(habit)

                        # uncomment, to activate cheating
                        # if st.button(label="Add Fake Data", key=habit.name+"3"):
                        #     add_fake_data_button(habit)                     

# tab for analysing habits
with tab_analysis:
    st.header("Habits per period")
    col_6, col_7, col_8, col_9 = st.columns(4)

    # selectbox to choose a period
    with col_6:
        select_period = st.selectbox(
            label = "Choose a period",
            options = ("all", "day", "week", "month", "quarter", "year"),
            key = "sel_period_analysis"
            )
        
    # add some headers
    with col_7:
        st.subheader("Habits")
        st.divider()
    with col_8:
        st.subheader("Current streak series")
        st.divider()
    with col_9:
        st.subheader("Longest streak series")
        st.divider()

    # select only the habits, which are active and 
    df_habits = analysis.get_active_habits_for_period(select_period)

    for habit in df_habits["name"].tolist():
        with col_7:
            st.text(habit)
            st.divider()
        with col_8:
            streaks = analysis.get_current_streak_series(habit)
            if streaks == []:
                st.text(0)
                st.divider()
            else:
                st.text(streaks)
                st.divider()  
        with col_9:
            longest_streak = analysis.get_habits_series(
                name = habit, 
                all_series = False,
                period = select_period
            )
            st.text(longest_streak.iloc[0]["streak_series"])
            st.divider()

    df_all_data = analysis.get_habits_series(
        all_series=True,
        period=select_period
    )

    # st.dataframe(df_all_data)
    # st.dataframe(db.get_tracking_data())

    if df_all_data.empty:
        st.text("No Habits for this period")
    else:
        st.bar_chart(
            data = df_all_data,
            x = "name",
            y_label = "Habit",
            stack = "normalize",
            color = ["#fd0000", "#05ae11"],
            horizontal = True
    )
        

with tab_inactive:
    inactive_habits = db.get_inactive()
    for habit_entry in inactive_habits:
            with st.container(border=True):
                col_1, col_2= st.columns(2)
                with col_1:
                    habit_name = habit_entry
                    habit_data = db.get_habit_data(habit_name)
                    habit = Habit(
                        name = habit_data.iloc[0]["name"],
                        description = habit_data.iloc[0]["description"],
                        period = habit_data.iloc[0]["period"],
                        active = habit_data.iloc[0]["active"]
                    )
                    longest_streak = analysis.get_habits_series(
                        name = habit_name, 
                        all_series = False,
                        period = habit.period
                    )
                    st.header(body = habit.name, divider='blue')
                    st.subheader(habit.description) 
                    st.text(f"Period: {habit.period}")
                with col_2:
                    if st.button("Modify Habit", key=habit.name):
                        modify_button(habit)
                    if st.button("Delete Habit", key=habit.name+"1"):
                        delete_button(habit)