#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/To-be-w1th0ut/KanXueCourse.git"
TARGET_DIR="${TARGET_DIR:-$HOME/KanXueCourse}"

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "[!] 请在 Linux 上运行此脚本"
  exit 1
fi

if ! command -v apt >/dev/null 2>&1; then
  echo "[!] 当前脚本仅支持 Ubuntu / Debian（apt）"
  exit 1
fi

sudo apt update
sudo apt install -y git ca-certificates curl

if ! command -v docker >/dev/null 2>&1; then
  sudo apt remove -y docker.io docker-compose docker-compose-v2 docker-doc podman-docker containerd runc || true
  sudo install -m 0755 -d /etc/apt/keyrings
  sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  sudo chmod a+r /etc/apt/keyrings/docker.asc
  sudo tee /etc/apt/sources.list.d/docker.sources > /dev/null <<EOF2
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF2
  sudo apt update
  sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  sudo systemctl enable --now docker
fi

DOCKER="docker"
if ! docker info >/dev/null 2>&1; then
  DOCKER="sudo docker"
fi

if [[ -d "$TARGET_DIR/.git" ]]; then
  git -C "$TARGET_DIR" pull --ff-only
else
  rm -rf "$TARGET_DIR"
  git clone "$REPO_URL" "$TARGET_DIR"
fi

cd "$TARGET_DIR/web-fieldlab"
cp .env.example .env
$DOCKER compose up -d --build
$DOCKER compose ps

for _ in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:5070/healthz >/dev/null 2>&1; then
    break
  fi
  sleep 3
done

LAN_IP="$(hostname -I | awk '{print $1}')"
echo "[+] 本机访问: http://127.0.0.1:5070"
echo "[+] 局域网访问: http://${LAN_IP}:5070"
