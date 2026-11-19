
from app.init_db import create_tables
from app.seed import seed_database


def initialize_database():
    create_tables()
    seed_database()
