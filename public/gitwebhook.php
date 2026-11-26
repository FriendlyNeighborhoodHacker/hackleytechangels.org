<?php
// GitHub push webhook: verifies the signature and runs the deploy script.
//
// Served at https://hackleytechangels.org/gitwebhook.php. GitHub -> repo ->
// Settings -> Webhooks: payload URL above, content type application/json,
// Secret = WEBHOOK_SECRET, "Just the push event". A push to WEBHOOK_BRANCH runs
// DEPLOY_SCRIPT (~/deploy/hackleytechangels.org.sh, the copy of
// deploy/hackleytechangels.org.sh kept outside the checkout) and appends the
// output to DEPLOY_LOG. Both constants live in config.local.php, which the
// deploy script installs next to this file from the secrets directory.
//
// Deliberately standalone: it needs nothing but config.local.php,
// so a broken deploy can still be re-triggered by a push.
declare(strict_types=1);

$configFile = __DIR__ . '/config.local.php';
if (!is_readable($configFile)) {
    http_response_code(500);
    echo "Server misconfigured\n";
    error_log('gitwebhook: missing config.local.php (copy config.local.php.example)');
    exit;
}
require_once $configFile;

$secret = defined('WEBHOOK_SECRET') ? (string)WEBHOOK_SECRET : '';
if ($secret === '') {
    http_response_code(500);
    echo "Server misconfigured\n";
    error_log('gitwebhook: WEBHOOK_SECRET is not set in config.local.php');
    exit;
}
$deployScript = defined('DEPLOY_SCRIPT') ? (string)DEPLOY_SCRIPT : dirname(__DIR__) . '/deploy/hackleytechangels.org.sh';
$logFile = defined('DEPLOY_LOG') ? (string)DEPLOY_LOG : dirname(__DIR__) . '/deploy/hackleytechangels.org.deploy.log';
$branch = defined('WEBHOOK_BRANCH') ? (string)WEBHOOK_BRANCH : 'main';

function logMessage(string $logFile, string $message): void {
    @file_put_contents($logFile, '[' . date('Y-m-d H:i:s') . '] ' . $message . "\n", FILE_APPEND | LOCK_EX);
}

$payload = (string)file_get_contents('php://input');
$signature = (string)($_SERVER['HTTP_X_HUB_SIGNATURE_256'] ?? '');
$event = (string)($_SERVER['HTTP_X_GITHUB_EVENT'] ?? '');

if ($payload === '' || $signature === '') {
    http_response_code(400);
    echo "Missing payload or signature\n";
    logMessage($logFile, 'Missing payload or signature');
    exit;
}

$expected = 'sha256=' . hash_hmac('sha256', $payload, $secret);
if (!hash_equals($expected, $signature)) {
    http_response_code(403);
    echo "Invalid signature\n";
    logMessage($logFile, 'Invalid signature from ' . ($_SERVER['REMOTE_ADDR'] ?? 'unknown'));
    exit;
}

if ($event !== 'push') {
    http_response_code(200);
    echo "Ignored $event event\n";
    exit;
}

$data = json_decode($payload, true);
$ref = is_array($data) ? (string)($data['ref'] ?? '') : '';
if ($ref !== '' && $ref !== 'refs/heads/' . $branch) {
    http_response_code(200);
    echo "Ignored push to $ref\n";
    logMessage($logFile, "Ignored push to $ref");
    exit;
}

if (!is_file($deployScript)) {
    http_response_code(500);
    echo "Deploy script not found\n";
    logMessage($logFile, 'Deploy script not found: ' . $deployScript);
    exit;
}

logMessage($logFile, 'Deploy started (' . substr((string)($data['after'] ?? ''), 0, 8) . ' pushed by ' . ($data['pusher']['name'] ?? '?') . ')');
$output = [];
$returnVar = 0;
exec('/bin/bash ' . escapeshellarg($deployScript) . ' 2>&1', $output, $returnVar);

if ($returnVar !== 0) {
    http_response_code(500);
    echo "Deploy failed\n" . implode("\n", $output) . "\n";
    logMessage($logFile, "Deploy failed (exit $returnVar)\n" . implode("\n", $output));
    exit;
}

http_response_code(200);
logMessage($logFile, "Deploy successful\n" . implode("\n", $output));
echo "Deploy successful\n" . implode("\n", $output) . "\n";
