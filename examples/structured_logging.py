#!/usr/bin/env python

"""Structured logging with code location info."""

import journald_send


def process_data(user_id: str) -> None:
    journald_send.send_compliant(
        f'Đang xử lý dữ liệu cho người dùng {user_id}',
        (
            ('CODE_FILE', __file__.encode()),
            ('CODE_LINE', b'10'),
            ('CODE_FUNC', b'process_data'),
            ('USER_ID', user_id.encode()),
        ),
    )


process_data('9999')
