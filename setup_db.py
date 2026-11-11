from database import Store
from settings import Settings

if __name__ == "__main__":
    Store(Settings.from_env().database_path).initialize()
    print("Waypoint database initialized.")
