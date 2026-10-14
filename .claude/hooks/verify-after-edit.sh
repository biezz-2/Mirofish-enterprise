#!/bin/bash
# PostToolUse hook for Edit|Write matcher
# Remind about ground-truth verification

payload=$(cat | jq -r '.tool_input.file_path // empty')

if [ -n "$payload" ]; then
    echo "Pengingat: Verifikasi kebenaran ground-truth (typecheck/linter/test) untuk file $payload!"
fi

exit 0
