#!/usr/bin/env bash
# Bash + curl + jq. No API key in command-line arguments or source files.
set -euo pipefail
: "${NEVISA_API_KEY:?Set NEVISA_API_KEY}"
base="${NEVISA_BASE_URL:-https://persianspeech.com}"
base="${base%/}"
audio="${1:?Usage: bash examples/curl/asr.sh AUDIO [ENGINE]}"
engine="${2:-nevisa-file}"
case "$engine" in nevisa-file|nevisa-live|nevisa-fusion) ;; *) echo 'Unknown ASR engine' >&2; exit 1;; esac
# Headers are supplied through stdin, avoiding a key visible in the process list.
api() {
  printf 'X-API-Key: %s\n' "$NEVISA_API_KEY" |
    curl --silent --show-error --fail-with-body --connect-timeout 15 --max-time 180 --header @- "$@"
}
body="$(api --form "audio=@$audio" --form "engine=$engine" --form language=fa "$base/api/jobs/upload/")"
if ! jq -e '(.errors | length) == 0 and (.created | length) > 0' <<<"$body" >/dev/null; then
  printf '%s\n' "$body" >&2; exit 1
fi
job_key="$(jq -r '.created[0].job_key' <<<"$body")"
deadline=$((SECONDS + ${NEVISA_TIMEOUT:-600}))
while (( SECONDS < deadline )); do
  job="$(api "$base/api/jobs/$job_key/")"
  case "$(jq -r .status <<<"$job")" in
    completed) jq -r .result_text <<<"$job"; exit 0;;
    failed|canceled) jq -r .error_message <<<"$job" >&2; exit 1;;
  esac
  sleep 2
done
echo "Polling deadline reached. Resume with GET /api/jobs/$job_key/" >&2
exit 1
