import os

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

from data import (
    BASE_DIR,
    ensure_previous_standings_data,
    ensure_training_data,
    ensure_2026_midseason_data,
)

PREDICTORS = ["points_so_far", "avg_points_per_race", "current_rank", "PreviousPoints"]
TARGET = "FinalPoints"


def train_model(training_data):
    train = training_data[training_data["Season"] < 2024].copy()
    test = training_data[training_data["Season"] >= 2024].copy()

    reg = LinearRegression()
    reg.fit(train[PREDICTORS], train[TARGET])

    test = test.copy()
    test["Predictions"] = reg.predict(test[PREDICTORS])
    test.loc[test["Predictions"] < 0, "Predictions"] = 0
    test["Predictions"] = test["Predictions"].round()

    mae = mean_absolute_error(test[TARGET], test["Predictions"])
    return reg, test, mae


def predict_next_season(year, up_to_race, reg):
    current_midseason_path = ensure_2026_midseason_data(up_to_race)
    prev_standings_path = ensure_previous_standings_data(year - 1)

    base = pd.read_csv(current_midseason_path)
    prev = pd.read_csv(prev_standings_path)
    prev = prev[["Abbreviation", "Points"]].rename(columns={"Points": "PreviousPoints"})

    base = base.merge(prev, on="Abbreviation", how="left")
    base["PreviousPoints"] = base["PreviousPoints"].fillna(0)
    base = base.sort_values("points_so_far", ascending=False).drop_duplicates(subset="Abbreviation", keep="first")
    base["Season"] = year
    base["predicted_points"] = reg.predict(base[PREDICTORS])

    return base[[
        "Season",
        "Abbreviation",
        "FullName",
        "TeamName",
        "PreviousPoints",
        "current_rank",
        "predicted_points",
    ]]


def get_prediction_summary(year=2026, up_to_race=13):
    training_path = ensure_training_data(up_to_race)
    training_data = pd.read_csv(training_path)

    reg, test, mae = train_model(training_data)
    pred_2026 = predict_next_season(year, up_to_race, reg)
    pred_2026 = pred_2026.sort_values("predicted_points", ascending=False).reset_index(drop=True)
    pred_2026["predicted_rank"] = pred_2026.index + 1

    constructors = (
        pred_2026.groupby("TeamName", as_index=False)["predicted_points"].sum()
        .sort_values("predicted_points", ascending=False)
        .reset_index(drop=True)
    )
    constructors["predicted_rank"] = constructors["predicted_points"].rank(ascending=False, method="dense").astype(int)

    summary = {
        "training_data": training_data,
        "test_data": test,
        "mae": mae,
        "predicted_drivers": pred_2026,
        "predicted_constructors": constructors,
    }
    return summary


if __name__ == "__main__":
    summary = get_prediction_summary(year=2026, up_to_race=13)
    print(f"Mean Absolute Error: {summary['mae']:.2f} points")
    print(summary["predicted_drivers"].head(10).to_string(index=False))
    print(summary["predicted_constructors"].head(10).to_string(index=False))
