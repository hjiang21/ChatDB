# app/llm/validate_sql.py
"""
Pre-execution validation for LLM-generated SQL.

This is a second, independent guardrail layer that sits between LLM1
(text -> SQL) and actual execution against the database. It does not
trust the prompt alone to constrain behavior -- it re-checks the
generated SQL's actual statement type, statement count, and referenced
tables before anything touches the database.
"""

import re
import sqlparse

# The only tables that exist in this schema. Anything else referenced
# in a generated query is treated as invalid rather than executed.
ALLOWED_TABLES = {"disease", "symptom", "disease_symptom", "patient"}

# Statement types allowed per endpoint "mode". /query is read-only,
# /modify is write-only -- neither should ever bleed into the other.
ALLOWED_TYPES = {
    "read": {"SELECT"},
    "write": {"INSERT", "UPDATE", "DELETE"},
}

# Regardless of mode, these are never acceptable coming out of this
# application -- there is no legitimate reason for LLM-generated SQL
# in this project to touch schema or permissions.
HARD_BLOCKED_KEYWORDS = {
    "DROP", "TRUNCATE", "ALTER", "GRANT", "REVOKE",
    "CREATE", "ATTACH", "DETACH", "REPLACE",
}


class SQLValidationError(Exception):
    """Raised when generated SQL fails a pre-execution guardrail check."""
    pass


_QUESTION_STARTERS = (
    "what", "who", "which", "when", "where", "why", "how",
    "is", "are", "was", "were", "does", "do", "did", "can", "could",
    "show me", "give me", "list", "tell me",
)


def looks_like_a_question(user_text: str) -> bool:
    """
    Cheap, deterministic (non-LLM) heuristic: does the raw user request
    look like a read/question rather than a write instruction? This runs
    BEFORE the LLM is called at all -- it does not depend on model
    compliance, and it costs nothing.

    This is intentionally conservative (a heuristic, not a classifier):
    it's meant to catch the obvious case cheaply, not to be the only
    line of defense. The NOT_A_WRITE_REQUEST sentinel handled elsewhere
    is the second, LLM-side layer for subtler cases this misses.
    """
    text = user_text.strip().lower()
    if not text:
        return False
    if text.endswith("?"):
        return True
    return any(text.startswith(starter) for starter in _QUESTION_STARTERS)


NOT_A_WRITE_REQUEST_SENTINEL = "NOT_A_WRITE_REQUEST"


def _extract_referenced_tables(sql: str) -> set:
    """
    Best-effort extraction of table names following FROM, JOIN, INTO,
    UPDATE, and DELETE FROM. This is intentionally simple (regex, not a
    full SQL parser) -- it's a defense-in-depth check on top of the
    statement-type check, not a substitute for it.
    """
    pattern = re.compile(
        r"\b(?:FROM|JOIN|INTO|UPDATE)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        re.IGNORECASE,
    )
    return {match.lower() for match in pattern.findall(sql)}


def validate_sql(sql: str, mode: str) -> None:
    """
    Validate a single generated SQL statement before execution.

    Raises SQLValidationError with a human-readable reason if the
    statement fails any guardrail check. Returns None (silently) if
    the statement passes.

    mode: "read" (for /query) or "write" (for /modify)
    """
    if mode not in ALLOWED_TYPES:
        raise SQLValidationError(f"Unknown validation mode: {mode!r}")

    if not sql or not sql.strip():
        raise SQLValidationError("Generated SQL was empty.")

    # 1) Reject hard-blocked keywords outright, regardless of mode.
    upper_sql = sql.upper()
    for keyword in HARD_BLOCKED_KEYWORDS:
        if re.search(rf"\b{keyword}\b", upper_sql):
            raise SQLValidationError(
                f"Generated SQL contains a disallowed operation: {keyword}."
            )

    # 2) Reject statement stacking (e.g. "SELECT ...; DROP TABLE ...").
    #    Only a single statement is ever expected from this pipeline.
    parsed = sqlparse.parse(sql)
    statements = [s for s in parsed if s.token_first(skip_cm=True) is not None]
    if len(statements) != 1:
        raise SQLValidationError(
            f"Expected exactly one SQL statement, found {len(statements)}."
        )

    statement = statements[0]
    stmt_type = statement.get_type()  # e.g. 'SELECT', 'INSERT', 'UNKNOWN'

    # 3) Check the statement type against what this endpoint allows.
    if stmt_type not in ALLOWED_TYPES[mode]:
        raise SQLValidationError(
            f"Statement type '{stmt_type}' is not allowed for mode '{mode}' "
            f"(allowed: {sorted(ALLOWED_TYPES[mode])})."
        )

    # 4) Check referenced tables against the known schema.
    referenced = _extract_referenced_tables(sql)
    unknown = referenced - ALLOWED_TABLES
    if unknown:
        raise SQLValidationError(
            f"Generated SQL references unknown table(s): {sorted(unknown)}."
        )