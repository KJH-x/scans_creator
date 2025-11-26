from typing import Literal

Color = Literal["red", "green", "yellow", "blue", "magenta", "cyan", "white", "reset"]

COLOR_CODES: dict[Color, str] = {
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    "reset": "\033[0m",
}


def cprint(*args, color: Color = "reset", prefix: str = "", **kwargs) -> None:
    sep: str = kwargs.pop("sep", " ")
    text = sep.join(str(arg) for arg in args)
    if prefix:
        text = f"{prefix} {text}"
    colored_text = f"{COLOR_CODES.get(color, COLOR_CODES['reset'])}{text}{COLOR_CODES['reset']}"
    print(colored_text, **kwargs)


def cinput(prompt: str, color: Color = "reset") -> str:
    return input(f"{COLOR_CODES.get(color, COLOR_CODES['reset'])}{prompt}{COLOR_CODES['reset']} ")


class Logger:
    def debug(self, *args, **kwargs):
        cprint(*args, color="blue", prefix="[DEBUG]", **kwargs)

    def info(self, *args, **kwargs):
        cprint(*args, color="green", prefix="[INFO]", **kwargs)

    def warn(self, *args, **kwargs):
        cprint(*args, color="yellow", prefix="[WARN]", **kwargs)

    def error(self, *args, **kwargs):
        cprint(*args, color="red", prefix="[ERROR]", **kwargs)


log = Logger()
