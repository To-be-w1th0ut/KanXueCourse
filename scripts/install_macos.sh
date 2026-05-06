#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/To-be-w1th0ut/KanXueCourse.git"
TARGET_DIR="${TARGET_DIR:-$HOME/KanXueCourse}"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "[!] 请在 macOS 上运行此脚本"
  exit 1
fi

if ! command -v git >/dev/null 2>&1; then
  echo "[*] 正在触发 Xcode Command Line Tools 安装"
  xcode-select --install || true
  echo "[!] 请完成 Git 安装后重新运行本脚本"
  exit 1
fi

if [[ ! -d /Applications/Docker.app ]]; then
  ARCH="$(uname -m)"
  if [[ "$ARCH" == "arm64" ]]; then
    DOCKER_URL="https://desktop.docker.com/mac/main/arm64/Docker.dmg"
  else
    DOCKER_URL="https://desktop.docker.com/mac/main/amd64/Docker.dmg"
  fi
  curl -L "$DOCKER_URL" -o /tmp/Docker.dmg
  sudo hdiutil attach /tmp/Docker.dmg
  sudo /Volumes/Docker/Docker.app/Contents/MacOS/install --accept-license
  sudo hdiutil detach /Volumes/Docker
fi

open -a Docker
until docker info >/dev/null 2>&1; do
  echo "waiting Docker Desktop..."
  sleep 5
done

if [[ -d "$TARGET_DIR/.git" ]]; then
  git -C "$TARGET_DIR" pull --ff-only
else
  rm -rf "$TARGET_DIR"
  git clone "$REPO_URL" "$TARGET_DIR"
fi

cd "$TARGET_DIR/web-fieldlab"
cp .env.example .env
docker compose up -d --build
docker compose ps

for _ in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:5070/healthz >/dev/null 2>&1; then
    break
  fi
  sleep 3
done

LAN_IP="$(ipconfig getifaddr en0 || ipconfig getifaddr en1 || true)"
echo "[+] 本机访问: http://127.0.0.1:5070"
echo "[+] 局域网访问: http://${LAN_IP}:5070"
