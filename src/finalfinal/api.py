"""FinalFinal™ — The Enterprise-Grade™ File Versioning Solution Nobody Asked For.

This module provides a robust, scalable, and completely unnecessary file naming
management system. It solves the age-old problem of "report_final_FINAL_v2_ok_def.docx"
by replacing it with "report_final_FINAL_v2_ok_def_this-one_validated_100%_last.docx".

Progress.

Example:
    Basic usage for the uninitiated::

        from finalfinal import track, increment, reset, to_pdf

        # Begin the cycle of suffering
        path = track("my_presentation.pptx")

        # Work in progress (allegedly)
        path = increment(path, increment_type=IncrementType.WIP)

        # It's definitely done this time
        path = increment(path, increment_type=IncrementType.FINAL, certainty_level=2)

        # It was not done
        path = increment(path, increment_type=IncrementType.RETAKE)

        # Archive the evidence and start fresh
        path = reset(path)

        # Generate a PDF that explains nothing
        to_pdf(path)
"""

import argparse
import re
import shutil
from datetime import datetime
from enum import Enum
from pathlib import Path
from random import choice, random, randint
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


class WhatAreYouTringToDoError(Exception):
    """Raised when the user attempts something FinalFinal™ finds philosophically objectionable."""


TRACKING_SUFFIXES: list[str] = [
    "to do",
    "waiting",
    "start",
    "v1",
    "fresh",
    "v0",
    "init",
    "new",
    "brand new",
    "initial draft",
    "first iteration",
    "kickoff",
    "baseline",
    "origin",
    "alpha",
    "ground zero",
    "genesis",
    "draft",
    "raw",
    "untouched",
    "unscathed",
]

FINAL_SUFFIXES: list[str] = [
    "final",
    "def",
    "definitive",
    "last one",
    "last",
    "ultimate",
    "all done",
    "this one",
    "validated",
    "client validated",
    "validated by supervisor",
    "for real",
    "do not touch",
    "shipped",
    "delivered",
    "signed off",
    "stamped and approved",
    "carved in stone",
    "FINAL",
    "the one",
    "fin",
    "use this",
    "farewell",
    "for posterity",
    "def2",
    "defgood",
    "defgood2",
]

WIP_SUFFIXES: list[str] = [
    "doing stuff",
    "wip",
    "updated",
    "work",
    "working",
    "in progress",
    "ongoing",
    "bis",
    "iterating",
    "touch-ups",
    "tweaks",
    "micro-adjustments",
    "minor edits",
    "polish",
    "refined",
    "chaos",
    "mess",
    "not ready",
    "do not look",
    "needs love",
    "touched",
]

RETAKE_SUFFIXES: list[str] = [
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
    "client feedback",
    "stakeholder input",
    "direction change",
    "scope creep",
    "updated brief",
    "revised brief",
    "my fault",
    "their fault",
    "monday morning version",
    "post-meeting",
    "after the call",
    "dont even ask",
    "yikes",
    "lol",
    "lmao",
]

FIX_SUFFIXES: list[str] = [
    "done",
    "ok",
    "fixed",
    "settled",
    "resolved",
    "patched",
    "addressed",
    "corrected",
    "remediated",
    "sorted",
    "handled",
    "closed",
    "better",
    "improved",
    "cleaner",
    "tighter",
    "crisper",
    "sharper",
    "nicer",
    "good now",
    "actually good",
    "decent",
    "not terrible",
    "passable",
    "yolo",
    "to scale",
    "with yellow layer",
    "with cyan layer",
    "with magenta layer",
    "with black layer",
    "with red layer",
    "with green layer",
    "with blue layer",
    "with alpha layer",
    "with linked media",
    "with fonts",
    "without watermark",
    "with bigger logo",
    "cat input cleaned",
]

