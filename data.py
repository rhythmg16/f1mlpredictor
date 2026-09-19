import os

import fastf1
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)
fastf1.Cache.enable_cache(CACHE_DIR)


def get_standings(year):
    all_results = []
    schedule = fastf1.get_event_schedule(year)
    races = schedule[schedule["EventFormat"] != "testing"]

    for _, race in races.iterrows():
        for session_type in ["R", "S"]:
            try:
                session = fastf1.get_session(year, race["RoundNumber"], session_type)
                session.load(laps=False, telemetry=False)
                results = session.results[["Abbreviation", "FullName", "TeamName", "Points"]].copy()
                results["RaceName"] = race["EventName"]
                all_results.append(results)
                print(f"Loaded: {race['EventName']} {session_type} {year}")
            except Exception as e:
                print(f"Skipping {race['EventName']} {session_type} {year}: {e}")

    if all_results:
        final_df = pd.concat(all_results, ignore_index=True)
        standings = final_df.groupby(["Abbreviation", "TeamName"])["Points"].sum().reset_index()
        fullnames = final_df.groupby("Abbreviation")["FullName"].agg(lambda x: x.mode()[0]).reset_index()
        standings = standings.merge(fullnames, on="Abbreviation", how="left")
        standings = standings.sort_values("Points", ascending=False).reset_index(drop=True)
        standings["SeasonRank"] = standings.index + 1
        return standings
    return None


def build_training_data(years):
    all_standings = []
    for year in years:
        standings = get_standings(year)
        if standings is not None:
            standings["Season"] = year
            all_standings.append(standings)

    combined = pd.concat(all_standings, ignore_index=True)
    combined = combined.sort_values(["Abbreviation", "Season"])
    combined["PreviousPoints"] = combined.groupby("Abbreviation")["Points"].shift(1)
    combined = combined.dropna(subset=["PreviousPoints"]).reset_index(drop=True)
    combined.to_csv(os.path.join(BASE_DIR, "F1_Training_Data.csv"), index=False)
    print("Done! F1_Training_Data.csv saved.")
    return combined


def season_csv(year):
    all_laps = []
    schedule = fastf1.get_event_schedule(year)
    races = schedule[schedule["EventFormat"] != "testing"]

    for _, race in races.iterrows():
        try:
            session = fastf1.get_session(year, race["RoundNumber"], "R")
            session.load(laps=False, telemetry=False)
            results = session.results[["DriverNumber", "Abbreviation", "FullName", "Position", "Time", "Points"]].copy()
            results["RaceName"] = race["EventName"]
            results["Round"] = race["RoundNumber"]
            all_laps.append(results)
            print(f"Loaded: {race['EventName']}")
        except Exception as e:
            print(f"Skipping {race['EventName']}: {e}")

    if all_laps:
        final_df = pd.concat(all_laps, ignore_index=True)
        final_df.to_csv(os.path.join(BASE_DIR, f"F1_{year}_Full_Season_Laps.csv"), index=False)
        print("Done! File saved.")


def get_midseason_standings(year, up_to_race):
    all_results = []
    schedule = fastf1.get_event_schedule(year)
    races = schedule[schedule["EventFormat"] != "testing"]
    races = races[races["RoundNumber"] <= up_to_race]

    for _, race in races.iterrows():
        try:
            session = fastf1.get_session(year, race["RoundNumber"], "R")
            session.load(laps=False, telemetry=False)
            results = session.results[["Abbreviation", "FullName", "TeamName", "Points"]].copy()
            all_results.append(results)
            print(f"Loaded: {race['EventName']} {year}")
        except Exception as e:
            print(f"Skipping {race['EventName']} {year}: {e}")

    if all_results:
        final_df = pd.concat(all_results, ignore_index=True)
        standings = final_df.groupby(["Abbreviation", "FullName", "TeamName"]).agg(
            points_so_far=("Points", "sum"),
            races_completed=("Points", "count")
        ).reset_index()
        standings["avg_points_per_race"] = standings["points_so_far"] / standings["races_completed"]
        standings = standings.sort_values("points_so_far", ascending=False).reset_index(drop=True)
        standings["current_rank"] = standings.index + 1
        standings["Season"] = year
        return standings
    return None


