from typing import List, Any, Dict
# ──────────────────────────────────────────────────────────────────────────
# Helper: inflate SvelteKit’s __data.json structure
# -------------------------------------------------------------------------

import json
import sys

def unpack_data_array(data_array):
    """
    Given a SvelteKit 'data' array (mapping objects and payload values),
    returns a dict mapping field names to their values, handling nested objects and lists.
    """
    if not data_array or not isinstance(data_array[0], dict):
        raise ValueError("Unexpected format: first element must be a dict of field->index.")
    mapA = data_array[0]

    # Find all candidate mapping dicts (values are ints) excluding the first
    candidates = [item for item in data_array
                  if isinstance(item, dict)
                  and item is not mapA
                  and all(isinstance(v, int) for v in item.values())]
    if not candidates:
        raise ValueError("Could not find any mapping dicts in data array.")
    # Choose the largest mapping dict (the actual record schema)
    mapB = max(candidates, key=lambda d: len(d))

    field_to_index = {**mapA, **mapB}

    def get_value(idx):
        # Handle invalid or negative indexes
        if not isinstance(idx, int) or idx < 0 or idx >= len(data_array):
            return None
        val = data_array[idx]
        # Nested dict mapping
        if isinstance(val, dict) and all(isinstance(i, int) for i in val.values()):
            return {field: get_value(i) for field, i in val.items()}
        # List of indices
        if isinstance(val, list) and val and all(isinstance(i, int) for i in val):
            return [get_value(i) for i in val]
        return val

    return {field: get_value(idx) for field, idx in field_to_index.items()}


def unpack_svelte_payload(payload):
    """
    Extracts the first relevant 'data' node from a SvelteKit __data.json payload and unpacks it.

    Skips None, non-dict nodes, and metadata-only nodes (e.g., user session/profile data).
    """
    if payload.get("type") != "data" or "nodes" not in payload:
        raise ValueError("Not a valid SvelteKit __data.json payload.")

    for node in payload.get("nodes", []):
        # skip empty or non-dict entries
        if not isinstance(node, dict):
            continue
        if node.get("type") != "data" or not isinstance(node.get("data"), list):
            continue
        data_array = node["data"]
        # skip metadata-only arrays (e.g., user profile/session data)
        if data_array and isinstance(data_array[0], dict) and 'profile' in data_array[0]:
            continue
        # found a data node with actual record schema
        return unpack_data_array(data_array)

    raise ValueError("No unpackable data node found.")("Not a valid SvelteKit __data.json payload.")

    for node in payload.get("nodes", []):
        if not isinstance(node, dict):
            continue
        if node.get("type") == "data" and isinstance(node.get("data"), list):
            return unpack_data_array(node["data"])

    raise ValueError("No unpackable data node found.")

def fmt(val, fmt_str="{:.2f}"):
    return fmt_str.format(val) if val is not None else "—"