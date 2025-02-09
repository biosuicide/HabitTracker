# Habit Tracking app
This app will track your habits. You can do it in your normal browser

## Install:

clone the repo using: 
```

```

or simply donload it to a direction of your choice

at first startup a virtual environment will be created and all dependencies will be installed there 

## Using the App

- execute ```start_habittracker.py``` in your terminal
- after all dependencies are installed your standard browser automatically will open the app
- on first startup you can choose to import some test datasets by clicking the button **Add Test Data**
- you have 3 tabs where you can manage your habits:

### Your active habits
Create, modify and delete your habits.
This tab is divided into 2 parts, habits you have to complete and already completed habits. 

### Analyse your habits
Here you can display your active habits in comparison. Choose a period, to see all habits, which share the same routine period. This will display, how long your longest streak series for a habit is. Also a visual representation of the streak series is shown for the given period.

### Inactive habits
If you choose to inactivate a habit it will be displayed there. All inactive habits are excluded from analysis. 

## Testing
A pytest script is provided. Just activate the venv in your terminal and execute ```pytest```
