#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

OPENAPI_FILE="${PROJECT_ROOT}/api/openapi.yaml"
OUTPUT_FILE="${PROJECT_ROOT}/api/server.gen.go"
PACKAGE_NAME="api"
OAPI_CODEGEN="${OAPI_CODEGEN:-github.com/oapi-codegen/oapi-codegen/v2/cmd/oapi-codegen@v2.7.0}"

if [[ ! -f "${OPENAPI_FILE}" ]]; then
  echo "OpenAPI file not found: ${OPENAPI_FILE}" >&2
  exit 1
fi

GEN_WORKDIR="$(mktemp -d)"
trap 'rm -rf "${GEN_WORKDIR}"' EXIT

(
  cd "${GEN_WORKDIR}"
  go mod init psyled-go-codegen >/dev/null 2>&1
  go run "${OAPI_CODEGEN}" \
    -generate "types,std-http,spec" \
    -package "${PACKAGE_NAME}" \
    -o "${OUTPUT_FILE}" \
    "${OPENAPI_FILE}"
)

echo "Generated ${OUTPUT_FILE}"
