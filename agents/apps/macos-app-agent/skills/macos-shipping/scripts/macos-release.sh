#!/bin/bash
# Developer ID release steps for a macOS app: preflight, sign, DMG, notarize, verify, gatekeeper.
#
#   macos-release.sh preflight                                   identity and notary credentials work
#   macos-release.sh sign <App.app> [entitlements] [inherit]     inside-out signing, hardened runtime
#   macos-release.sh dmg <App.app> <out.dmg>                     DMG with an /Applications link, signed
#   macos-release.sh notarize <file.dmg|file.pkg|file.zip|App.app>  submit, require Accepted, log, staple
#   macos-release.sh verify <App.app|file.dmg>                   read-only checks; non-zero on failure
#   macos-release.sh gatekeeper <file.dmg>                       a user's double-click: quarantined
#                    copy, app copied out, spctl + syspolicy_check distribution
#   macos-release.sh selftest                                    ad-hoc run on a throwaway bundle
#
# Release order (two notarizations): notarize App.app (zipped, then the .app is stapled), dmg,
# notarize App.dmg, verify both, gatekeeper App.dmg. A ticket on the DMG alone is not enough.
#
# Environment (no secret values, only names and paths):
#   SIGN_ID          signing identity; default "Developer ID Application". codesign matches a
#                    substring: when more than one matches, set the SHA-1 hash of one
#   NOTARY_PROFILE   notarytool keychain profile; default "notary"
#   ASC_KEY_PATH, ASC_KEY_ID, ASC_ISSUER   use an App Store Connect API key instead (CI)
#
# Electron apps: electron-builder signs, notarizes and staples the .app (references/electron.md);
# then dmg, notarize, verify, gatekeeper here. Xcode apps: export with Developer ID, then the same.
set -euo pipefail

ID="${SIGN_ID:-Developer ID Application}"
PROFILE="${NOTARY_PROFILE:-notary}"
TS=--timestamp   # only selftest overrides it (ad-hoc signing cannot be timestamped)
TAB=$'\t'
# Signed by a Developer ID Application certificate issued by Apple. A Team ID string alone proves
# nothing: anyone can ad-hoc sign with --team-identifier.
DEVID_REQ='anchor apple generic and certificate 1[field.1.2.840.113635.100.6.2.6] exists and certificate leaf[field.1.2.840.113635.100.6.1.13] exists'
WORK="$(mktemp -d)"   # every temp file lives here
MOUNTED=""           # a disk image gatekeeper attached
cleanup() {
  if [ -n "$MOUNTED" ]; then hdiutil detach -quiet "$MOUNTED" 2>/dev/null || hdiutil detach -force -quiet "$MOUNTED" || true; fi
  rm -rf "$WORK"
}
trap cleanup EXIT

die() { echo "macos-release: $*" >&2; exit 1; }
check() { echo "+ $*"; "$@" || { FAIL=1; echo "FAILED: $*" >&2; }; }   # record a failure, keep going
json_field() { plutil -extract "$1" raw -o - - 2>/dev/null || true; }   # JSON on stdin

