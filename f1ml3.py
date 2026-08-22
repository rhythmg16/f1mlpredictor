import os
import pandas as pd
import fastf1
import seaborn as sns
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cache_dir = os.path.expanduser("~/Desktop/personal_projects/f1mlpredictor/cache")
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)
fastf1.Cache.enable_cache(cache_dir) #setting up the local folder where fastf1 can save the race data

def get_standings(year):
    all_results = []
    schedule = fastf1.get_event_schedule(year)
    races = schedule[schedule['EventFormat'] != 'testing']

    for i, race in races.iterrows(): #loops through each race
        for session_type in ['R', 'S']: #loads both race and sprint
            try:
                session = fastf1.get_session(year, race['RoundNumber'], session_type)
                session.load(laps=False, telemetry=False)
                results = session.results[['Abbreviation', 'FullName', 'TeamName', 'Points']].copy() #now including team name for constructors championship
                results['RaceName'] = race['EventName'] #adds column RaceName with the name of the event
                all_results.append(results) #add everything to the array
                print(f"Loaded: {race['EventName']} {session_type} {year}")
            except Exception as e:
                print(f"Skipping {race['EventName']} {session_type} {year}: {e}")

    if all_results:
        final_df = pd.concat(all_results, ignore_index=True)
        standings = final_df.groupby(['Abbreviation', 'TeamName'])['Points'].sum().reset_index()
        fullnames = final_df.groupby('Abbreviation')['FullName'].agg(lambda x: x.mode()[0]).reset_index()
        standings = standings.merge(fullnames, on='Abbreviation', how='left')
        standings = standings.sort_values('Points', ascending=False).reset_index(drop=True)
        standings['SeasonRank'] = standings.index + 1
        return standings
    return None

def build_training_data(years): #so still trying to create the best csv to train the model on for my purpose
    all_standings = [] #creates the array
    for year in years:
        standings = get_standings(year) #looping through the years and getting the positions
        if standings is not None:
            standings['Season'] = year
            all_standings.append(standings) #if it exists add it to the array
    combined = pd.concat(all_standings, ignore_index=True) #puts it all in one big dataframe
    combined = combined.sort_values(['Abbreviation', 'Season']) #sorts by driver and then season
    combined['PreviousPoints'] = combined.groupby('Abbreviation')['Points'].shift(1) #previous points from last year
    combined = combined.dropna(subset=['PreviousPoints']) #drops the first season
    combined = combined.reset_index(drop=True)
    combined.to_csv(os.path.join(BASE_DIR, 'F1_Training_Data.csv'), index=False)
    print("Done! F1_Training_Data.csv saved.")
    return combined

def season_csv(year):
    all_laps = [] #creates the array
    schedule = fastf1.get_event_schedule(year) #gets the schedule
    races = schedule[schedule['EventFormat'] != 'testing'] #doesn't include the testing rounds
    for i, race in races.iterrows(): #i am filtering what I want
        try: #so this is actually from the fastf1 api so it filters to only the most simple stats, just their ending time position etc
            session = fastf1.get_session(year, race['RoundNumber'], 'R')
            session.load(laps=False, telemetry=False)
            results = session.results[['DriverNumber', 'Abbreviation', 'FullName', 'Position', 'Time', 'Points']].copy()
            results['RaceName'] = race['EventName']
            results['Round'] = race['RoundNumber']
            all_laps.append(results)
            print(f"Loaded: {race['EventName']}")
        except Exception as e:
            print(f"Skipping {race['EventName']}: {e}")
    if all_laps:
        final_df = pd.concat(all_laps, ignore_index=True)
        final_df.to_csv(os.path.join(BASE_DIR, f'F1_{year}_Full_Season_Laps.csv'), index=False) #puts it in a file in the same folder so we can use it
        print("Done! File saved.") #so earlier the problem was that it wasn't saving in a file, just kind of loading it

def get_midseason_standings(year, up_to_race):
    all_results = [] #empty list that will collect results race by race
    schedule = fastf1.get_event_schedule(year)
    races = schedule[schedule['EventFormat'] != 'testing'] #gets calendar and filters out testing sessions
    races = races[races['RoundNumber'] <= up_to_race] #filters races up to the cutoff
    for i, race in races.iterrows():
        try:
            session = fastf1.get_session(year, race['RoundNumber'], 'R')
            session.load(laps=False, telemetry=False)
            results = session.results[['Abbreviation', 'FullName', 'TeamName', 'Points']].copy()
            all_results.append(results)
            print(f"Loaded: {race['EventName']} {year}") #loops through each race, loads it, and gets the results and adds to the list
        except Exception as e:
            print(f"Skipping {race['EventName']} {year}: {e}")
    if all_results:
        final_df = pd.concat(all_results, ignore_index=True) #putting all results in a single dataframe
        standings = final_df.groupby(['Abbreviation', 'FullName', 'TeamName']).agg( #groups all the rows by driver and .agg calculates points so far for each driver and races completed
            points_so_far=('Points', 'sum'),
            races_completed=('Points', 'count')
        ).reset_index()
        standings['avg_points_per_race'] = standings['points_so_far'] / standings['races_completed'] #gets the average
        standings = standings.sort_values('points_so_far', ascending=False).reset_index(drop=True) #sorts points by highest to lowest, assigning rank
        standings['current_rank'] = standings.index + 1
        standings['Season'] = year
        return standings
    return None

