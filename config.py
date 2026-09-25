import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")

    MENUCI_URL = os.getenv(
        "MENUCI_URL",
        "https://menuci.ir"
    )

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:////opt/app-root/src/data/app.db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False