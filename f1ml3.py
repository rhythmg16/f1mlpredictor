import os
import pandas as pd
import fastf1
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

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
    combined.to_csv('F1_Training_Data.csv', index=False) #saves the hopefully final csv
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

teams = pd.read_csv("F1_Training_Data.csv")

teams.select_dtypes(include=['number']).corr()["Points"] #looking at the correlation

teams[teams.isnull().any(axis=1)] #checking if there any rows with missing values

sns.lmplot(x="PreviousPoints", y="Points", data=teams, fit_reg=True, ci=None)
sns.lmplot(x="SeasonRank", y="Points", data=teams, fit_reg=True, ci=None)
teams.plot.hist(y="Points")

teams['SeasonRankInverted'] = 1/teams['SeasonRank'] #making it a positive instead of negative relationship

train = teams[teams["Season"] < 2024].copy() #splits for training the data
test = teams[teams["Season"] >= 2024].copy() #splits for testing the data

reg = LinearRegression() #enables to train and make predictions using a linear model

predictors = ["SeasonRankInverted", "PreviousPoints"] #using these two columns to predict the points
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
testing = test[test["TeamName"] == "Mercedes"]
print(testing)