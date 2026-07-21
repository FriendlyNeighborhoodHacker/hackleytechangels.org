<?php

// /var/www/myapp/webhook.php

// Secrets live in config.local.php, which is gitignored. Copy
// config.local.php.example to config.local.php and fill it in on each machine.
$configFile = __DIR__ . '/config.local.php';

if (!is_readable($configFile)) {
    http_response_code(500);
    echo "Server misconfigured\n";
    error_log('gitwebhook: missing config.local.php (copy config.local.php.example)');
    exit;
}

$config = require $configFile;

if (empty($config['webhook_secret'])) {
    http_response_code(500);
    echo "Server misconfigured\n";
    error_log('gitwebhook: webhook_secret is not set in config.local.php');
    exit;
}

$secret = $config['webhook_secret'];

$deployScript = '/home/lillyjane/deploy_scripts/hackleytechangels.org.deploy.sh';
$logFile = '/home/lillyjane/deploy_scripts/hackleytechangels.org.deploy.log';

$payload = file_get_contents('php://input');
$signature = $_SERVER['HTTP_X_HUB_SIGNATURE_256'] ?? '';
$event = $_SERVER['HTTP_X_GITHUB_EVENT'] ?? '';


function logMessage(string $logFile, string $message): void
{
  $timestamp = date('Y-m-d H:i:s');
  file_put_contents($logFile, "[$timestamp] $message/n", FILE_APPEND);
}

if (!$payload || !$signature) {
    http_response_code(400);
    echo "Missing payload or signature\n";
    logMessage($logFile, "Missing payload or signature");
    exit;
}

$expected = 'sha256=' . hash_hmac('sha256', $payload, $secret);

if (!hash_equals($expected, $signature)) {
    http_response_code(403);
    echo "Invalid signature\n";
    logMessage($logFile, "Invalid signature");
    exit;
}

if ($event !== 'push') {
    http_response_code(200);
    echo "Ignored non-push event\n";
    exit;
}

// Run deploy script and capture output
$output = [];
$returnVar = 0;
exec($deployScript . ' 2>&1', $output, $returnVar);

if ($returnVar !== 0) {
    http_response_code(500);
    echo "Deploy failed\n";
    echo implode("\n", $output);
    logMessage($logFile, "Deploy failed");
    logMessage($logFile, implode("\n", $output));
    exit;
}

http_response_code(200);
logMessage($logFile, 'Deploy Successful');
echo "Deploy successful\n";
echo implode("\n", $output);