def build_midseason_training_data(years, up_to_race):
    all_data = []
    for year in years: #get standings up until the cutoff race
        midseason = get_midseason_standings(year, up_to_race)
        if midseason is None:
            continue
        final = get_standings(year) #end of season standings as the target
        if final is None:
            continue
        prev = get_standings(year - 1) #get previous season standings for PreviousPoints
        if prev is None:
            continue
        #renaming the final points column so i can tell them apart after merging
        final = final[['Abbreviation', 'Points']].rename(columns={'Points': 'FinalPoints'})
        prev = prev[['Abbreviation', 'Points']].rename(columns={'Points': 'PreviousPoints'}) #renaming previous season points
        merged = midseason.merge(final, on='Abbreviation', how='inner') #merge everything on abbreviation
        merged = merged.merge(prev, on='Abbreviation', how='inner')
        all_data.append(merged)
    combined = pd.concat(all_data, ignore_index=True)
    combined.to_csv(os.path.join(BASE_DIR, f'F1_Midseason_Training_Data_race{up_to_race}.csv'), index=False)
    print("Done! Training Data saved.")
    return combined

def predict_next_season(year, up_to_race):
    current_midseason_path = os.path.join(BASE_DIR, f'F1_{year}_Midseason_race{up_to_race}.csv')
    if not os.path.exists(current_midseason_path):
        get_midseason_standings(year, up_to_race).to_csv(current_midseason_path, index=False)

    base = pd.read_csv(current_midseason_path) #mid-season data up to the cutoff race
    prev = pd.read_csv(os.path.join(BASE_DIR, f'F1_{year - 1}_Standings.csv')) #full previous season final standings
    prev = prev[['Abbreviation', 'Points']].rename(columns={'Points': 'PreviousPoints'})
    base = base.merge(prev, on='Abbreviation', how='left')
    base['PreviousPoints'] = base['PreviousPoints'].fillna(0) #rookies with no previous season data get 0
    base = base.sort_values('points_so_far', ascending=False).drop_duplicates(subset='Abbreviation', keep='first')
    base['Season'] = year
    base['predicted_points'] = reg.predict(base[predictors]) #gives the predictions to the linear regression model
    return base[[
        'Season', 'Abbreviation', 'FullName', 'TeamName',
        'PreviousPoints', 'current_rank', 'predicted_points'
    ]]

up_to_race = 13  # change this to however many races have happened in 2026
# get_midseason_standings(2026, up_to_race).to_csv(os.path.join(BASE_DIR, f'F1_2026_Midseason_race{up_to_race}.csv'), index=False)
# get_standings(2025).to_csv(os.path.join(BASE_DIR, 'F1_2025_Standings.csv'), index=False)
training_data_path = os.path.join(BASE_DIR, f'F1_Midseason_Training_Data_race{up_to_race}.csv')
if not os.path.exists(training_data_path):
    build_midseason_training_data([2021, 2022, 2023, 2024, 2025], up_to_race)
training_data = pd.read_csv(training_data_path)

predictors = ['points_so_far', 'avg_points_per_race', 'current_rank', 'PreviousPoints']
target = 'FinalPoints'

train = training_data[training_data['Season'] < 2024].copy()
test = training_data[training_data['Season'] >= 2024].copy()

reg = LinearRegression() #using linear regression model
reg.fit(train[predictors], train[target])

test['Predictions'] = reg.predict(test[predictors])
test.loc[test['Predictions'] < 0, 'Predictions'] = 0#sets all negatives to 0 and rounds
test['Predictions'] = test['Predictions'].round()

mae = mean_absolute_error(test[target], test['Predictions'])
print(f"Mean Absolute Error: {mae:.2f} points")
print(test[["Abbreviation", "FullName", "Season", "FinalPoints", "Predictions"]]) #calculates how far off predictions were on average

errors = (test[target] - test['Predictions']).abs() #calculates raw errors for each driver
error_by_team = errors.groupby(test['TeamName']).mean() #grouping the teams
print(error_by_team)
points_by_team = test[target].groupby(test['TeamName']).mean() #how many points each team earned on average
error_ratio = error_by_team / points_by_team

error_by_driver = errors.groupby(test['Abbreviation']).mean() #grouping the drivers
print(error_by_driver)
points_by_driver = test[target].groupby(test['Abbreviation']).mean()
error_ratio_driver = error_by_driver / points_by_driver
error_ratio_driver = error_ratio_driver[np.isfinite(error_ratio_driver)]
print(error_ratio_driver.sort_values())#removes any infinite values and sorts

#predicting the drivers championship 2026
pred_2026 = predict_next_season(2026, up_to_race)
pred_2026 = pred_2026.sort_values('predicted_points', ascending=False).reset_index(drop=True)
pred_2026['predicted_rank'] = pred_2026.index + 1 #sorting into predicted points highest to lowest

print(pred_2026.to_string(index=False))

top_driver = pred_2026.iloc[0] #first row is top driver
print(top_driver[['predicted_rank', 'Abbreviation', 'FullName', 'TeamName', 'predicted_points']])

#predicting the constructors championship
constructors_2026 = (
    pred_2026.groupby('TeamName', as_index=False)['predicted_points'].sum() #grouping the drivers by teams and adding up predicted points
    .sort_values('predicted_points', ascending=False)
)
constructors_2026['predicted_rank'] = (
    constructors_2026['predicted_points'] #ranking them
    .rank(ascending=False, method='dense')
    .astype(int)
)

print(constructors_2026.to_string(index=False))

top_constructor = constructors_2026.iloc[0] #top team is the winner
print(top_constructor)
