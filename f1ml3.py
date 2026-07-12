import os
import pandas as pd
import fastf1
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cache_dir = os.path.join(BASE_DIR, "cache")

cache_dir = os.path.expanduser("~/Desktop/personal_projects/f1mlpredictor/cache")
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)
fastf1.Cache.enable_cache(cache_dir) #setting up the local folder where fasf1 can save the race data

def get_standings(year):
    all_results = []
    schedule = fastf1.get_event_schedule(year)
    races = schedule[schedule['EventFormat'] != 'testing']
    for i, race in races.iterrows(): #loops through each race
        try:
            session = fastf1.get_session(year, race['RoundNumber'], 'R')
            session.load(laps=False, telemetry=False)
            results = session.results[['Abbreviation', 'FullName', 'TeamName', 'Points']].copy() #now including team name for constructors championship
            results['RaceName'] = race['EventName'] #adds column RaceName with the name of the event
            all_results.append(results) #add everything to the array
            print(f"Loaded: {race['EventName']} {year}")
        except Exception as e:
            print(f"Skipping {race['EventName']} {year}: {e}")
    if all_results:
        final_df = pd.concat(all_results, ignore_index=True)
        standings = final_df.groupby(['Abbreviation', 'FullName', 'TeamName'])['Points'].sum().reset_index()
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
        final_df.to_csv(f'F1_{year}_Full_Season_Laps.csv', index=False) #puts it in a file in the same folder so we can use it
        print("Done! File saved.") #so earlier the problem was that it wasn't saving in a file, just kind of loading it

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(BASE_DIR, "F1_Training_Data.csv")
teams = pd.read_csv(csv_path)
teams.select_dtypes(include=['number']).corr()["Points"] #looking at the correlation

teams[teams.isnull().any(axis=1)] #checking if there any rows with missing values

sns.lmplot(x="PreviousPoints", y="Points", data=teams, fit_reg=True, ci=None)
sns.lmplot(x="SeasonRank", y="Points", data=teams, fit_reg=True, ci=None)
teams.plot.hist(y="Points")

teams['SeasonRankInverted'] = 1/teams['SeasonRank'] #making it a positive instead of negative relationship

train = teams[teams["Season"] < 2024].copy() #splits for training the data
test = teams[teams["Season"] >= 2024].copy() #splits for testing the data

reg = LinearRegression() #enables to train and make predictions using a linear model

predictors = ["SeasonRankInverted", "PreviousPoints", ] #using these two columns to predict the points
target = "Points"

reg.fit(train[predictors], train[target]) # so now the algorithm will be trained on the training data set

predictions = reg.predict(test[predictors])
test["predictions"] = predictions #the predictions don't come out to whole numbers
test.loc[test["predictions"] < 0, "predictions"] = 0 #if a prediction is less than 0, then its turned into a 0
test["predictions"] = test["predictions"].round() # rounds all predictions
print(test)

from sklearn.metrics import mean_absolute_error
error = mean_absolute_error(test["Points"], test["predictions"])
print(error) # we were within 45 points of how many points a team actually won
print(teams.describe()["Points"]) #since 45 is below the standard deviation, this is a good error
# print(test[["Season", "FullName", "TeamName", "Points", "predictions"]].to_string(index=False))
errors = (test["Points"] - test["predictions"]).abs()
# print(errors)
error_by_team = errors.groupby(test["TeamName"]).mean() #grouping the teams
print(error_by_team)
points_by_team = test["Points"].groupby(test["TeamName"]).mean() #how many points each team earned on average
error_ratio = error_by_team / points_by_team
# print(error_ratio)
# print(error_ratio.sort_values())

error_by_driver = errors.groupby(test["Abbreviation"]).mean()
print(error_by_driver)
points_by_driver = test["Points"].groupby(test["Abbreviation"]).mean()
error_ratio_driver = error_by_driver / points_by_driver
import numpy as np
error_ratio_driver = error_ratio_driver[np.isfinite(error_ratio_driver)]
print(error_ratio_driver.sort_values())

