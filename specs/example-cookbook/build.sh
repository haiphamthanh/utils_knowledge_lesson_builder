#!/usr/bin/env bash
set -euo pipefail

BOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="$BOOK_DIR/dist"
TARGET="${1:-all}"
PDF_OUTPUT="$DIST_DIR/system-engineering-cookbook.pdf"
HTML_OUTPUT="$DIST_DIR/system-engineering-cookbook.html"

usage() {
  echo "Usage: $0 {pdf|html|all|clean}"
}

require_command() {
  local command_name="$1"
  local install_hint="$2"
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "[cookbook] Missing command: $command_name"
    echo "[cookbook] $install_hint"
    exit 1
  fi
}

build_pdf() {
  require_command pandoc "Install Pandoc 3.x from https://pandoc.org/installing.html"
  require_command xelatex \
    "Ubuntu: sudo apt install texlive-xetex texlive-latex-extra fonts-texgyre"
  echo "[cookbook] Building PDF..."
  (
    cd "$BOOK_DIR"
    pandoc --defaults=book.yaml \
      --to=latex \
      --pdf-engine=xelatex \
      --template=theme/pdf-template.tex \
      --output="$PDF_OUTPUT"
  )
  echo "[cookbook] Created $PDF_OUTPUT"
}

build_html() {
  require_command pandoc "Install Pandoc 3.x from https://pandoc.org/installing.html"
  echo "[cookbook] Building standalone HTML..."
  (
    cd "$BOOK_DIR"
    pandoc --defaults=book.yaml \
      --to=html5 \
      --template=theme/html-template.html \
      --css=theme/book.css \
      --embed-resources \
      --output="$HTML_OUTPUT"
  )
  echo "[cookbook] Created $HTML_OUTPUT"
}

case "$TARGET" in
  pdf)
    mkdir -p "$DIST_DIR"
    build_pdf
    ;;
  html)
    mkdir -p "$DIST_DIR"
    build_html
    ;;
  all)
    mkdir -p "$DIST_DIR"
    build_pdf
    build_html
    ;;
  clean)
    if [[ "$DIST_DIR" != "$BOOK_DIR/dist" ]]; then
      echo "[cookbook] Refusing to clean an unexpected directory."
      exit 1
    fi
    rm -rf "$DIST_DIR"
    echo "[cookbook] Removed generated output."
    ;;
  *)
    usage
    exit 1
    ;;
esac

