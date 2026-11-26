<?php
// Dependency-free SMTP client, ported from neon.everosenthal.com's _mailer.php
// (itself from portal.bronxconservatory.org's mailer.php). Same config
// constants: SMTP_HOST/PORT/SECURE/USER/PASS, SMTP_FROM_EMAIL/SMTP_FROM_NAME.
// Supports implicit SSL (465) and STARTTLS (587), AUTH LOGIN, plain-text body.
//
// Include-only: contact.php defines HTA_MAILER before requiring it, and
// .htaccess denies direct requests.
declare(strict_types=1);

defined('HTA_MAILER') or exit;

/** Removes anything that could start a new header line. */
function mail_header_safe(string $value): string
{
    return trim(preg_replace('/[\r\n\x00-\x1F\x7F]+/', ' ', $value) ?? '');
}

/**
 * Sends one plain-text message. $replyToEmail (already validated by the
 * caller) is where a reply to the message goes. Returns false and sets
 * $errorMessage on any failure.
 */
function send_smtp_mail(
    string $toEmail,
    string $subject,
    string $text,
    string $replyToEmail = '',
    string $replyToName = '',
    string &$errorMessage = ''
): bool {
    if (!defined('SMTP_HOST') || !defined('SMTP_PORT') || !defined('SMTP_USER') || !defined('SMTP_PASS')
        || SMTP_HOST === '' || SMTP_USER === '' || SMTP_PASS === '') {
        $errorMessage = 'SMTP configuration missing';
        return false;
    }

    $host = (string)SMTP_HOST;
    $port = (int)SMTP_PORT;
    $secure = defined('SMTP_SECURE') ? strtolower((string)SMTP_SECURE) : 'tls';
    $fromEmail = defined('SMTP_FROM_EMAIL') && SMTP_FROM_EMAIL ? (string)SMTP_FROM_EMAIL : (string)SMTP_USER;
    $fromName = defined('SMTP_FROM_NAME') && SMTP_FROM_NAME ? (string)SMTP_FROM_NAME : 'Hackley Tech Angels website';

    $toEmail = mail_header_safe($toEmail);
    $subject = mail_header_safe($subject);
    $replyToEmail = mail_header_safe($replyToEmail);
    $replyToName = mail_header_safe($replyToName);

    $timeout = 20;
    $transport = ($secure === 'ssl') ? "ssl://$host" : $host;
    $fp = @stream_socket_client("$transport:$port", $errno, $errstr, $timeout, STREAM_CLIENT_CONNECT);
    if (!$fp) {
        $errorMessage = "Failed to connect to $host:$port - $errstr ($errno)";
        return false;
    }
    stream_set_timeout($fp, $timeout);

    $lastResponse = '';
    $expect = function (array $codes) use ($fp, &$lastResponse): bool {
        do {
            $line = fgets($fp, 515);
            if ($line === false) {
                $lastResponse = 'Connection lost or timeout';
                return false;
            }
            $lastResponse = trim($line);
            $code = (int)substr($line, 0, 3);
            $more = isset($line[3]) && $line[3] === '-';
        } while ($more);
        return in_array($code, $codes, true);
    };
    $send = function (string $cmd) use ($fp): bool {
        return fwrite($fp, $cmd . "\r\n") !== false;
    };
    $fail = function (string $step) use ($fp, &$errorMessage, &$lastResponse): bool {
        $errorMessage = "$step failed: $lastResponse";
        fclose($fp);
        return false;
    };

    if (!$expect([220])) return $fail('SMTP greeting');

    $ehloName = preg_replace('/[^A-Za-z0-9.-]/', '', (string)($_SERVER['SERVER_NAME'] ?? '')) ?: 'localhost';
    if (!$send("EHLO $ehloName") || !$expect([250])) return $fail('EHLO');

    if ($secure === 'tls') {
        if (!$send('STARTTLS') || !$expect([220])) return $fail('STARTTLS');
        if (!stream_socket_enable_crypto($fp, true, STREAM_CRYPTO_METHOD_TLS_CLIENT)) return $fail('TLS negotiation');
        if (!$send("EHLO $ehloName") || !$expect([250])) return $fail('EHLO after STARTTLS');
    }

    if (!$send('AUTH LOGIN') || !$expect([334])) return $fail('AUTH LOGIN');
    if (!$send(base64_encode((string)SMTP_USER)) || !$expect([334])) return $fail('SMTP username');
    if (!$send(base64_encode((string)SMTP_PASS)) || !$expect([235])) return $fail('SMTP password');

    if (!$send("MAIL FROM:<$fromEmail>") || !$expect([250])) return $fail('MAIL FROM');
    if (!$send("RCPT TO:<$toEmail>") || !$expect([250, 251])) return $fail('RCPT TO');
    if (!$send('DATA') || !$expect([354])) return $fail('DATA');

    $fromDomain = substr((string)strrchr($fromEmail, '@'), 1) ?: 'localhost';
    $headers = [
        'Date: ' . date('r'),
        'From: ' . mb_encode_mimeheader($fromName) . " <{$fromEmail}>",
        "To: <{$toEmail}>",
        'Subject: ' . mb_encode_mimeheader($subject),
        'Message-ID: <' . bin2hex(random_bytes(16)) . '@' . $fromDomain . '>',
        'MIME-Version: 1.0',
        'Content-Type: text/plain; charset=UTF-8',
        'Content-Transfer-Encoding: 8bit',
    ];
    if ($replyToEmail !== '') {
        $name = $replyToName !== '' ? mb_encode_mimeheader($replyToName) . ' ' : '';
        $headers[] = "Reply-To: {$name}<{$replyToEmail}>";
    }

    // Normalize newlines and dot-stuff the body.
    $body = preg_replace("/\r\n|\r|\n/", "\r\n", $text);
    $body = preg_replace('/^\./m', '..', $body);

    $data = implode("\r\n", $headers) . "\r\n\r\n" . $body . "\r\n.";
    if (!$send($data) || !$expect([250])) return $fail('Message data');

    $send('QUIT');
    fclose($fp);
    return true;
}
