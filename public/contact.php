<?php
// Contact form endpoint. The form on the Contact page (src/components/Contact.astro,
// src/scripts/contact.ts) POSTs name, email, topic, message here and gets JSON back:
//   200 {"ok":true}
//   4xx/5xx {"ok":false,"error":"<code>"}   codes: method, invalid, rate, unconfigured, send
// The message is emailed to CONTACT_TO through the SMTP account in
// config.local.php, with the visitor in Reply-To. Nothing is stored.
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

function respond(int $status, array $body): never
{
    http_response_code($status);
    echo json_encode($body), "\n";
    exit;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    header('Allow: POST');
    respond(405, ['ok' => false, 'error' => 'method']);
}

// Same-origin only: a browser form on another site cannot use this as a relay.
$origin = (string)($_SERVER['HTTP_ORIGIN'] ?? '');
if ($origin !== '' && parse_url($origin, PHP_URL_HOST) !== preg_replace('/:\d+$/', '', (string)($_SERVER['HTTP_HOST'] ?? ''))) {
    respond(403, ['ok' => false, 'error' => 'invalid']);
}

$field = static fn(string $k): string => trim((string)($_POST[$k] ?? ''));
$name = $field('name');
$email = $field('email');
$topic = $field('topic');
$message = $field('message');

// Honeypot: a field people never see. Bots that fill it get a quiet "ok".
if ($field('website') !== '') {
    respond(200, ['ok' => true]);
}

$topics = ['Join the Angels', 'Pitch a project', 'Collaborate', 'Something else'];
if (!in_array($topic, $topics, true)) {
    $topic = 'Something else';
}
if ($name === '' || mb_strlen($name) > 100
    || $message === '' || mb_strlen($message) > 5000
    || mb_strlen($email) > 200 || filter_var($email, FILTER_VALIDATE_EMAIL) === false
    || preg_match('/[\r\n]/', $name . $email)) {
    respond(422, ['ok' => false, 'error' => 'invalid']);
}

$configFile = __DIR__ . '/config.local.php';
if (is_readable($configFile)) {
    require_once $configFile;
}
$to = defined('CONTACT_TO') ? array_values(array_filter((array)CONTACT_TO)) : [];
if (!$to || !defined('SMTP_HOST') || !defined('SMTP_USER') || !defined('SMTP_PASS')
    || SMTP_HOST === '' || SMTP_USER === '' || SMTP_PASS === '') {
    respond(503, ['ok' => false, 'error' => 'unconfigured']);
}

// Rate limit: at most 5 messages per address per hour, counted in a small file
// in the system temp directory (the site has no database).
$ip = (string)($_SERVER['REMOTE_ADDR'] ?? 'unknown');
$window = 3600;
$limit = 5;
$rateFile = sys_get_temp_dir() . '/hackleytechangels-contact-' . hash('sha256', $ip) . '.json';
$now = time();
$hits = [];
if (is_file($rateFile)) {
    $saved = json_decode((string)@file_get_contents($rateFile), true);
    if (is_array($saved)) {
        $hits = array_values(array_filter($saved, static fn($t) => is_int($t) && $t > $now - $window));
    }
}
if (count($hits) >= $limit) {
    header('Retry-After: ' . $window);
    respond(429, ['ok' => false, 'error' => 'rate']);
}
$hits[] = $now;
@file_put_contents($rateFile, json_encode($hits), LOCK_EX);

define('HTA_MAILER', true);
require __DIR__ . '/mailer.php';

$subject = "[Tech Angels] $topic — $name";
$text = $message . "\n\n— $name ($email)\n\nSent from the contact form at hackleytechangels.org. Reply to this email to answer them.\n";

$sent = 0;
$error = '';
foreach ($to as $recipient) {
    if (send_smtp_mail((string)$recipient, $subject, $text, $email, $name, $error)) {
        $sent++;
    } else {
        error_log("contact.php: could not send to $recipient: $error");
    }
}
if ($sent === 0) {
    respond(502, ['ok' => false, 'error' => 'send']);
}
respond(200, ['ok' => true]);