DONE_SUFFIXES: list[str] = [
    "done",
    "ok",
    "ready",
    "yes",
    "approved",
    "to deliver",
    "for review",
    "delivery",
    "ready to go",
    "good",
    "decent",
    "awaiting validation",
    "ship it",
    "for client",
    "for producer",
    "for boss",
    "for stakeholders",
    "pending approval",
    "submitted",
    "in review",
    "not my problem anymore",
    "their problem now",
    "launching",
    "ready to print",
    "to prepress",
]

WEAK_CERTITUDE_MARKERS: list[str] = [
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
    "mostly",
    "sort of",
    "kind of",
    "technically",
    "loosely speaking",
    "arguably",
    "debatably",
    "let's say",
    "supposedly",
    "allegedly",
    "fingers crossed",
    "theoretically",
]

STRONG_CERTITUDE_MARKERS: list[str] = [
    "sure",
    "100%",
    "definitely",
    "certainly",
    "undeniably",
    "without doubt",
    "undoublebly",
    "absolutely",
    "positively",
    "guaranteed",
    "beyond doubt",
    "10000%",
]

RESTART_SUFFIXES: list[str] = [
    "redo",
    "start over",
    "restart",
    "milestone",
    "clean",
    "new start",
    "fresh start",
    "new2",
    "after backup",
    "reboot",
    "reset",
    "take two",
    "second attempt",
    "third time lucky",
    "this time for sure",
    "clean slate",
    "new leaf",
    "phoenix",
    "post-disaster",
    "after the incident",
    "lessons learned",
    "with wisdom",
    "humbled",
    "enlightened",
    "matured",
    "square one",
    "post-feedback",
    "post-therapy",
    "renewed",
    "reborn",
    "v2 from scratch",
    "rebuild",
    "refactor",
]

CHANGELOG_SENTENCES: list[str] = [
    "Someone did something.",
    "The file was modified in some way.",
    "God knows what happened on {dt}, but a new version of the file was saved.",
    "At {dt}, an unspecified change was made by an unspecified individual for unspecified reasons.",
    "A human being interacted with this file on {dt}. Motivation: unknown.",
    "Something was altered. Details are scarce. This is intentional.",
    "The file grew. No one knows by how much. No one asked.",
    "Edits were performed. Whether they were improvements is a matter of perspective.",
    "On {dt}, the file was opened, stared at, and then saved. Progress.",
    "Version increment detected.",
    "A spontaneous modification event occurred at approximately {dt}.",
    "The file was touched.",
    "Changes were made. At this stage, we choose to believe they were necessary.",
    "At {dt}, someone clicked Save. We'll count that as work.",
    "The file evolved.",
    "This version exists because someone, somewhere, was not satisfied with the previous one.",
    "A new version was born into this world at {dt}, screaming and unnamed.",
    "The file was improved, allegedly, at {dt}.",
    "An act of creation — or destruction — took place at {dt}. Records are unclear.",
    "The binary gods smiled upon this file at {dt} and decreed: it shall be different.",
    "Undocumented changes were made by an undocumented person in an undocumented manner.",
    "At {dt}, a brave soul made a modification and did not write a commit message.",
    "The contents of this file shifted, as does our confidence in the project overall.",
    "Version history note: see other versions for context.",
]

SEPARATORS: list[str] = ["-", "_", " "]
SUFFIX_SEPARATORS: list[str] = ["-", "_", " ", ""]


class IncrementType(str, Enum):
    """The taxonomy of despair, formalized.

    Each member represents a distinct emotional and professional state
    in the lifecycle of a file that should probably be under git.

    Attributes:
        WIP: Work In Progress. Or Work In Paralysis. Tomato, tomato.
        RETAKE: Something went wrong. Again. It's fine. It's fine.
        FIX: A specific error has been addressed. Others remain. Unacknowledged.
        DONE: The file is done. (It is not done.)
        FINAL: The file is final. (See: DONE.)
    """

    WIP = "wip"
    RETAKE = "retake"
    FIX = "fix"
    DONE = "done"
    FINAL = "final"


