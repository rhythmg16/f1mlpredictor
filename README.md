This is my first machine learning project and it is for Formula 1. This is based off https://www.youtube.com/watch?v=Hr06nSA-qww this machine learing project.
I am using linear regression for the model and using the Season Rank and previous points of a driver to predict how many points they will have in this 2026 season.
The error metric is absolute mean error and I am using pandas, seaborn, fastf1 api, and sklearn.
I was originally using Jupyter Notebook but switched to a .py file in vscode due to the files used being too large for Jupyter Notebook.

## Website

The UI is HTML / CSS / JavaScript. Your **Python model is unchanged** — it still does all the predicting.

### Local (live model via Flask)

```bash
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

### Vercel (static hosting)

Vercel serves the frontend plus a precomputed `predictions.json` from your Python model:

```bash
python generate_predictions.py
```

Then commit/push `static/predictions.json` (and redeploy). On Vercel the site loads that file; locally Flask can still use the live `/api/predictions` endpoint.

- `/` — championship predictor site
- `/predictions.json` — latest model output (for Vercel)
- `/api/predictions?year=2026` — live predictions when running Flask locally
- `/api/season?year=2026` — current/next race from the live calendar

The model reads the FastF1 schedule and predicts from the most recent completed race when you generate or run Flask.
