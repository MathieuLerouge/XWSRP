def yellow(text: str) -> str:
    """Return text formatted in color #ffab40 (orange-yellow) using 24-bit ANSI codes."""
    return f"\033[38;2;255;171;64m{text}\033[0m"


def blue(text: str) -> str:
    """Return text formatted in color #4285f4 (blue) using 24-bit ANSI codes."""
    return f"\033[38;2;66;133;244m{text}\033[0m"


def gray(text: str) -> str:
    """Return text formatted in color #767676 (gray) using 24-bit ANSI codes."""
    return f"\033[38;2;118;118;118m{text}\033[0m"


def green(text: str) -> str:
    """Return text formatted in color #34a853 (green) using 24-bit ANSI codes."""
    return f"\033[38;2;52;168;83m{text}\033[0m"


def red(text: str) -> str:
    """Return text formatted in color #ea4335 (red) using 24-bit ANSI codes."""
    return f"\033[38;2;234;67;53m{text}\033[0m"


def bold(text: str) -> str:
    """Return text formatted in bold using ANSI codes."""
    return f"\033[1m{text}\033[0m"
