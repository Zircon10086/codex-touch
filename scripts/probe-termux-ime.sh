#!/usr/bin/env bash
# Run in a fresh Termux shell (or an interactive guest shell), outside Codex/tmux.
set -eu

usage='Usage: bash scripts/probe-termux-ime.sh [--ime-window]'
case "${1-}" in
    --help) echo "$usage"; exit 0 ;;
    --ime-window|'') ;;
    *) echo "$usage" >&2; exit 2 ;;
esac
[[ $# -le 1 ]] || { echo "$usage" >&2; exit 2; }
[[ -t 0 && -t 1 ]] || { echo 'An interactive terminal is required.' >&2; exit 1; }

saved=$(stty -g)
on=$'\033[?1000h\033[?1006h'
off=$'\033[?1006l\033[?1000l'
cleanup() {
    printf '%s\033[?1049l' "$off"
    stty "$saved"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 148' TSTP

stty -echo -icanon min 1 time 0
target='[ Test input ]'
printf '\033[?1049h\033[2J\033[H%s%s\033[2;1H%s\033[4;1H%s' \
    "$on" 'Tap the field or a blank cell.' "$target" 'q: quit (auto-exit: 45s)'
pattern='^([0-9]{1,3});([0-9]{1,5});([0-9]{1,5})([Mm])$'
pressed=0
count=0
deadline=$((SECONDS + 45))
while (( SECONDS < deadline )); do
    IFS= read -rsn 1 -t 1 ch || continue
    [[ $ch != q ]] || break
    [[ $ch == $'\033' ]] || continue
    IFS= read -rsn 2 -t 0.25 prefix && [[ $prefix == '[<' ]] || continue
    report=''
    for ((i=0; i<16; i++)); do
        IFS= read -rsn 1 -t 0.25 ch || break
        report+=$ch
        [[ $ch == [0-9\;] ]] || break
    done
    [[ $report =~ $pattern ]] || { pressed=0; continue; }
    button=${BASH_REMATCH[1]}
    x=$((10#${BASH_REMATCH[2]}))
    y=$((10#${BASH_REMATCH[3]}))
    edge=${BASH_REMATCH[4]}
    hit=0
    (( y == 2 && x >= 1 && x <= ${#target} )) && hit=1
    if [[ $button == 0 && $edge == M ]]; then
        pressed=$hit
        continue
    fi
    if [[ $button == 0 && $edge == m ]]; then
        ((count+=1))
        label='outside'
        if (( pressed && hit )); then
            label='field'
            if [[ ${1-} == --ime-window ]]; then
                # See whether Termux checks mouse mode again when it confirms the tap.
                printf '%s' "$off"
                sleep 0.7
                printf '%s' "$on"
            fi
        fi
        printf '\033[6;1H\033[2Ktap %d: %s' "$count" "$label"
    fi
    pressed=0
done
