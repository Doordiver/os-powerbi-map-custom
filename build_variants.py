import copy
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PBIVIZ_JSON = ROOT / "pbiviz.json"
RESOURCES_TS = ROOT / "src" / "resources.ts"
DIST = ROOT / "dist"

FULL_OUTPUT = DIST / "OS-Map-Full-Build.pbiviz"
LIGHT_OUTPUT = DIST / "OS-Map-Lightweight.pbiviz"

LIGHT_NAME = "oSMapsLight"
LIGHT_GUID = "oSMapsLight455D1584AE894DF6B26F87D8DED2142C"

# Preserve the exact original files so they can be restored afterwards.
original_pbiviz = PBIVIZ_JSON.read_bytes()
original_resources = RESOURCES_TS.read_bytes()

def set_lightweight_switch(enabled):
    text = RESOURCES_TS.read_text(encoding="utf-8")
    updated, count = re.subn(
        r"export const IS_LIGHTWEIGHT_BUILD = (?:true|false);",
        f"export const IS_LIGHTWEIGHT_BUILD = {str(enabled).lower()};",
        text,
    )
    if count != 1:
        raise RuntimeError("Could not find exactly one IS_LIGHTWEIGHT_BUILD setting.")
    RESOURCES_TS.write_text(updated, encoding="utf-8")

def build_variant(metadata, lightweight, output_path):
    metadata["visual"]["guid"] = (
        LIGHT_GUID if lightweight else original_metadata["visual"]["guid"]
    )

    if lightweight:
        metadata["visual"]["name"] = LIGHT_NAME
        metadata["visual"]["displayName"] = "OS Power BI Map Visual (Lightweight)"

    PBIVIZ_JSON.write_text(
        json.dumps(metadata, indent=4) + "\n",
        encoding="utf-8",
    )
    set_lightweight_switch(lightweight)

    print(f"\nBuilding {'lightweight' if lightweight else 'full'} version...")
    subprocess.run(["npm", "run", "package"], cwd=ROOT, check=True)

    guid = metadata["visual"]["guid"]
    version = metadata["visual"]["version"]
    package_path = DIST / f"{guid}.{version}.pbiviz"

    if not package_path.is_file():
        raise FileNotFoundError(f"Expected package was not created: {package_path}")

    shutil.copy2(package_path, output_path)
    print(f"Created: {output_path}")

try:
    original_metadata = json.loads(original_pbiviz.decode("utf-8"))
    full_metadata = copy.deepcopy(original_metadata)
    light_metadata = copy.deepcopy(original_metadata)

    DIST.mkdir(exist_ok=True)

    build_variant(full_metadata, False, FULL_OUTPUT)
    build_variant(light_metadata, True, LIGHT_OUTPUT)

    print("\nBoth Power BI visual packages were created successfully.")

finally:
    # Restore the repository files exactly as they were before the script ran.
    PBIVIZ_JSON.write_bytes(original_pbiviz)
    RESOURCES_TS.write_bytes(original_resources)
    print("Original pbiviz.json and resources.ts have been restored.")