_SUFFIX_MAP: dict[IncrementType, list[str]] = {
    IncrementType.WIP: WIP_SUFFIXES,
    IncrementType.RETAKE: RETAKE_SUFFIXES,
    IncrementType.FIX: FIX_SUFFIXES,
    IncrementType.DONE: DONE_SUFFIXES,
    IncrementType.FINAL: FINAL_SUFFIXES,
}


def _upper(word: str) -> str:
    """Transforms a word into SCREAMING CASE. For emphasis. Or panic."""
    return word.upper()


def _lower(word: str) -> str:
    """Transforms a word into Sentence case. Professional. Approachable. Forgettable."""
    return word.capitalize()


def _title(word: str) -> str:
    """Transforms A Word Into Title Case. Very Important. Very Serious."""
    return word.title()


def _camel_case(word: str) -> str:
    """Transforms a word intoCamelCase. For developers who got lost on their way to git."""
    word = word.title()
    return word[:1].lower() + word[1:]


_CASING_CALLBACKS = [_upper, _lower, _title, _camel_case]
"""The four horsemen of inconsistent typography."""


def random_separator() -> str:
    """Returns a randomly selected separator character.

    Ensures that no two versions of the same filename look quite the same,
    which is the entire point of this enterprise.

    Returns:
        A separator string from ``SEPARATORS`` (``"-"``, ``"_"``, or ``" "``).
    """
    return choice(SEPARATORS)


def randomize_casing(word: str) -> str:
    """Applies a randomly selected casing transformation to a word.

    The transformation is selected from upper, capitalize, title, and camelCase.
    The result is unpredictable. This is a feature, not a bug.

    Args:
        word: The input string, in whatever casing it currently suffers under.

    Returns:
        The word, in a new and unexpected casing. Yay.
    """
    return choice(_CASING_CALLBACKS)(word)


def randomize_separators(word: str) -> str:
    """Replaces spaces in a word with a randomly chosen separator (or nothing).

    For multi-word suffixes like "brand new" or "oopsie daisy", this function
    ensures they emerge with maximum visual clarity.

    Args:
        word: A potentially multi-word string containing spaces.

    Returns:
        The word with spaces replaced by a random entry from ``SUFFIX_SEPARATORS``.
    """
    return word.replace(" ", choice(SUFFIX_SEPARATORS))


def random_word(word_list: list[str]) -> str:
    """Picks a random word from a list and applies randomized casing and separators.

    The randomization is non-negotiable. Do not attempt to predict it.
    Do not attempt to control it. Simply accept the output and move on.

    Args:
        word_list: A non-empty list of candidate suffix strings.

    Returns:
        A randomly selected, case-mangled, separator-scrambled suffix.
    """
    word = choice(word_list)
    word = randomize_casing(word)
    word = randomize_separators(word)
    return word


def _normalize(text: str) -> str:
    """Normalizes a string for deduplication comparison.

    Strips all separators and converts to lowercase, because the file system
    doesn't care about your aesthetic choices and neither does this function.

    Args:
        text: A string. Duh.

    Returns:
        A lowercase, separator-free version of the input.
    """
    return re.sub(r"[-_ ]", "", text).lower()


def _suffix_already_present(path: Path, candidate: str) -> bool:
    """Checks whether a candidate suffix is already embedded in the filename.

    Performs a normalized, case-insensitive, separator-agnostic comparison,
    because the previous version of the file was called
    ``report-wip_WIP-Wip.docx`` and no one is laughing.

    Args:
        path: The ``Path`` object representing the current file.
        candidate: The proposed suffix to add, pre-separator but post-word.

    Returns:
        ``True`` if the suffix is already present (normalized); ``False`` otherwise.
    """
    normalized_stem = _normalize(path.stem)
    normalized_candidate = _normalize(candidate)
    return normalized_candidate in normalized_stem


