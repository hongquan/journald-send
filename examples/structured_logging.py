#!/usr/bin/env python

"""Structured logging with code location info."""

import journald_send


def process_data(user_id: str) -> None:
    journald_send.send_compliant(
        f'Đang xử lý dữ liệu cho người dùng {user_id}',
        (
            ('CODE_FILE', __file__),
            ('CODE_LINE', '10'),
            ('CODE_FUNC', 'process_data'),
            ('USER_ID', user_id),
        ),
    )


process_data('9999')
