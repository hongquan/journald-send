#!/usr/bin/env python

"""Sử dụng hàm send_compliant với hỗ trợ khóa lặp lại."""

import journald_send
from journald_send import Priority


# Sử dụng cơ bản với các mục đơn
journald_send.send_compliant(
    'Xin chào, journald!',
    (('PRIORITY', str(Priority.INFO)),),
)

# Sử dụng khóa lặp lại (tính năng độc đáo của send_compliant)
# Điều này cho phép nhiều giá trị cho cùng một khóa
journald_send.send_compliant(
    'Hành động người dùng với nhiều thẻ',
    (
        ('PRIORITY', str(Priority.NOTICE)),
        ('USER_ID', b'12345'),
        ('TAG', 'đăng nhập'.encode()),
        ('TAG', 'thành công'.encode()),  # Khóa TAG lặp lại
        ('TAG', 'đã xác minh'.encode()),  # Khóa TAG lặp lại lần nữa
    ),
)

# Kết hợp giá trị chuỗi và bytes
journald_send.send_compliant(
    'Các loại giá trị hỗn hợp',
    (
        ('PRIORITY', '6'),  # Giá trị chuỗi
        ('CUSTOM_FIELD', b'bytes'),  # Giá trị bytes
        ('ANOTHER_FIELD', 'chuỗi'),  # Giá trị chuỗi (sẽ được mã hóa UTF-8)
    ),
)

# Với thông tin vị trí mã nguồn
journald_send.send_compliant(
    'Đang xử lý yêu cầu',
    (
        ('CODE_FILE', __file__.encode()),
        ('CODE_LINE', b'32'),
        ('CODE_FUNC', b'main'),
        ('REQUEST_ID', b'req-12345'),
    ),
)