#prediciting the drivers championship 2026
def predict_next_season(year):
    base = teams[teams["Season"] == year].copy() #takes all the data from year as the starting points for predictions
    base["Season"] = year + 1
    base["PreviousPoints"] = base["Points"]
    base["SeasonRankInverted"] = 1/ base["SeasonRank"] #sets the season to year+1, and shifts previous points to years points and
    #recalculating the season rank
    base["predicted_points"] = reg.predict(base[predictors])#gives the predictiosn to the linear regression model

    return base[[
        "Season", "Abbreviation", "FullName", "TeamName",
        "PreviousPoints", "SeasonRank", "predicted_points"
    ]]

pred_2026 = predict_next_season(2025)

pred_2026 = pred_2026.sort_values("predicted_points", ascending=False).reset_index(drop=True)
pred_2026["predicted_rank"] = pred_2026.index + 1 #sorting into predicted points highest to lowest

print(pred_2026.to_string(index=False))

top_driver = pred_2026.iloc[0] #first row is top driver
print(top_driver[["predicted_rank", "Abbreviation", "FullName", "TeamName", "predicted_points"]])

#predicting the constructors championship
constructors_2026 = (
    pred_2026.groupby("TeamName", as_index = False)["predicted_points"].sum() #grouping the drivers by teams and addign up predicted points
    .sort_values("predicted_points", ascending=False)
)
constructors_2026["predicted_rank"] = (
    constructors_2026["predicted_points"]#ranking them
    .rank(ascending=False, method="dense")
    .astype(int)
)

print(constructors_2026.to_string(index=False))

top_constructor = constructors_2026.iloc[0]#top team is the winner
print(top_constructor)

#Going to use better predictors, mainly the data we already have so all of the 
#races up until now

def get_midseason_standings(year, up_to_race):
    all_results = [] #empty list that will collect results race by race
    schedule = fastf1.get_event_schedule(year)
    races = schedule[schedule['EventFormat'] != 'testing'] #gets calender and filters out testing sessions
    races = races[races['RoundNumber'] <= up_to_race] #filters races up to the cutoff

    for i, race in races.itserrows():
        try:
            session = fastf1.get_session(year, race['RoundNumber'], "R")
            session.load(laps=False, telemetry = False)
            results = session.results[['Abbreviation', 'FullName', 'TeamName', "Points"]].copy()
            all_results.append(results)
            print(f"Loaded: {race['EventName']} {year}") #loops through each race, loads it, and gets the resutls and adds to the list
        except Exception as e:
            print(f"Skipping {race['EventName']} {year}: {e}")
    if all_results:
        final_df = pd.concat(all_results, ignore_index = True) #putting all resutls in a single dataframe
        standings = final_df.groupby(['Abbreviation', 'FullName', 'TeamName']). agg( #groups all the rows by driver and .agg calculates points so far for each driver and races completed
            points_so_far = ('Points', 'sum'),
            races_completed = ('Points', 'count')
        ).reset_index()
        standings['avg_points_per_race'] = standings['points_so_far'] / standings['races_completed'] #gets the average
        standings= standings.sort_values('points_so_far', ascending = False).reset_index(drop=True) #sorts points by highest to lowest, assinging rank
        standings['current_rank'] = standings.index + 1
        standings['Season'] = year
        return standings

    return None

#new training data function
def build_midseason_training_data(years, up_to_race):
    all_data = []
    for year in years: #get standings up until the cutoff race
        midseason = get_midseason_standings(year, up_to_race)
        if midseason is None:
            continue
        final = get_standings(year) #end of season standigns as the target
        if final is None:
            continue
        prev = get_standings(year - 1)#get previous season standings for PreviousPoints
        if prev is None:
            continue
        #renaming the final points column so i can tell them apart after merging
        final = final[['Abbreviation', 'Points']].rename(columns={'Points': 'FinalPoints'})
        prev = prev[['Abbreviation', 'Points']].rename(columns = {'Points': 'PreviousPoints'}) #renaming previous season points
        merged = midseason.merge(final, on='Abbreviation', how='inner') #merge everything on abbreviation
        merged = merged.merge(prev, on='Abbreviation', how = 'inner')
        all_data.append(merged)
    combined = pd.concat(all_data, ignore_index = True)
    combined.to_csv(f'F1_Midseason_Training_Data_race(up_to_race).csv', index=False)
    print("Done! Training Data saved.")
    return combined

