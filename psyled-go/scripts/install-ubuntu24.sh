#!/usr/bin/env bash
set -euo pipefail

GO_VERSION="${GO_VERSION:-1.22.5}"
MIN_GO_VERSION="${MIN_GO_VERSION:-1.22.5}"
INSTALL_QJACKCTL="${INSTALL_QJACKCTL:-0}"
TARGET_USER="${SUDO_USER:-${USER}}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Please run this installer with sudo or as root." >&2
  exit 1
fi

if [[ -r /etc/os-release ]]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  if [[ "${ID:-}" != "ubuntu" || "${VERSION_ID:-}" != 24.* ]]; then
    echo "Warning: this script targets Ubuntu 24.x, detected ${PRETTY_NAME:-unknown}." >&2
  fi
fi

apt-get update

export DEBIAN_FRONTEND=noninteractive
echo "jackd2 jackd/tweak_rt_limits boolean true" | debconf-set-selections || true

PACKAGES=(
  ca-certificates
  curl
  git
  tar
  build-essential
  pkg-config
  alsa-utils
  jackd2
  jack-tools
  libjack-jackd2-dev
)

if [[ "${INSTALL_QJACKCTL}" == "1" ]]; then
  PACKAGES+=(qjackctl)
fi

apt-get install -y "${PACKAGES[@]}"

go_version_number() {
  go version 2>/dev/null | awk '{print $3}' | sed 's/^go//'
}

version_ge() {
  [[ "$(printf '%s\n%s\n' "$2" "$1" | sort -V | head -n1)" == "$2" ]]
}

go_archive_arch() {
  case "$(uname -m)" in
    x86_64 | amd64) echo "amd64" ;;
    aarch64 | arm64) echo "arm64" ;;
    armv6l | armv7l) echo "armv6l" ;;
    *)
      echo "Unsupported architecture for official Go archive: $(uname -m)" >&2
      exit 1
      ;;
  esac
}

install_go() {
  local arch archive url tmp
  arch="$(go_archive_arch)"
  archive="go${GO_VERSION}.linux-${arch}.tar.gz"
  url="https://go.dev/dl/${archive}"
  tmp="$(mktemp -d)"
  trap 'rm -rf "${tmp}"' EXIT

  echo "Installing Go ${GO_VERSION} from ${url}"
  curl -fsSL "${url}" -o "${tmp}/${archive}"
  rm -rf /usr/local/go
  tar -C /usr/local -xzf "${tmp}/${archive}"
  cat >/etc/profile.d/go.sh <<'EOF'
export PATH=/usr/local/go/bin:$PATH
EOF
}

current_go="$(go_version_number || true)"
if [[ -z "${current_go}" ]] || ! version_ge "${current_go}" "${MIN_GO_VERSION}"; then
  install_go
else
  echo "Go ${current_go} is already installed and satisfies >= ${MIN_GO_VERSION}."
fi

if id "${TARGET_USER}" >/dev/null 2>&1; then
  usermod -aG audio "${TARGET_USER}"
fi

cat >/etc/security/limits.d/95-psyled-audio.conf <<'EOF'
@audio   -  rtprio     95
@audio   -  memlock    unlimited
@audio   -  nice       -19
EOF

pkg-config --exists jack

cat <<EOF
Ubuntu installer finished.

Installed JACK runtime/development packages and Go tooling.
Target user '${TARGET_USER}' was added to the audio group if it exists.

Log out and back in before running JACK if this is the first time the user was
added to the audio group.

Verify:
  go version
  pkg-config --cflags --libs jack
  cd psyled-go && go test -tags jack ./internal/audio
EOF
