# app/graph/nodes/error_node.py
"""
Error node — terminal node for malformed JD or unrecoverable failures.

Writes a structured error into state and sets pipeline_complete=True
so the caller gets a clean response rather than a KeyError on missing fields.
"""

