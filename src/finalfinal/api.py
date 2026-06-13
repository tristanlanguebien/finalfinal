import shutil
from pathlib import Path
from random import choice


class WhatAreYouTringToDoError(Exception): ...


TRACKING_SUFFIXES = [
    "to do",
    "waiting",
    "start",
    "v1",
    "fresh",
    "v0",
    "new",
    "brand new",
]
FINAL_SUFFIXES = [
    "final",
    "ok sure",
    "def",
    "definitive",
    "very last one",
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
WEAK_CERTITUDE_MARKERS = [
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
STRONG_CERTITUDE_MARKERS = [
    "sure",
    "100%",
    "definitely",
    "certainly",
    "undeniably",
    "without doubt",
    "undoublebly",
]
RESTART_SUFFIX = [
    "redo",
    "start over",
    "restart",
    "milestone",
    "clean",
    "new start",
    "fresh start",
    "new2",
    "after backup",
]

SEPARATORS = ["-", "_", " "]
SUFFIX_SEPARATORS = ["-", "_", " ", ""]


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
    return word.replace(" ", choice(SUFFIX_SEPARATORS))


def get_metadata_file(path: Path | str) -> Path:
    path = Path(path)
    return path.with_name("important_notes_DONT_DELETE.docx")


def get_suffix(word_list: list[str]) -> str:
    separator = random_separator()
    word = random_word(word_list)
    if not separator:
        word = word.capitalize()
    return separator + word


def add_suffix(path: Path, word_list: list[str]) -> Path:
    name = path.stem + get_suffix(word_list) + path.suffix
    return path.with_name(name)


def is_tracked(path: Path) -> bool:
    metadata_path = get_metadata_file(path)
    if not metadata_path.exists():
        return False
    return True


def track(path: Path | str) -> Path:
    path = Path(path).resolve()
    if not path.exists():
        raise WhatAreYouTringToDoError(
            "The file does not exist. How could FinalFinal™ possibly track it?"
        )

    original_path_name = path.name
    metadata_path = get_metadata_file(path)
    if is_tracked(path):
        raise WhatAreYouTringToDoError(
            f"File {path.name} is already tracked by FinalFinal™"
        )

    new_path = add_suffix(path, TRACKING_SUFFIXES)
    shutil.copy(path, new_path)

    if not metadata_path.exists():
        metadata_path.write_text(original_path_name)

    return new_path


def get_latest(path: Path) -> Path:
    metadata_path = get_metadata_file(path)
    if not metadata_path:
        raise WhatAreYouTringToDoError(
            f"The file {path.name} is not tracked by FinalFinal™"
        )
    original_file = Path(metadata_path.read_text())

    files = [
        file
        for file in path.parent.iterdir()
        if file.is_file()
        and file.name.startswith(original_file.stem)
        and file.suffix == original_file.suffix
    ]
    files.sort(key=lambda x: len(x.name))
    return files[-1]


def get_incremented_path(
    path: Path | str,
    increment_type: str = "wip",
    custom_suffix: str | None = None,
    certainty_level: int = 1,
) -> Path:
    path = Path(path)
    path = get_latest(path)

    # Custom suffix
    if custom_suffix:
        return add_suffix(path, [custom_suffix])

    # Add certitude suffif
    if certainty_level < 1:
        path = add_suffix(path, WEAK_CERTITUDE_MARKERS)
    elif certainty_level > 1:
        path = add_suffix(path, STRONG_CERTITUDE_MARKERS)

    # Add main suffix
    if increment_type == "wip":
        return add_suffix(path, WIP_SUFFIXES)
    if increment_type == "retake":
        return add_suffix(path, RETAKE_SUFFIXES)
    if increment_type == "done":
        return add_suffix(path, DONE_SUFFIXES)
    if increment_type == "final":
        return add_suffix(path, FINAL_SUFFIXES)

    return path


def increment(
    path: Path | str,
    increment_type="wip",
    certainty_level: int = 1,
    custom_suffix: str | None = None,
    overwrite=True,
) -> Path:
    path = Path(path)
    path = get_latest(path)
    new_path = get_incremented_path(
        path,
        increment_type=increment_type,
        certainty_level=certainty_level,
        custom_suffix=custom_suffix,
    )
    print(new_path)
    return new_path


def prune(path: Path) -> Path:
    ...
    # old, backup


def to_pdf(path: Path) -> Path: ...


if __name__ == "__main__":
    # track("./sandbox/test.txt")
    increment(r"D:\gitlab\finalfinal\sandbox\test.txt")