def _pick_unique_suffix(word_list: list[str], path: Path) -> str:
    """Picks a suffix that does not already appear in the filename.

    Shuffles through the word list until it finds one that isn't already
    baked into the path. If all suffixes are already present — congratulations,
    your filename is longer than most legal documents.

    Args:
        word_list: The pool of candidate suffix strings to draw from.
        path: The current ``Path``, used for duplicate detection.

    Returns:
        A suffix string that is (probably) not already in the filename.

    Raises:
        WhatAreYouTringToDoError: If every single suffix in the list has
            already been used. You have achieved something. We're not sure what.
    """
    shuffled = list(word_list)
    tried: list[str] = []
    for _ in range(
        len(shuffled) * 3
    ):  # generous attempts, because hope springs eternal
        candidate_raw = choice(shuffled)
        candidate_cased = randomize_casing(candidate_raw)
        candidate_sep = randomize_separators(candidate_cased)
        if not _suffix_already_present(path, candidate_raw):
            return candidate_sep
        tried.append(candidate_raw)

    raise WhatAreYouTringToDoError(
        f"Every suffix in this category already appears in '{path.name}'. "
        "Your filename is a monument to indecision. Consider starting over. "
        "FinalFinal™ has a reset() function for exactly this kind of situation."
    )


def get_metadata_file(path: Path | str) -> Path:
    """Returns the path to the FinalFinal™ metadata file for a given tracked file.

    The metadata file is a sacred artifact named ``important_notes_DONT_DELETE.docx``
    (it is not a real docx), stored in the same directory as the tracked file.
    Deleting it is the leading cause of WhatAreYouTringToDoError in the workplace.

    Args:
        path: The ``Path`` (or path-like string) of the tracked file.

    Returns:
        The ``Path`` to the corresponding metadata file.
    """
    path = Path(path)
    return path.with_name("important_notes_DONT_DELETE.docx")


def _get_suffix_string(separator: str, word: str) -> str:
    """Concatenates a separator and a word into a suffix fragment.

    If the separator is empty, the word is capitalized for visual distinction.
    This is the one place in FinalFinal™ where something intentional happens.

    Args:
        separator: A separator character from ``SEPARATORS``.
        word: The already-cased, already-separated suffix word.

    Returns:
        The combined separator + word string ready for appending.
    """
    if not separator:
        return word.capitalize()
    return separator + word


def add_suffix(path: Path, word_list: list[str]) -> Path:
    """Appends a randomly chosen, deduplicated suffix to a file path.

    Combines a random separator with a word drawn from ``word_list``,
    verified not to already appear in the filename.

    Args:
        path: The ``Path`` to which the suffix should be appended.
        word_list: The pool of candidate suffix strings.

    Returns:
        A new ``Path`` with the suffix appended before the file extension.
    """
    separator = random_separator()
    word = _pick_unique_suffix(word_list, path)
    suffix_str = _get_suffix_string(separator, word)
    name = path.stem + suffix_str + path.suffix
    return path.with_name(name)


def is_tracked(path: Path) -> bool:
    """Checks whether a file is currently being tracked by FinalFinal™.

    Detection is performed by checking for the presence of the metadata file.
    If the metadata file has been deleted, FinalFinal™ will pretend the file
    never existed. This is called "deniability."
    Do not ask for a more robust system: we already wrote DONT_DELETE in upper
    case, YOU are responsible if the versioning framework breaks.

    Args:
        path: The ``Path`` to check for tracked status.

    Returns:
        ``True`` if the metadata file exists; ``False`` if it was deleted
        (or never existed).
    """
    return get_metadata_file(path).exists()


def track(path: Path | str) -> Path:
    """Begins tracking a file with FinalFinal™. Godspeed.

    Creates a copy of the file with a randomized tracking suffix and records
    the original filename in the metadata file. The original file is left
    untouched, because FinalFinal™ respects boundaries.

    Args:
        path: The ``Path`` (or path-like string) of the file to track.
            Must exist on disk. FinalFinal™ cannot track hypothetical files.

    Returns:
        The ``Path`` to the newly created, suffix-adorned copy of the file.

    Raises:
        WhatAreYouTringToDoError: If the file does not exist, or if it is
            already being tracked. You had one job.
    """
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
    """Retrieves the most recent version of a tracked file.

    "Most recent" is defined as the file whose name is the longest,
    because each iteration appends a suffix, and length is the closest
    thing to version history this system has.

    Args:
        path: Any ``Path`` in the tracked file's directory. It need not be
            the latest version; FinalFinal™ will find it regardless.

    Returns:
        The ``Path`` to the longest-named file matching the original stem
        and extension. Presumably the most recent. Hopefully.

    Raises:
        WhatAreYouTringToDoError: If the metadata file is missing
            (see: ``is_tracked``), or if no matching files can be found
    """
    metadata_path = get_metadata_file(path)
    if not metadata_path.exists():
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
    if not files:
        raise WhatAreYouTringToDoError(
            f'No file with prefix "{original_file.stem}" could not be found'
        )
    return files[-1]


