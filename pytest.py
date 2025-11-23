"""Minimal pytest shim to run unittest-based test suites.

This lightweight module allows environments without the real pytest dependency
installed to still execute the project's unittest suite via ``python -m pytest``.
It intentionally supports only a subset of pytest's CLI flags that are commonly
used by automation (``-k``, ``-m``, ``-v``, ``-q``, ``-x``, ``--maxfail``).
All other flags are ignored.
"""
from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path
from typing import Iterable, List


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("paths", nargs="*", help="Test files or directories to run")
    parser.add_argument("-k", dest="keyword", default=None)
    parser.add_argument("-m", dest="marker", default=None)
    parser.add_argument("-q", "--quiet", action="store_true")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument("-x", "--exitfirst", action="store_true")
    parser.add_argument("--maxfail", type=int, default=None)
    parser.add_argument("--disable-warnings", action="store_true")
    return parser


def _discover_from_target(loader: unittest.TestLoader, target: str) -> unittest.TestSuite:
    path = Path(target)
    if path.is_dir():
        return loader.discover(str(path), pattern="test*.py")
    if path.is_file() and path.suffix == ".py":
        module_name = str(path.with_suffix("")).replace("/", ".").replace("\\", ".")
        return loader.loadTestsFromName(module_name)
    return loader.loadTestsFromName(target)


def _filter_by_keyword(suite: unittest.TestSuite, keyword: str) -> unittest.TestSuite:
    def matches(test_id: str) -> bool:
        return keyword in test_id

    filtered = unittest.TestSuite()
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            filtered.addTests(_filter_by_keyword(test, keyword))
        else:
            if matches(test.id()):
                filtered.addTest(test)
    return filtered


def main(argv: Iterable[str] | None = None) -> None:
    parser = _build_argument_parser()
    args, _ = parser.parse_known_args(argv)

    targets: List[str] = list(args.paths) if args.paths else ["tests"]
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for target in targets:
        suite.addTests(_discover_from_target(loader, target))

    if args.keyword:
        suite = _filter_by_keyword(suite, args.keyword)

    verbosity = 0 if args.quiet else 2 if args.verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    if not result.wasSuccessful():
        if args.exitfirst or (args.maxfail is not None and result.failures):
            sys.exit(1)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
