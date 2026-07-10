import requests
import pandas as pd
import fastf1
from fastf1 import cache
cache_dir = "f1cache"
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)
fastf1.Cache.enable_cache('cache')
session = fastf1.get_session(2025, 'Australia', 'R')

print(session)