def get_incremented_path(
    path: Path | str,
    increment_type: IncrementType = IncrementType.WIP,
    custom_suffix: Optional[str] = None,
    certainty_level: int = 1,
) -> Path:
    """Computes the new path a file would receive upon incrementation, without moving anything.

    This is the purely theoretical arm of the operation. It calculates destiny
    without committing to it — much like your project manager during sprint planning.

    The suffix pool is selected by ``increment_type``, then optionally prefixed
    with a certitude marker depending on ``certainty_level``:

    - ``certainty_level < 1``: Weak certitude (e.g., "roughly final", "sort of done")
    - ``certainty_level == 1``: No certitude marker (blissful neutrality)
    - ``certainty_level > 1``: Strong certitude (e.g., "100% final", "bank on it done")

    For ``IncrementType.WIP``, there is additionally a 37.569% chance the last digit
    of the stem is incremented instead of appending a word suffix. We believe it is
    smarter than just naming your file "wip-wip-wip".

    Args:
        path: The ``Path`` (or path-like string) from which to compute the new path.
            The latest version will be located automatically.
        increment_type: The type of increment to perform. Defaults to ``IncrementType.WIP``
            because statistically, that is where you are.
        custom_suffix: An optional override suffix. If provided, all certitude and
            type logic is bypassed. You get exactly what you asked for. You probably
            shouldn't have asked for it.
        certainty_level: An integer expressing how sure you are. Values below 1
            express doubt. Values above 1 express overconfidence. Both are delusional
            in their own way. Defaults to ``1`` (affecting neutrality).

    Returns:
        A ``Path`` representing what the file would be renamed to.
        Nothing on disk is changed. This is merely a premonition.
    """
    path = Path(path)
    path = get_latest(path)

    if custom_suffix:
        return add_suffix(path, [custom_suffix])

    word_list = list(_SUFFIX_MAP[increment_type])
    if certainty_level < 1:
        certainty_word = choice(WEAK_CERTITUDE_MARKERS)
        word_list = [f"{certainty_word} {w}" for w in word_list]
    elif certainty_level > 1:
        if randint(0, 1000000) == 1:
            certainty_word = choice([])
        else:
            certainty_word = choice(STRONG_CERTITUDE_MARKERS)
        word_list = [f"{certainty_word} {w}" for w in word_list]

    if increment_type == IncrementType.WIP and random() < 0.37569:
        stem = path.stem
        if stem[-1].isdigit() and certainty_level == 1:
            path = path.with_stem(stem[:-1] + str(int(stem[-1]) + 1))
        else:
            path = path.with_stem(stem + "2")
        return path

    return add_suffix(path, word_list)


