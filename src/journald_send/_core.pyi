def send(
    message: str,
    priority: int | None = None,
    code_file: str | None = None,
    code_line: int | None = None,
    code_func: str | None = None,
    **kwargs: object,
) -> None: ...

_PRI_EMERGENCY: int
_PRI_ALERT: int
_PRI_CRITICAL: int
_PRI_ERROR: int
_PRI_WARNING: int
_PRI_NOTICE: int
_PRI_INFO: int
_PRI_DEBUG: int

_VERSION: str
