"""Small hand-authored case for unit tests. Not benchmark data and not a model result."""


def demo_case():
    """One rule change and one control whose document names that rule."""
    return {
        "change_id": "DEMO-ADDRESS",
        "change_ticket": {
            "title": "Structured address validation update",
            "text": "Update structured address validation rule.",
            "changed_entity_ids": ["R-ADDRESS"],
        },
        "visible_metadata": {
            "nodes": [
                {
                    "id": "R-ADDRESS",
                    "name": "Structured address validation rule",
                    "type": "RULE",
                },
                {
                    "id": "C-ADDRESS",
                    "name": "Address validation control",
                    "type": "CONTROL",
                    "criticality": "KEY",
                },
            ],
            "edges": [],
        },
        "control_documents": [
            {
                "control_id": "C-ADDRESS",
                "title": "Address validation",
                "text": "The address validation control depends directly on the structured address validation rule.",
            }
        ],
    }
