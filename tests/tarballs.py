"""A .tar.gz written member by member, for tests that unpack, verify or refuse one."""

import io
import tarfile
from collections.abc import Mapping
from pathlib import Path


def write_tarball(
    path: Path,
    files: Mapping[str, bytes],
    *,
    links: Mapping[str, str] | None = None,
) -> Path:
    """path, a gzipped tar of files (name: content) and symbolic links (name: target),
    each named exactly as given, unsafe names included."""
    with tarfile.open(path, "w:gz") as archive:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
        for name, target in (links or {}).items():
            info = tarfile.TarInfo(name)
            info.type, info.linkname = tarfile.SYMTYPE, target
            archive.addfile(info)
    return path
