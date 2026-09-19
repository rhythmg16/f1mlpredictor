"""Run the Python model and write static/predictions.json for Vercel."""

import json
import os

from model import get_prediction_summary

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(BASE_DIR, "static", "predictions.json")


def build_payload(year=2026, refresh=False):
    summary = get_prediction_summary(year=year, refresh=refresh)
    drivers = summary["predicted_drivers"].copy()
    constructors = summary["predicted_constructors"].copy()

    drivers["predicted_points"] = drivers["predicted_points"].round(1)
    constructors["predicted_points"] = constructors["predicted_points"].round(1)

    return {
        "year": year,
        "up_to_race": summary["up_to_race"],
        "auto": True,
        "season": summary["season"],
        "mae": round(float(summary["mae"]), 2),
        "predictors": [
            "points_so_far",
            "avg_points_per_race",
            "current_rank",
            "PreviousPoints",
        ],
        "drivers": drivers.to_dict(orient="records"),
        "constructors": constructors.to_dict(orient="records"),
        "champion": {
            "driver": drivers.iloc[0].to_dict() if len(drivers) else None,
            "constructor": constructors.iloc[0].to_dict() if len(constructors) else None,
        },
    }


def main():
    payload = build_payload(year=2026, refresh=False)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote {OUT_PATH}")
    print(f"Through race {payload['up_to_race']} · MAE {payload['mae']}")


if __name__ == "__main__":
    main()
