"""workflow — versioned route/form definitions + rules DSL (Phase 2).

Definitions move Draft → Approved → Effective (plan decision 6). The rules DSL
(``rules.py``) uses the Interpreter pattern. No router yet.
"""

from mes_core.workflow.rules import evaluate, parse  # noqa: F401
