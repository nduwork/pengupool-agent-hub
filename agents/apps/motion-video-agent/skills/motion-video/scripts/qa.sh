#!/usr/bin/env bash
# QA sheets for a rendered video. Outputs land next to the input. Contact and phone sheets cover the
# whole video: the grid grows with its duration.
# Usage: scripts/qa.sh contact|phone|loop <video>   |   scripts/qa.sh strip|poster <video> <seconds>
set -euo pipefail
cmd=${1:?usage: qa.sh contact|phone|strip|loop|poster <video> [seconds]}
in=${2:?video path}
dir=$(dirname "$in")
q="ffmpeg -hide_banner -loglevel error -y"
# sheet <fps> <cols> <width> <out>: one tile per 1/fps seconds, enough rows for the whole duration.
sheet() {
  local dur rows
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$in")
  [[ $dur =~ ^[0-9.]+$ ]] || { echo "qa.sh: no duration for $in (ffprobe said '$dur')" >&2; exit 1; }
  rows=$(awk -v d="$dur" -v f="$1" -v c="$2" 'BEGIN { n = int(d * f + 0.999); print int((n + c - 1) / c) }')
  $q -i "$in" -vf "fps=$1,scale=$3:-1,tile=$2x$rows" -frames:v 1 "$4"
}
case $cmd in
  contact) sheet 2 6 270 "$dir/contact.png" ;;
  phone)   sheet 1 5 360 "$dir/phone.png" ;;
  strip)   $q -ss "${3:?seconds}" -i "$in" -vf "scale=320:-1,tile=12x1" -frames:v 1 "$dir/strip_$3.png" ;;
  loop)    $q -stream_loop 2 -i "$in" -c copy "$dir/loop_check.mp4" ;;
  poster)  $q -ss "${3:?seconds}" -i "$in" -frames:v 1 "$dir/poster.png" ;;
  *) echo "unknown check: $cmd" >&2; exit 2 ;;
esac
echo "$cmd → $dir"
