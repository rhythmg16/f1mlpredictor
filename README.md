This is my first machine learning project and it is for Formula 1. This is based off https://www.youtube.com/watch?v=Hr06nSA-qww this machine learing project.
I am using linear regression for the model and using the Season Rank and previous points of a driver to predict how many points they will have in this 2026 season.
The error metric is absolute mean error and I am using pandas, seaborn, fastf1 api, and sklearn.
I was originally using Jupyter Notebook but switched to a .py file in vscode due to the files used being too large for Jupyter Notebook.

## Website

The predictions UI is a static HTML / CSS / JavaScript frontend served by Flask.

```bash
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000

- `/` — championship predictor site
- `/api/predictions?year=2026` — JSON predictions using the latest completed race automatically
- `/api/season?year=2026` — current/next race from the live calendar

The site reads the FastF1 schedule and always predicts from the most recent completed race, so you do not need to bump the race number by hand.
