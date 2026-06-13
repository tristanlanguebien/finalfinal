from pathlib import Path
from random import choice

TRACKING_SUFFIXES = ["to do", "waiting", "start", "v1", "fresh", "v0", "new"]
FINAL_SUFFIXES = [
    "final",
    "ok sure",
    "def",
    "definitive",
    "last",
    "ultimate",
    "all done",
    "this one",
    "validated",
    "client validated",
    "validated by supervisor",
]
WIP_SUFFIXES = ["doing stuff", "wip", "updated", "work", "working"]
RETAKE_SUFFIXES = [
    "retake",
    "error",
    "redo",
    "ugh",
    "sigh...",
    "whoops",
    "oopsie daisy",
    "mistake",
    "oversight",
    "wrong",
    "nope",
    "nah",
    "nevermind",
]
RETAKEDONE_SUFFIXES = ["done", "ok", "fixed", "settled"]
DONE_SUFFIXES = [
    "done",
    "ok",
    "ready",
    "yes",
    "approved",
    "to deliver",
    "for review",
    "review",
    "delivery",
    "ready to go",
    "good",
    "decent",
    "awaiting validation",
    "for client",
    "for producer",
    "for boss",
]
MODAL_MARKERS = [
    "almost",
    "nearly",
    "not quite",
    "about",
    "just about",
    "more or less",
    "roughly",
    "surely",
    "pretty much",
    "practically",
    "virtually",
    "next to",
    "close to",
    "not far from",
    "nigh on",
    "approximatively",
    "pretty well",
    "to all intents and purposes",
    "mostly",
]
CERTITUDE_MARKERS = ["sure", "important", "100%"]
RESTART_SUFFIX = [
    "redo",
    "start over",
    "restart",
    "milestone",
    "clean",
    "new start",
    "fresh start",
]

SEPARATORS = ["-", "_", " "]


def random_separator() -> str:
    return choice(SEPARATORS)


def random_word(word_list: list[str]) -> str:
    word = choice(word_list)
    word = randomize_casing(word)
    word = randomize_separators(word)
    return word


def upper(word: str) -> str:
    return word.upper()


def lower(word: str) -> str:
    return word.capitalize()


def title(word: str) -> str:
    return word.title()


def camel_case(word: str) -> str:
    word = word.title()
    return word[:1].lower() + word[1:]


def randomize_casing(word: str) -> str:
    callbacks = [upper, lower, title, camel_case]
    return choice(callbacks)(word)


def randomize_separators(word: str) -> str:
    return word.replace(" ", random_separator())


def get_metadata_file(path: Path | str) -> Path:
    path = Path(path)
    return path.with_name("important_notes_DONT_DELETE.docx")


def add_suffix(path: Path, word_list: list[str]) -> Path:
    name = path.stem + random_separator() + random_word(word_list) + path.suffix
    return path.with_name(name)


def is_tracked(path: Path) -> bool:
    metadata_path = get_metadata_file(path)
    if not metadata_path.exists():
        return False
    return True


def track(path: Path | str):
    path = Path(path).resolve()
    metadata_path = get_metadata_file(path)
    if is_tracked(path):
        print(f"File {path.name} is already tracked by FinalFinal™")
        return

    path = add_suffix(path, TRACKING_SUFFIXES)

    if not path.exists():
        path.parent.mkdir(exist_ok=True, parents=True)
        path.write_text("")

    if not metadata_path.exists():
        metadata_path.write_text(path.name)


def increment(
    path: Path,
    overwrite=True,
    is_final=False,
    custom_suffix: str | None = None,
    certainty_level: int = 1,
) -> Path:
    # bis
    ...


def prune(path: Path) -> Path:
    ...
    # old, backup


def to_pdf(path: Path) -> Path: ...


if __name__ == "__main__":
    track("./sandbox/test.txt")
