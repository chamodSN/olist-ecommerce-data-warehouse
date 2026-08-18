import great_expectations as gx
from pathlib import Path

# This file lives in data_quality/expectations/, so parents[1] is data_quality/
PROJECT_ROOT_DIR = Path(__file__).resolve().parents[1]


def get_project_context():
    return gx.get_context(mode="file", project_root_dir=str(PROJECT_ROOT_DIR))
