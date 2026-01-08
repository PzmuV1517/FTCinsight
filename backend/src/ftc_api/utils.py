import os
import pickle
from typing import Any


def dump_cache(path: str, data: Any) -> None:
    """Save data to cache"""
    os.makedirs(os.path.dirname(path + "/data.p"), exist_ok=True)
    with open(path + "/data.p", "wb") as f:
        pickle.dump(data, f)


def load_cache(path: str) -> Any:
    """Load data from cache"""
    with open(path + "/data.p", "rb") as f:
        return pickle.load(f)