def build_midseason_training_data(years, up_to_race):
    all_data = []
    for year in years:
        midseason = get_midseason_standings(year, up_to_race)
        if midseason is None:
            continue

        final = get_standings(year)
        if final is None:
            continue

        prev = get_standings(year - 1)
        if prev is None:
            continue

        final = final[["Abbreviation", "Points"]].rename(columns={"Points": "FinalPoints"})
        prev = prev[["Abbreviation", "Points"]].rename(columns={"Points": "PreviousPoints"})
        merged = midseason.merge(final, on="Abbreviation", how="inner")
        merged = merged.merge(prev, on="Abbreviation", how="inner")
        all_data.append(merged)

    combined = pd.concat(all_data, ignore_index=True)
    combined.to_csv(os.path.join(BASE_DIR, f"F1_Midseason_Training_Data_race{up_to_race}.csv"), index=False)
    print("Done! Training Data saved.")
    return combined


def get_season_progress(year):
    """Return the latest completed race and next race from the live calendar."""
    schedule = fastf1.get_event_schedule(year)
    races = schedule[schedule["EventFormat"] != "testing"].copy()
    if races.empty:
        return {
            "year": year,
            "latest_completed_race": 0,
            "latest_completed_name": None,
            "next_race": None,
            "next_race_name": None,
            "next_race_date": None,
            "total_races": 0,
        }

    now = pd.Timestamp.now(tz="UTC")
    race_times = pd.to_datetime(races["Session5DateUtc"], utc=True)
    completed = races[race_times <= now]
    upcoming = races[race_times > now]

    latest_completed_race = int(completed["RoundNumber"].max()) if not completed.empty else 0
    latest_completed_name = (
        completed.sort_values("RoundNumber").iloc[-1]["EventName"]
        if not completed.empty
        else None
    )
    next_race = int(upcoming["RoundNumber"].min()) if not upcoming.empty else None
    next_row = upcoming.sort_values("RoundNumber").iloc[0] if not upcoming.empty else None

    return {
        "year": year,
        "latest_completed_race": latest_completed_race,
        "latest_completed_name": latest_completed_name,
        "next_race": next_race,
        "next_race_name": None if next_row is None else next_row["EventName"],
        "next_race_date": None if next_row is None else str(pd.to_datetime(next_row["Session5DateUtc"], utc=True)),
        "total_races": int(races["RoundNumber"].max()),
    }


def get_latest_completed_race(year):
    progress = get_season_progress(year)
    return max(1, progress["latest_completed_race"])


def get_training_data_path(up_to_race):
    return os.path.join(BASE_DIR, f"F1_Midseason_Training_Data_race{up_to_race}.csv")


def _find_nearest_training_path(up_to_race):
    matches = []
    for name in os.listdir(BASE_DIR):
        if not name.startswith("F1_Midseason_Training_Data_race") or not name.endswith(".csv"):
            continue
        try:
            race_num = int(name.replace("F1_Midseason_Training_Data_race", "").replace(".csv", ""))
        except ValueError:
            continue
        matches.append((abs(race_num - up_to_race), race_num, os.path.join(BASE_DIR, name)))

    if not matches:
        return None
    matches.sort()
    return matches[0][2]


def ensure_training_data(up_to_race, years=(2021, 2022, 2023, 2024, 2025)):
    path = get_training_data_path(up_to_race)
    if os.path.exists(path):
        return path

    nearest = _find_nearest_training_path(up_to_race)
    if nearest is not None:
        # Reuse the closest existing mid-season training cut so the site
        # can keep up with new races without a full multi-year rebuild.
        return nearest

    build_midseason_training_data(list(years), up_to_race)
    return path


def get_2026_midseason_path(up_to_race):
    return os.path.join(BASE_DIR, f"F1_2026_Midseason_race{up_to_race}.csv")


def ensure_2026_midseason_data(up_to_race, force=False):
    path = get_2026_midseason_path(up_to_race)
    if force or not os.path.exists(path):
        standings = get_midseason_standings(2026, up_to_race)
        if standings is None:
            raise FileNotFoundError(
                f"No mid-season results available yet for 2026 through race {up_to_race}."
            )
        standings.to_csv(path, index=False)
    return path


def get_previous_standings_path(year):
    return os.path.join(BASE_DIR, f"F1_{year}_Standings.csv")


def ensure_previous_standings_data(year):
    path = get_previous_standings_path(year)
    if not os.path.exists(path):
        standings = get_standings(year)
        if standings is not None:
            standings.to_csv(path, index=False)
    return path
