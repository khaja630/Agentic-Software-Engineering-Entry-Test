import json
from pathlib import Path
import sys
import urllib.error
import urllib.request
from packaging.specifiers import SpecifierSet
from packaging.version import Version
TARGET_PYTHON = Version("3.11")

def fetch_json(url):
    request = urllib.request.Request(
        url, headers={"User-Agent": "agentic-software-engineering"}
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise
def main():
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
    else:
        input_path = Path(__file__).with_name("requirements.txt")
    lines = input_path.read_text(encoding="utf-8").splitlines()
    not_found = 0
    incompatible = 0
    highest_minimum = None
    highest_requirement = None
    for line_number, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue
        parts = line.split("==")
        if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
            raise ValueError(f"Line {line_number}: expected name==version")
        name = parts[0].strip()
        version = parts[1].strip()
        release = fetch_json(f"https://pypi.org/pypi/{name}/{version}/json")
        if release is None:
            not_found += 1
            continue
        requires_python = release["info"].get("requires_python") or ""
        if not requires_python.strip():
            # The question counts a release with no requirement as compatible.
            continue
        specifiers = SpecifierSet(requires_python)
        if TARGET_PYTHON not in specifiers:
            incompatible += 1
        for specifier in specifiers:
            if specifier.operator == ">=":
                minimum = Version(specifier.version)
                if highest_minimum is None or minimum > highest_minimum:
                    highest_minimum = minimum
                    highest_requirement = f"{name}=={version}"
    
    print(f"Dependencies checked: {len(lines)}")
    print(f"Not found on PyPI: {not_found}")
    print(f"Incompatible with Python 3.11: {incompatible}")
    if highest_minimum is None:
        print("Highest requirement: none")
    else:
        print(f"Highest requirement: {highest_requirement} (>={highest_minimum})")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, urllib.error.URLError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
