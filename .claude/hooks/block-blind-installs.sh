#!/bin/bash
# PreToolUse hook for Bash matcher
# Blocks blind dependency installation

payload=$(cat | jq -r '.tool_input.command // empty')

if echo "$payload" | grep -qE '(npm i|npm install|pip install|composer require|cargo add|go get)'; then
    echo "Pemasangan dependensi tanpa verifikasi (blind install) dilarang. Harap periksa manifest terlebih dahulu!" >&2
    exit 2
fi

exit 0
