import argparse
import logging
import re
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

SEMVER = r"\d+\.\d+\.\d+"

# Files that carry the wdl-ci version. Each regex's full match is the bare X.Y.Z
# version; lookarounds anchor it to the surrounding literal so we never touch
# unrelated version-like strings such as SHA-pinned third-party actions.
VERSION_LOCATIONS = [
    (
        "pyproject.toml",
        re.compile(r'(?<=^version = ")' + SEMVER + r'(?=")', re.MULTILINE),
    ),
    ("action.yml", re.compile(r"(?<=docker://dnastack/wdl-ci:v)" + SEMVER)),
    ("README.md", re.compile(r"(?<=dnastack/wdl-ci@v)" + SEMVER)),
]


def bump(version):
    for path, pattern in VERSION_LOCATIONS:
        with open(path, "r") as handle:
            text = handle.read()
        new_text, count = pattern.subn(version, text)
        if count == 0:
            logger.error("No version reference found in %s", path)
            return 1
        with open(path, "w") as handle:
            handle.write(new_text)
        logger.info("Updated %d reference(s) in %s -> %s", count, path, version)
    return 0


def check():
    found = {}
    for path, pattern in VERSION_LOCATIONS:
        with open(path, "r") as handle:
            text = handle.read()
        matches = set(pattern.findall(text))
        if not matches:
            logger.error("No version reference found in %s", path)
            return 1
        if len(matches) > 1:
            logger.error("Inconsistent versions within %s: %s", path, sorted(matches))
            return 1
        found[path] = matches.pop()
    unique = set(found.values())
    if len(unique) > 1:
        logger.error("Version mismatch across files: %s", found)
        return 1
    logger.info("Version is consistent across all files: %s", unique.pop())
    return 0


def main(args):
    if args.check:
        return check()
    return bump(args.version)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Bump or verify the wdl-ci version across project files."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-v",
        "--version",
        type=str,
        help="New version to set, e.g. 2.2.0 (no 'v' prefix)",
    )
    group.add_argument(
        "-c",
        "--check",
        action="store_true",
        help="Verify the version is consistent across all files",
    )
    parsed_args = parser.parse_args()
    if parsed_args.version and not re.fullmatch(SEMVER, parsed_args.version):
        parser.error("version must look like X.Y.Z")
    sys.exit(main(parsed_args))