def increment(
    path: Path | str,
    increment_type: IncrementType = IncrementType.WIP,
    certainty_level: int = 1,
    custom_suffix: Optional[str] = None,
    overwrite: bool = True,
) -> Path:
    """Renames (or copies) the latest version of a tracked file with a new suffix.

    This is the primary action of FinalFinal™. Each call represents one step
    further into the filename. Each step is, statistically, not the last.

    Args:
        path: The ``Path`` (or path-like string) to any version of the tracked file.
            The latest version will be located and operated upon.
        increment_type: The emotional register of the new suffix. Defaults to
            ``IncrementType.WIP``, which is where we all are, always.
        certainty_level: How confident you are that this version matters.
            Accepts any integer. Only three ranges are meaningful:
            below 1 (uncertain), 1 (neutral), above 1 (dangerously confident).
        custom_suffix: An escape hatch for those who wish to bypass the carefully
            curated suffix pools and write their own destiny. Literally.
        overwrite: If ``True`` (default), the current latest file is renamed.
            If ``False``, a copy is made and the original is preserved.
            Set to ``False`` if you are the kind of person who keeps both.
            You know who you are.

    Returns:
        The ``Path`` of the newly named (or newly created) file version.
    """
    path = Path(path)
    path = get_latest(path)
    new_path = get_incremented_path(
        path,
        increment_type=increment_type,
        certainty_level=certainty_level,
        custom_suffix=custom_suffix,
    )
    if overwrite:
        path.rename(new_path)
    else:
        shutil.copy(path, new_path)
    return new_path


def reset(path: Path | str, backup_folder_name: str = "OLD") -> Path:
    """Archives all versioned files into a backup folder and starts fresh.

    When the filename has grown to a length that violates several international
    conventions, it is time to reset. This function moves all files matching
    the original stem into a subfolder (``OLD`` by default, or whatever you'd
    like to call the archive of your failures), then creates a new clean file
    using one of the RESTART_SUFFIXES.

    The metadata file is preserved. It has seen too much to be discarded.

    Args:
        path: The ``Path`` (or path-like string) of any version of the tracked file.
            All matching versions will be located and relocated.
        backup_folder_name: The name of the subfolder into which the old versions
            will be moved. Defaults to ``"OLD"``. ``"BEFORE_THE_INCIDENT"`` is
            also acceptable, and encouraged.

    Returns:
        The ``Path`` of the newly created clean file with a fresh restart suffix.

    Raises:
        WhatAreYouTringToDoError: If the file is not tracked (how did you get here?),
            or if no matching files are found (where did they go?).
    """
    path = Path(path).resolve()
    metadata_path = get_metadata_file(path)

    if not metadata_path.exists():
        raise WhatAreYouTringToDoError(
            f"The file {path.name} is not tracked by FinalFinal™. "
            "FinalFinal™ cannot reset what it never held."
        )

    original_file = Path(metadata_path.read_text())
    parent = path.parent

    # Collect all version files (not the metadata)
    version_files = [
        f
        for f in parent.iterdir()
        if f.is_file()
        and f.name.startswith(original_file.stem)
        and f.suffix == original_file.suffix
        and f != metadata_path
    ]

    if not version_files:
        raise WhatAreYouTringToDoError(
            f'No files with prefix "{original_file.stem}" were found. '
            "Perhaps they were never real. Perhaps you were never real."
        )

    # Create backup folder
    backup_dir = parent / backup_folder_name
    backup_dir.mkdir(exist_ok=True)

    # Move all old versions into backup
    for f in version_files:
        shutil.move(str(f), backup_dir / f.name)

    # Create a fresh file with a restart suffix
    latest_backup = sorted(
        [backup_dir / f.name for f in version_files], key=lambda x: len(x.name)
    )[-1]
    new_path = add_suffix(parent / original_file.name, RESTART_SUFFIXES)
    shutil.copy(backup_dir / latest_backup.name, new_path)

    return new_path


def prune(path: Path) -> Path:
    """Removes old, backup, and clearly redundant versions of a tracked file.

    This function is a placeholder: as it will permanently damage files on your
    computer and servers, we take extra care to make it as safe as possible.
    It will be implemented it the final version of the python package.

    Args:
        path: The ``Path`` to the tracked file whose older versions should be pruned.

    Returns:
        The ``Path`` to the surviving file. Presumably.
    """
    ...


