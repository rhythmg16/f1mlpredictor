import os
from flask import Flask, jsonify, request, send_from_directory

from data import get_season_progress
from model import get_prediction_summary

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="")


@app.get("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.get("/api/season")
def season():
    year = request.args.get("year", default=2026, type=int)
    try:
        return jsonify(get_season_progress(year))
    except Exception as exc:
        return jsonify({"error": f"Failed to load season calendar: {exc}"}), 500


@app.get("/api/predictions")
def predictions():
    year = request.args.get("year", default=2026, type=int)
    up_to_race = request.args.get("up_to_race", default=None, type=int)
    refresh = request.args.get("refresh", default="0") in {"1", "true", "True"}

    try:
        summary = get_prediction_summary(year=year, up_to_race=up_to_race, refresh=refresh)
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 404
    except Exception as exc:
        return jsonify({"error": f"Failed to generate predictions: {exc}"}), 500

    drivers = summary["predicted_drivers"].copy()
    constructors = summary["predicted_constructors"].copy()
    season_info = summary["season"]

    drivers["predicted_points"] = drivers["predicted_points"].round(1)
    constructors["predicted_points"] = constructors["predicted_points"].round(1)

    return jsonify(
        {
            "year": year,
            "up_to_race": summary["up_to_race"],
            "auto": up_to_race is None,
            "season": season_info,
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
    )


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
