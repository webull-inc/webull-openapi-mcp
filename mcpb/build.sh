#!/usr/bin/env bash
#
# Build the Webull OpenAPI .mcpb bundle in one step.
#
# It installs a *published* release of webull-openapi-mcp from PyPI, extracts
# its live tool list, regenerates manifest.json + pyproject.toml (version and
# Python constraint auto-derived from the installed package), and packs the
# .mcpb. This guarantees the bundle never drifts from what users actually run.
#
# Usage:
#   ./build.sh                # build the version declared in the repo
#   ./build.sh 1.2.0          # build a specific published version
#
# Env overrides:
#   PYTHON=/path/to/python    # interpreter to create the build venv (default: python3)
#   MCPB="mcpb"               # mcpb CLI command (default: npx -y @anthropic-ai/mcpb)
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${SCRIPT_DIR}"

PYTHON="${PYTHON:-python3}"
MCPB="${MCPB:-npx -y @anthropic-ai/mcpb}"
OUTPUT="webull-openapi-mcp.mcpb"
SMITHERY_OUTPUT="webull-openapi-mcp.smithery.mcpb"

# Resolve the version to build: explicit arg, else the repo's declared version.
# Extract the first semver-looking token from __init__.py (avoids fragile quote
# handling in shell) — the file only contains __version__ = "X.Y.Z".
if [[ $# -ge 1 ]]; then
  VERSION="$1"
else
  VERSION="$(grep -oE '[0-9]+\.[0-9]+([.-][0-9A-Za-z]+)*' "${REPO_ROOT}/webull_openapi_mcp/__init__.py" | head -1)"
fi

if [[ -z "${VERSION}" ]]; then
  echo "ERROR: could not resolve version. Pass it explicitly: ./build.sh <version>" >&2
  exit 1
fi

echo ">> Building Webull OpenAPI .mcpb for version ${VERSION}"

# Isolated build venv; removed on exit.
BUILD_VENV="$(mktemp -d)/venv"
cleanup() { rm -rf "$(dirname "${BUILD_VENV}")"; }
trap cleanup EXIT

echo ">> Creating build venv with ${PYTHON}"
"${PYTHON}" -m venv "${BUILD_VENV}"
VENV_PY="${BUILD_VENV}/bin/python"

echo ">> Installing webull-openapi-mcp==${VERSION} from PyPI"
"${VENV_PY}" -m pip install --quiet --upgrade pip
"${VENV_PY}" -m pip install --quiet "webull-openapi-mcp==${VERSION}"

echo ">> Extracting live tool list"
TOOLS_JSON="$(mktemp)"
trap 'cleanup; rm -f "${TOOLS_JSON}"' EXIT
"${VENV_PY}" - "${TOOLS_JSON}" <<'PY'
import asyncio, json, sys
from webull_openapi_mcp.config import load_config
from webull_openapi_mcp.server import build_server

server = build_server(load_config(None))
tools = asyncio.run(server.list_tools())


def convert(ft):
    # FastMCP FunctionTool -> canonical MCP Tool (exposes inputSchema),
    # which Smithery's release validation requires for every tool.
    d = ft.to_mcp_tool().model_dump(by_alias=True, exclude_none=True)
    entry = {"name": d["name"]}
    if d.get("description"):
        entry["description"] = d["description"].strip()
    schema = d.get("inputSchema")
    if not isinstance(schema, dict):
        schema = {"type": "object", "properties": {}}
    entry["inputSchema"] = schema
    return entry


data = sorted((convert(t) for t in tools), key=lambda d: d["name"])
with open(sys.argv[1], "w", encoding="utf-8") as f:
    json.dump(data, f)
print(f"   extracted {len(data)} tools", file=sys.stderr)
PY

# ---- Claude Desktop / MCPB bundle (packed by mcpb; tools without inputSchema) ----
echo ">> Regenerating manifest.json + pyproject.toml (mcpb target)"
"${VENV_PY}" build_manifest.py --tools "${TOOLS_JSON}" --target mcpb

echo ">> Packing ${OUTPUT} (Claude Desktop / GitHub Release)"
${MCPB} pack . "${OUTPUT}"

# ---- Smithery bundle (manual zip; tools WITH inputSchema, required by Smithery) ----
echo ">> Building ${SMITHERY_OUTPUT} (Smithery)"
SMITHERY_MANIFEST="$(mktemp)"
"${VENV_PY}" build_manifest.py --tools "${TOOLS_JSON}" --target smithery --out "${SMITHERY_MANIFEST}" --no-pyproject
SMITHERY_MANIFEST="${SMITHERY_MANIFEST}" SMITHERY_OUTPUT="${SMITHERY_OUTPUT}" "${VENV_PY}" - <<'PY'
import os, zipfile
manifest = os.environ["SMITHERY_MANIFEST"]
out = os.environ["SMITHERY_OUTPUT"]
# Mirror exactly what mcpb pack includes, but swap in the Smithery manifest.
files = ["pyproject.toml", "src/server.py"]
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(manifest, "manifest.json")
    for f in files:
        z.write(f, f)
print(f"   wrote {out}")
PY
rm -f "${SMITHERY_MANIFEST}"

echo ">> Done:"
echo "   ${SCRIPT_DIR}/${OUTPUT}           -> Claude Desktop (double-click) / GitHub Release"
echo "   ${SCRIPT_DIR}/${SMITHERY_OUTPUT}  -> Smithery: smithery mcp publish ./${SMITHERY_OUTPUT} -n <org>/<server>"
