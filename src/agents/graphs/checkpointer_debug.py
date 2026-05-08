"""Temporary debug helpers — DO NOT MERGE."""
import json


def dump_state(state, path):
    """Quick-and-dirty state serializer for debugging."""
    with open(path, 'w') as f:
        json.dump(str(state), f, default=str)
