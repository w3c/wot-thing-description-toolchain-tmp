"""Read the section prose files of the specification and expand their include markers."""

import re
from collections.abc import Callable, Mapping
from pathlib import Path

from ..errors import GenerationError

INTRO_SUFFIX = ".intro.html"
CONTENT_SUFFIX = ".html"

_MARKER = re.compile(r"%(\w+)\(([^)%]*)\)%")
_MARKER_ARGUMENT = re.compile(r"'([^']*)'")

type Include = Callable[..., str]


class SectionProse:
    """The prose files of one directory; every file must be read by the end of the spec build."""

    def __init__(self, directory: Path | None, markup: Callable[[str], str], includes: Mapping[str, Include]) -> None:
        self._markup = markup
        self._includes = includes
        self._unread = set(_files(directory)) if directory else set()

    def intro(self, class_name: str) -> str:
        """Return the prose shown before the vocabulary table of a class, or an empty string."""
        return self._read(class_name, INTRO_SUFFIX)

    def content(self, class_name: str) -> str:
        """Return the prose shown after the vocabulary table of a class, or an empty string."""
        return self._read(class_name, CONTENT_SUFFIX)

    def require_all_read(self) -> None:
        """Raise GenerationError for the files that no section of the specification used."""
        if self._unread:
            names = ", ".join(sorted(str(file) for file in self._unread))
            raise GenerationError(
                f"section prose is not used by any class section of the specification: {names}. "
                f"A file is named <Class>{CONTENT_SUFFIX} or <Class>{INTRO_SUFFIX} after a class shown in the spec."
            )

    def _read(self, class_name: str, suffix: str) -> str:
        file = next((file for file in self._unread if file.name == f"{class_name}{suffix}"), None)
        if file is None:
            return ""
        self._unread.remove(file)
        try:
            text = file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise GenerationError(f"{file}: section prose could not be read: {exc}") from exc
        # Only the newline that ends the file is dropped: a blank last line reaches the specification.
        return _MARKER.sub(lambda marker: self._include(file, marker), self._markup(text.removesuffix("\n")))

    def _include(self, file: Path, marker: re.Match[str]) -> str:
        name, arguments = marker.group(1), _MARKER_ARGUMENT.findall(marker.group(2))
        if name not in self._includes:
            known = ", ".join(sorted(self._includes))
            raise GenerationError(f"{file}: unknown include marker {marker.group(0)!r}; known markers: {known}")
        try:
            return self._includes[name](*arguments)
        except (TypeError, ValueError) as exc:
            raise GenerationError(f"{file}: include marker {marker.group(0)!r} is invalid: {exc}") from exc


def _files(directory: Path) -> list[Path]:
    try:
        # Finder and editors leave hidden files such as .DS_Store in the directory.
        return [file for file in directory.iterdir() if not file.name.startswith(".")]
    except OSError as exc:
        raise GenerationError(f"{directory}: section prose directory could not be read: {exc}") from exc
