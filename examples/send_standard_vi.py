#!/usr/bin/env python

"""Sử dụng cơ bản của hàm send tiêu chuẩn."""

import journald_send
from journald_send import Priority


# Thông báo đơn giản với mức độ ưu tiên mặc định
journald_send.send('Xin chào, journald!')

# Thông báo với mức độ ưu tiên
journald_send.send('Đây là một cảnh báo', priority=Priority.WARNING)

# Thông báo với các trường tùy chỉnh
journald_send.send(
    'Người dùng đã đăng nhập',
    priority=Priority.INFO,
    USER_ID='12345',
    USERNAME='nguyen_van_a',
    SESSION_ID='abc123',
)

# Thông báo với vị trí mã nguồn
journald_send.send(
    'Đang xử lý dữ liệu',
    priority=Priority.DEBUG,
    code_file=__file__,
    code_line=26,
    code_func='main',
)
