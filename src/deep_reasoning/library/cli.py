"""dr-library: the App backend (serve), and import and export for the user (§4.8)."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from deep_reasoning.library import texts
from deep_reasoning.library.records import LibraryError

EXIT_ERROR = 1
HOST = "127.0.0.1"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dr-library", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    serve = commands.add_parser("serve", help="the App backend, on 127.0.0.1:PORT")
    serve.add_argument("--port", type=int, required=True)
    serve.add_argument("--log-level", default="info")
    imported = commands.add_parser("import", help="merge a dr config into the library")
    imported.add_argument("path", type=Path)
    exported = commands.add_parser("export", help="write the library as a dr config")
    exported.add_argument("dir", type=Path)
    exported.add_argument("--namespace")
    exported.add_argument("--rev", type=int)
    for command in (serve, imported, exported):
        command.add_argument(
            "--home", type=Path, help="default $DR_HOME, else ~/.deep-reasoning"
        )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """dr-library serve | import | export (argparse; exit 0, 1 on LibraryError with its
    message on stderr, 2 on usage)."""
    args = _parser().parse_args(argv)
    from deep_reasoning.library.library import Library, library_path

    try:
        library = Library.open(library_path(args.home))
        if args.command == "serve":
            import uvicorn

            from deep_reasoning.library.api import create_app

            uvicorn.run(
                create_app(library),
                host=HOST,
                port=args.port,
                log_level=args.log_level.lower(),
            )
        elif args.command == "import":
            report = library.import_config(args.path)
            created = sum(change.created for change in report.changed)
            print(
                texts.nothing_imported(str(args.path))
                if report.rev is None
                else texts.imported(
                    str(args.path),
                    report.rev,
                    created,
                    len(report.changed) - created,
                    len(report.unchanged),
                )
            )
        else:
            state = library.state(rev=args.rev)
            library.materialize(args.dir, namespace=args.namespace, rev=state.rev)
            print(
                texts.exported(
                    str(args.dir / "main.yaml"),
                    len(state.namespaces),
                    len(state.decompositions),
                    len(state.tools),
                )
            )
    except LibraryError as exc:
        print(exc, file=sys.stderr)
        return EXIT_ERROR
    return 0
