import os 
from datetime import datetime

accidents_dir = 'accidents'

def get_dates():
    if not os.path.exists("accidents"):
        return []
    
    dates = []
    for name in os.listdir(accidents_dir):
        path = os.path.join(accidents_dir, name)

        if not os.path.isdir(path):
            continue
        try:
            datetime.strptime(name, "%Y-%m-%d")
            dates.append(name)
        except ValueError:
            continue

    return sorted(dates, reverse=True)

