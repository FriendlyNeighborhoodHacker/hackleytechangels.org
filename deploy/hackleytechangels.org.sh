#!/usr/bin/env bash
#
# Deploy hackleytechangels.org from the git clone to the live web root.
#
#   1. reset the clone in $REPO_DIR to origin/$BRANCH
#   2. npm ci && npm run build (Astro static build -> dist/, including the
#      PHP files from public/: contact.php, mailer.php, gitwebhook.php, uptime.php)
#   3. stage dist/ plus config.local.php from $SECRETS_DIR as a fresh web root
#   4. move the current web root to $OLD_ROOT (replacing whatever was there)
#      and swap the fresh one into place
#
# Runs as the site user (no root): php-fpm runs as this same user, so nothing
# needs chown. Nothing in the web root has to survive a deploy.
#
# This file lives in the repo at deploy/hackleytechangels.org.sh, i.e. on the
# server at ~/deploy/hackleytechangels.org/deploy/hackleytechangels.org.sh.
# The GitHub webhook (public/gitwebhook.php) runs the copy OUTSIDE the checkout,
# ~/deploy/hackleytechangels.org.sh, so it cannot change under its own feet.
# After editing this file, refresh that copy:
#   cp ~/deploy/hackleytechangels.org/deploy/hackleytechangels.org.sh ~/deploy/hackleytechangels.org.sh
#
# Run by hand:  bash ~/deploy/hackleytechangels.org.sh
# See README "Deploying" for the one-time setup.

set -euo pipefail
# never fail silently: report the line that aborted the run
trap 'echo "ERROR: deploy aborted at line $LINENO (exit status $?). The live site is unchanged unless the swap (last step) was reached." >&2' ERR

# php-fpm gives the webhook a minimal environment; make sure git and php resolve
# and HOME is set (nvm and npm need it).
export PATH="/usr/local/bin:/usr/bin:/bin:${PATH:-}"
HOME="${HOME:-$(getent passwd "$(id -un)" | cut -d: -f6)}"
export HOME

# ---- layout (every value can be overridden by exporting it before running) ----
SITE_HOME="${SITE_HOME:-$HOME}"
REPO_DIR="${REPO_DIR:-$SITE_HOME/deploy/hackleytechangels.org}"
SECRETS_DIR="${SECRETS_DIR:-$SITE_HOME/deploy/hackleytechangels.org.secrets}"
BRANCH="${BRANCH:-main}"

WEB_ROOT="${WEB_ROOT:-$SITE_HOME/hackleytechangels.org}"
OLD_ROOT="$WEB_ROOT.old"
NEW_ROOT="$WEB_ROOT.new"            # staging dir, swapped into place at the end

export NVM_DIR="${NVM_DIR:-$SITE_HOME/.nvm}"
NODE_VERSION="${NODE_VERSION:-22}"
# -----------------------------------------------------------------------------

log()  { printf '==> %s\n' "$*"; }
die()  { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

[ "$(id -u)" -ne 0 ] || die "run as the site user, not root"

# ---- preflight: fail before touching anything --------------------------------
[ -d "$REPO_DIR/.git" ]                 || die "no git clone at $REPO_DIR"
[ -f "$SECRETS_DIR/config.local.php" ]  || die "missing $SECRETS_DIR/config.local.php (copy public/config.local.php.example there and fill it in)"
[ -s "$NVM_DIR/nvm.sh" ]                || die "nvm.sh not found at $NVM_DIR/nvm.sh"
command -v git >/dev/null 2>&1          || die "git not found in PATH"
command -v php >/dev/null 2>&1          || die "php not found in PATH"
php -l "$SECRETS_DIR/config.local.php" >/dev/null || die "$SECRETS_DIR/config.local.php has a syntax error"
php -r 'require $argv[1]; exit(defined("WEBHOOK_SECRET") ? 0 : 1);' "$SECRETS_DIR/config.local.php" \
    || die "$SECRETS_DIR/config.local.php does not define WEBHOOK_SECRET (is it the old array-style file? see public/config.local.php.example)"
php -r 'require $argv[1]; exit(defined("CONTACT_TO") && CONTACT_TO && defined("SMTP_PASS") && SMTP_PASS !== "" ? 0 : 1);' "$SECRETS_DIR/config.local.php" \
    || echo "WARNING: CONTACT_TO / SMTP_* are not filled in; the contact form will say the inbox is not connected" >&2

# nvm's scripts are not written for `set -u` / an ERR trap
set +u; trap - ERR
# shellcheck disable=SC1091
. "$NVM_DIR/nvm.sh"
nvm use "$NODE_VERSION" >/dev/null || die "nvm has no Node $NODE_VERSION (nvm install $NODE_VERSION)"
set -u
trap 'echo "ERROR: deploy aborted at line $LINENO (exit status $?). The live site is unchanged unless the swap (last step) was reached." >&2' ERR
log "node $(node -v), npm $(npm -v)"

# ---- 1. update the clone -----------------------------------------------------
log "updating $REPO_DIR ($BRANCH)"
git -C "$REPO_DIR" fetch --quiet --prune origin
git -C "$REPO_DIR" checkout --quiet "$BRANCH"
git -C "$REPO_DIR" reset --quiet --hard "origin/$BRANCH"
REV="$(git -C "$REPO_DIR" rev-parse --short HEAD)"
log "clone is at $REV"

# ---- 2. build ----------------------------------------------------------------
log "building"
cd "$REPO_DIR"
npm ci --no-audit --no-fund
npm run build
[ -s "$REPO_DIR/dist/index.html" ]   || die "build produced no dist/index.html"
[ -f "$REPO_DIR/dist/contact.php" ]  || die "build produced no dist/contact.php"

# ---- 3. stage the new web root -----------------------------------------------
log "staging $NEW_ROOT"
rm -rf "$NEW_ROOT"
mv "$REPO_DIR/dist" "$NEW_ROOT"
find "$NEW_ROOT" -type d -exec chmod 0755 {} +
find "$NEW_ROOT" -type f -exec chmod 0644 {} +

# config.local.php: secrets, readable by this user only (the secrets copy is the master)
install -m 0600 "$SECRETS_DIR/config.local.php" "$NEW_ROOT/config.local.php"

# carry over a Let's Encrypt challenge dir if the current root has one
if [ -d "$WEB_ROOT/.well-known" ]; then
    cp -a "$WEB_ROOT/.well-known" "$NEW_ROOT/"
fi

# record what was deployed
printf 'deployed %s from %s@%s on %s\n' "$REV" "$REPO_DIR" "$BRANCH" "$(date '+%Y-%m-%dT%H:%M:%S%z')" > "$NEW_ROOT/DEPLOYED"

# ---- 4. swap: current root -> OLD_ROOT, staging -> live ----------------------
log "replacing $OLD_ROOT with the current $WEB_ROOT"
rm -rf "$OLD_ROOT"
if [ -e "$WEB_ROOT" ]; then
    mv "$WEB_ROOT" "$OLD_ROOT"
fi
mv "$NEW_ROOT" "$WEB_ROOT"

log "deployed $REV to $WEB_ROOT (previous root is in $OLD_ROOT)"