# "path<TAB>kind" for the code under <dir>, with one `file` run for all files. Kinds:
#   EXEC       Mach-O executable (a bundled tool, a bundle's main executable)
#   LIB        Mach-O dylib or loadable bundle
#   APP        nested .app that the app launches itself (helper apps): gets the inherit entitlements
#   BUNDLE     other bundle with an executable (XPC service, extension, plug-in, login item)
#   FRAMEWORK  .framework
#   SKIP       Mach-O that can't be signed (object files, dSYM companions)
# Resource-only bundles are sealed by the bundle around them, not signed on their own. `file` adds
# one "path (for architecture x):" line per slice of a universal binary; those are dropped.
# A failing find (an unreadable folder) fails the whole list instead of shortening it.
code_list() {
  local d
  find "$1" -type f -exec file -N -F "$TAB" {} + | awk -F"$TAB" '
    $2 !~ /Mach-O/ || $1 ~ / \(for architecture [^)]*\):$/ { next }
    $2 ~ /executable/ { print $1 FS "EXEC"; next }
    $2 ~ /shared library|bundle/ { print $1 FS "LIB"; next }
    { print $1 FS "SKIP" }' || return 1
  find "$1" -mindepth 2 -type d -path '*/Contents/MacOS' | while IFS= read -r d; do
    d="${d%/Contents/MacOS}"
    case "$d" in
      */Contents/Library/LoginItems/*) echo "$d${TAB}BUNDLE" ;;   # launchd starts these, not the app
      *.app) echo "$d${TAB}APP" ;;
      *) echo "$d${TAB}BUNDLE" ;;
    esac
  done || return 1
  find "$1" -type d -name '*.framework' | sed "s|\$|${TAB}FRAMEWORK|" || return 1
}

is_dmg() { case "$1" in *.[dD][mM][gG]) return 0 ;; *) return 1 ;; esac; }

notary_auth() {
  if [ -n "${ASC_KEY_PATH:-}" ]; then
    [ -n "${ASC_KEY_ID:-}" ] && [ -n "${ASC_ISSUER:-}" ] || die "ASC_KEY_PATH needs ASC_KEY_ID and ASC_ISSUER"
    AUTH=(--key "$ASC_KEY_PATH" --key-id "$ASC_KEY_ID" --issuer "$ASC_ISSUER")
  else
    AUTH=(--keychain-profile "$PROFILE")
  fi
}

preflight() {
  local ids match n; ids="$(security find-identity -v -p codesigning)"
  match="$(grep -iF "$ID" <<<"$ids" || true)"   # codesign accepts a lowercase SHA-1
  n="$(grep -c . <<<"$match" || true)"
  [ "$n" -gt 0 ] || die "no '$ID' identity in the keychain (security find-identity -v -p codesigning)"
  [ "$n" -eq 1 ] || die "$n identities match '$ID': set SIGN_ID to the SHA-1 hash of one"
  case "$match" in *'"Developer ID Application: '*) ;;   # works for a name or a SHA-1 hash
    *) die "'$ID' is not a Developer ID Application identity; notarization rejects it: $match" ;;
  esac
  notary_auth
  xcrun notarytool history "${AUTH[@]}" >/dev/null \
    || die "notary credentials rejected: no profile '$PROFILE', or the API key is stale or revoked"
  echo "preflight ok: identity '$ID', notary credentials accepted"
}

sign_one() {  # <path> [entitlements]
  if [ -n "${2:-}" ]; then
    codesign --force --sign "$ID" $TS --options runtime --entitlements "$2" "$1"
  else
    codesign --force --sign "$ID" $TS --options runtime "$1"
  fi
}

sign() {
  local app="${1:?usage: sign <App.app> [entitlements] [inherit-entitlements]}"
  local ent="${2:-}" inh="${3:-}" p kind list e n=0
  [ -d "$app/Contents" ] || die "$app is not an app bundle"
  for p in "$ent" "$inh"; do [ -z "$p" ] || plutil -lint -s "$p" || die "invalid entitlements: $p"; done
  # Inside out, deepest path first, never --deep: Mach-O files, then nested bundles, the app last.
  # Tools and helper apps the app launches get the inherit entitlements (none unless given).
  # XPC services, extensions, plug-ins and login items keep the entitlements they were signed with
  # (read before anything is re-signed); sign one by hand first to give it its own. Libraries and
  # frameworks get none.
  list="$(code_list "$app/Contents")" || die "could not list the code in $app"
  : > "$WORK/kept"
  while IFS="$TAB" read -r p kind; do
    [ "$kind" = BUNDLE ] || continue
    n=$((n + 1)); e="$WORK/kept-$n.plist"
    if codesign -d --entitlements - --xml "$p" > "$e" 2>/dev/null && [ -s "$e" ]; then
      printf '%s\t%s\n' "$p" "$e" >> "$WORK/kept"
    fi
  done <<<"$list"
  while IFS="$TAB" read -r p kind; do
    case "$kind" in
      EXEC|APP) sign_one "$p" "$inh" ;;
      BUNDLE)
        e="$(awk -F"$TAB" -v p="$p" '$1 == p { print $2 }' "$WORK/kept")"
        [ -z "$e" ] || echo "keeping the entitlements of $p" >&2
        sign_one "$p" "$e" ;;
      LIB|FRAMEWORK) sign_one "$p" ;;
      SKIP) echo "skipping $p (Mach-O that can't be signed)" >&2 ;;
    esac
  done < <(awk -F"$TAB" 'NF { print split($1, parts, "/") FS $0 }' <<<"$list" | sort -rn -k1,1 | cut -f2-)
  sign_one "$app" "$ent"
  codesign --verify --deep --strict "$app"
  echo "signed: $app"
}

dmg() {
  local app="${1:?usage: dmg <App.app> <out.dmg>}" out="${2:?usage: dmg <App.app> <out.dmg>}"
  is_dmg "$out" || die "the output name must end in .dmg (hdiutil would add it): $out"
  STAGE="$WORK/dmg"; rm -rf "$STAGE"; mkdir "$STAGE"
  ditto "$app" "$STAGE/$(basename "$app")"          # ditto keeps symlinks and signatures intact
  ln -s /Applications "$STAGE/Applications"
  hdiutil create -volname "$(basename "$app" .app)" -srcfolder "$STAGE" -fs HFS+ -format UDZO -ov "$out" >/dev/null
  hdiutil verify "$out" >/dev/null
  codesign --force --sign "$ID" $TS "$out"          # an Application identity, never an Installer one
  echo "dmg: $out"
}

notarize() {
  local f="${1:?usage: notarize <file.dmg|file.pkg|file.zip|App.app>}" sub out id status log
  notary_auth
  sub="$f"
  if [ -d "$f" ]; then   # an .app is submitted as a zip, then the .app itself is stapled
    sub="$WORK/$(basename "$f").zip"
    ditto -c -k --keepParent "$f" "$sub"
  fi
  out="$(xcrun notarytool submit "$sub" "${AUTH[@]}" --wait --output-format json)" || true
  id="$(printf '%s' "$out" | json_field id)"
  status="$(printf '%s' "$out" | json_field status)"
  [ -n "$id" ] || die "submission failed: $out"
  log="${f%/}.notary-log.json"
  xcrun notarytool log "$id" "${AUTH[@]}" "$log" >/dev/null || echo "warning: could not fetch the notary log" >&2
  # Check the status itself: some notarytool versions exit 0 on Invalid.
  if [ "$status" != "Accepted" ]; then
    printf '%s\n' "$out" >&2
    [ -f "$log" ] && cat "$log" >&2
    case "$status" in Invalid|Rejected)   # a rejected artifact must not be uploaded by mistake
      mv "$f" "${f%/}.rejected"; echo "renamed to ${f%/}.rejected" >&2 ;;
    *) echo "not rejected yet: check later with xcrun notarytool info $id" >&2 ;;
    esac
    die "notarization ${status:-unknown} (submission $id); log in $log"
  fi
  echo "accepted: submission $id; read the warnings in $log"
  case "$f" in
    *.zip) echo "a zip cannot be stapled: staple the .app inside it and zip it again" ;;
    *) xcrun stapler staple "$f" && xcrun stapler validate "$f" ;;
  esac
}

verify() {
  local t="${1:?usage: verify <App.app|file.dmg>}" team p kind info list
  [ $# -eq 1 ] || die "usage: verify <App.app|file.dmg>"
  [ -e "$t" ] || die "no such file: $t"
  FAIL=0
  if is_dmg "$t"; then
      check codesign --verify --strict --verbose=2 -R="$DEVID_REQ" "$t"
      check xcrun stapler validate "$t"
      check spctl -a -vvv -t open --context context:primary-signature "$t"
  else
      # -R tests only the top-level code; the loop below tests each nested Mach-O against it
      check codesign --verify --deep --strict --verbose=2 -R="$DEVID_REQ" "$t"
      codesign -dvv "$t" 2>&1 | grep -E '^(Authority|TeamIdentifier|Timestamp)=|flags=' || true
      echo "entitlements:"; codesign -d --entitlements - --xml "$t" 2>/dev/null | plutil -p - 2>/dev/null || echo "  (none)"
      team="$(codesign -dv "$t" 2>&1 | sed -n 's/^TeamIdentifier=//p' || true)"   # unsigned: keep auditing
      list="$(code_list "$t")" || die "could not list the code in $t"
      while IFS="$TAB" read -r p kind; do   # every Mach-O: Developer ID, same team, runtime, timestamp
        case "$kind" in EXEC|LIB) ;; *) continue ;; esac
        codesign --verify -R="$DEVID_REQ" "$p" 2>/dev/null || { FAIL=1; echo "FAILED: $p is not Developer ID signed" >&2; }
        info="$(codesign -dvv "$p" 2>&1 || true)"
        grep -q "^TeamIdentifier=$team\$" <<<"$info" || { FAIL=1; echo "FAILED: $p not signed by team $team" >&2; }
        grep -q 'flags=.*runtime' <<<"$info" || { FAIL=1; echo "FAILED: $p lacks hardened runtime" >&2; }
        grep -q '^Timestamp=' <<<"$info" || { FAIL=1; echo "FAILED: $p has no secure timestamp" >&2; }
      done <<<"$list"
      # The .app needs its own ticket: with only the DMG stapled, spctl still accepts the app but
      # syspolicy_check distribution fails with "Notary Ticket Missing".
      check xcrun stapler validate "$t"
      check spctl -a -vvv -t exec "$t"
  fi
  [ "$FAIL" = 0 ] || die "verify failed: $t"
  echo "verify ok: $t (then run gatekeeper on the DMG)"
}

gatekeeper() {
  local dmg="${1:-}" copy app q
  [ $# -eq 1 ] && is_dmg "$dmg" && [ -f "$dmg" ] || die "usage: gatekeeper <file.dmg>"
  # A browser download: the copy carries com.apple.quarantine. The build Mac never quarantines its
  # own builds, so without this the checks pass on files no user ever receives.
  copy="$WORK/download.dmg"; cp "$dmg" "$copy"
  q="0083;$(printf '%x' "$(date +%s)");Safari;$(uuidgen)"
  xattr -w com.apple.quarantine "$q" "$copy"
  mkdir -p "$WORK/mnt" "$WORK/installed"
  hdiutil attach -nobrowse -readonly -noautoopen -mountpoint "$WORK/mnt" "$copy" >/dev/null
  MOUNTED="$WORK/mnt"
  for app in "$WORK/mnt"/*.app; do break; done
  [ -d "$app" ] || die "no .app at the top of $dmg"
  ditto "$app" "$WORK/installed/$(basename "$app")"     # the drag to /Applications
  app="$WORK/installed/$(basename "$app")"
  xattr -w com.apple.quarantine "$q" "$app"             # copied out of a quarantined image
  FAIL=0
  check spctl -a -vvv -t exec "$app"
  if command -v syspolicy_check >/dev/null; then
    check syspolicy_check distribution "$app"
  else
    echo "note: syspolicy_check needs macOS 14 or later; only spctl ran"
  fi
  hdiutil detach -quiet "$MOUNTED" && MOUNTED=""
  [ "$FAIL" = 0 ] || die "gatekeeper: a user opening $dmg would be blocked or warned"
  echo "gatekeeper ok: $dmg opens like a notarized download"
}

selftest() {
  local app ent p info
  TESTDIR="$WORK/selftest"; mkdir "$TESTDIR"
  app="$TESTDIR/Demo.app"
  mkdir -p "$app/Contents/MacOS" "$app/Contents/Resources/bin" "$app/Contents/Frameworks/Helper.app/Contents/MacOS" \
    "$app/Contents/XPCServices/Svc.xpc/Contents/MacOS"
  cp /usr/bin/true "$app/Contents/XPCServices/Svc.xpc/Contents/MacOS/Svc"
  cp /usr/bin/true "$app/Contents/MacOS/Demo"
  cp /usr/bin/true "$app/Contents/Resources/bin/tool"
  cp /usr/bin/true "$app/Contents/Frameworks/Helper.app/Contents/MacOS/Helper"
  echo data > "$app/Contents/Resources/data.txt"
  mkdir -p "$app/Contents/Resources/Res.bundle/Contents/Resources"   # resource-only bundle: not signed alone
  echo data > "$app/Contents/Resources/Res.bundle/Contents/Resources/x.txt"
  # a Mach-O object file (header only): codesign refuses these, so sign must skip it
  Z='\x00\x00\x00\x00'   # magic, arm64, subtype 0, filetype 1 (object), then zeros
  printf '\xcf\xfa\xed\xfe\x0c\x00\x00\x01%b\x01\x00\x00\x00%b%b%b%b' "$Z" "$Z" "$Z" "$Z" "$Z" \
    > "$app/Contents/Resources/prebuilt.o"
  plutil -create xml1 "$app/Contents/Info.plist"
  plutil -insert CFBundleIdentifier -string test.demo "$app/Contents/Info.plist"
  plutil -insert CFBundleExecutable -string Demo "$app/Contents/Info.plist"
  cp "$app/Contents/Info.plist" "$app/Contents/Frameworks/Helper.app/Contents/Info.plist"
  plutil -replace CFBundleExecutable -string Helper "$app/Contents/Frameworks/Helper.app/Contents/Info.plist"
  plutil -replace CFBundleIdentifier -string test.demo.helper "$app/Contents/Frameworks/Helper.app/Contents/Info.plist"
  ent="$TESTDIR/ent.plist"
  cat > "$ent" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict><key>com.apple.security.cs.allow-jit</key><true/></dict></plist>
EOF

  cp "$app/Contents/Info.plist" "$app/Contents/XPCServices/Svc.xpc/Contents/Info.plist"
  plutil -replace CFBundleExecutable -string Svc "$app/Contents/XPCServices/Svc.xpc/Contents/Info.plist"
  plutil -replace CFBundleIdentifier -string test.demo.svc "$app/Contents/XPCServices/Svc.xpc/Contents/Info.plist"
  # the XPC service is signed with its own entitlements first; sign must keep them
  codesign --force --sign - --options runtime --entitlements "$ent" "$app/Contents/XPCServices/Svc.xpc" 2>/dev/null

  # no `|| die` on the sign and dmg calls: it would switch off set -e inside the function
  ID=- TS=--timestamp=none sign "$app" "$ent" "$ent" >/dev/null
  codesign --verify --deep --strict "$app" || die "selftest: bundle does not verify after inside-out signing"
  for p in MacOS/Demo Resources/bin/tool Frameworks/Helper.app; do
    # capture first: grep -q closing the pipe early would trip pipefail
    info="$(codesign -dvv "$app/Contents/$p" 2>&1)"
    grep -q 'flags=.*runtime' <<<"$info" || die "selftest: $p lacks hardened runtime"
    info="$(codesign -d --entitlements - --xml "$app/Contents/$p" 2>/dev/null)"
    grep -q allow-jit <<<"$info" || die "selftest: $p lacks the inherit entitlements"
  done
  ( ID=- TS=--timestamp=none dmg "$app" "$TESTDIR/Demo" ) 2>/dev/null && die "selftest: dmg accepted a name without .dmg"
  ID=- TS=--timestamp=none dmg "$app" "$TESTDIR/Demo.dmg" >/dev/null
  codesign --verify --strict "$TESTDIR/Demo.dmg" || die "selftest: dmg is not signed"
  ( verify "$app" ) >/dev/null 2>&1 && die "selftest: verify accepted an ad-hoc app"
  ( verify "$app" --bogus ) >/dev/null 2>&1 && die "selftest: verify accepted an extra argument"
  # gatekeeper runs in its own process (its own temp dir and cleanup) and must reject ad-hoc code
  # and leave nothing mounted
  # "$BASH": works without the exec bit; the message proves the checks ran (not a failed start or attach)
  info="$("$BASH" "$0" gatekeeper "$TESTDIR/Demo.dmg" 2>&1 >/dev/null || true)"
  grep -q "gatekeeper: a user opening" <<<"$info" || die "selftest: gatekeeper did not reject an ad-hoc DMG: $info"
  info="$(hdiutil info)"
  ! grep -q "$TESTDIR/Demo.dmg\|/download.dmg" <<<"$info" || die "selftest: gatekeeper left a disk image attached"
  # the requirement must parse and must reject ad-hoc code ("invalid requirement" would mean a typo)
  info="$(codesign --verify -R="$DEVID_REQ" "$app" 2>&1 || true)"
  grep -q 'failed to satisfy' <<<"$info" || die "selftest: Developer ID requirement: $info"
  is_dmg "x.DMG" && ! is_dmg "x.app" || die "selftest: is_dmg"
  # without an inherit file, nested code gets no entitlements
  ID=- TS=--timestamp=none sign "$app" "$ent" >/dev/null 2>&1
  info="$(codesign -d --entitlements - --xml "$app/Contents/Resources/bin/tool" 2>/dev/null)"
  ! grep -q allow-jit <<<"$info" || die "selftest: nested tool got entitlements with no inherit file"
  info="$(codesign -d --entitlements - --xml "$app/Contents/XPCServices/Svc.xpc" 2>/dev/null)"
  grep -q allow-jit <<<"$info" || die "selftest: the XPC service lost its own entitlements"
  [ "$(printf '{"id":"abc","status":"Accepted"}' | json_field status)" = Accepted ] || die "selftest: json_field"
  [ -z "$(printf 'not json' | json_field status)" ] || die "selftest: json_field on bad input"
  echo "selftest ok"
}

cmd="${1:-}"; shift || true
case "$cmd" in
  preflight|sign|dmg|notarize|verify|gatekeeper|selftest) "$cmd" "$@" ;;
  *) awk 'NR > 1 { if (/^set -euo/) exit; print }' "$0"; exit 2 ;;
esac
