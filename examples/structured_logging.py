"""Structured logging with code location info."""

import journald_send


def process_data(user_id: str) -> None:
    journald_send.send(
        f"Processing data for user {user_id}",
        code_file=__file__,
        code_line=10,
        code_func="process_data",
        USER_ID=user_id,
    )


process_data("12345")
