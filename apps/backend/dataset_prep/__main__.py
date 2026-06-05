"""Allow running the package as: python -m dataset_prep"""
from .cli import run

if __name__ == "__main__":
    raise SystemExit(run())