def to_pdf(path: Path | str, pdf_path: Path | str | None = None) -> Path:
    """Generates a PDF changelog from all versions of a tracked file.

    Iterates over all files matching the original tracked stem, sorted by
    filename length (a reasonable proxy for chronological order, given that
    this system does not use timestamps, git, or common sense). For each file,
    retrieves the filesystem modification time and pairs it with a randomly
    selected changelog sentence, because actual commit messages were not
    provided. Commit Messages were an actual feature of FinalFinal™, in its
    initial version, but we decided to drop it, because typing a few words
    made the user experience too clunky.

    The resulting PDF is named after the original file with a ``_changelog``
    suffix, and is saved in the same directory. It may be emailed to a producer,
    who may or may not read it. This is out of the scope of FinalFinal™.

    Args:
        path: The ``Path`` (or path-like string) of any version of the tracked file.
        pdf_path: The ``Path`` (or path-like string) to the output pdf file.

    Returns:
        The ``Path`` to the generated PDF changelog.

    Raises:
        WhatAreYouTringToDoError: If the file is not tracked, or if no matching
            versions can be found.
    """
    path = Path(path).resolve()
    pdf_path = Path(pdf_path).resolve() if pdf_path else None
    metadata_path = get_metadata_file(path)

    if not metadata_path.exists():
        raise WhatAreYouTringToDoError(
            f"The file {path.name} is not tracked by FinalFinal™. "
            "There is no history to document. There is no history at all, really."
        )

    original_file = Path(metadata_path.read_text())
    parent = path.parent

    # Gather all version files and sort by name length (our proxy for chronology)
    version_files = sorted(
        [
            f
            for f in parent.iterdir()
            if f.is_file()
            and f.name.startswith(original_file.stem)
            and f.suffix == original_file.suffix
        ],
        key=lambda x: len(x.name),
    )

    if not version_files:
        raise WhatAreYouTringToDoError(
            "No version files were found. The history is empty. "
            "Much like this project's documentation."
        )

    # Build changelog entries
    entries: list[tuple[str, str]] = []
    for f in version_files:
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        dt_str = mtime.strftime("%Y-%m-%d at %H:%M:%S")
        sentence_template = choice(CHANGELOG_SENTENCES)
        sentence = sentence_template.format(dt=dt_str)
        entries.append((f.name, sentence))

    # Generate PDF
    if not pdf_path:
        pdf_path = parent / f"{original_file.stem}_changelog.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("FinalFinal&#8482; Changelog", styles["Title"]))
    story.append(Paragraph(f"File: {original_file.name}", styles["Heading2"]))
    story.append(
        Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.5 * cm))
    story.append(
        Paragraph(
            "The following represents the complete audit trail of this file. "
            "It should not be used in a court of law.",
            styles["Italic"],
        )
    )
    story.append(Spacer(1, 0.8 * cm))

    # Entries
    for i, (filename, sentence) in enumerate(entries, start=1):
        story.append(Paragraph(f"<b>Version {i}:</b> {filename}", styles["Heading3"]))
        story.append(Paragraph(sentence, styles["Normal"]))
        story.append(Spacer(1, 0.4 * cm))

    doc.build(story)
    return pdf_path


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", required=True, type=Path)
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument("-t", "--track", action="store_true")
    action_group.add_argument("-i", "--increment", action="store_true")
    action_group.add_argument("-pdf", "--export_pdf", action="store_true")
    action_group.add_argument("-r", "--reset", action="store_true")
    parser.add_argument("-pf", "--pdf_file", required=False, type=Path)
    parser.add_argument(
        "-it", "--increment_type", type=IncrementType, default=IncrementType.WIP
    )
    parser.add_argument("-cl", "--certainty_level", required=False, type=int, default=1)
    parser.add_argument("-cs", "--custom_suffix", required=False, type=str)
    parser.add_argument("-ow", "--overwrite", action="store_true")
    args = parser.parse_args()

    if args.track:
        track(args.path)
    if args.increment:
        increment(
            args.path,
            increment_type=args.increment_type,
            certainty_level=args.certainty_level,
            overwrite=args.overwrite,
            custom_suffix=args.custom_suffix,
        )
    if args.export_pdf:
        to_pdf(args.path, args.pdf_file)
    if args.reset:
        reset(path=args.path)


if __name__ == "__main__":
    _parse_args()
