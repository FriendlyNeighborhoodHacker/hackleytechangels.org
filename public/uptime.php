<?php
declare(strict_types=1);

/**
 * Uptime check for external monitors (HetrixTools, a cron curl, ...).
 *
 * Proves the whole request path works: DNS -> Apache -> PHP -> the web root
 * holding a finished Astro build. Point the monitor at
 *   https://hackleytechangels.org/uptime.php
 * and have it alert on anything other than HTTP 200 or a body that does not
 * start with "success".
 *
 * Responses (text/plain, never cached):
 *   200  success : 2026-11-05 14:03:21 EST
 *   503  failure : 2026-11-05 14:03:21 EST : <what went wrong>
 *
 * The site is static and has no database, so the only thing that can be wrong
 * on the server side is the deploy itself: deploy/hackleytechangels.org.sh swaps the whole
 * web root for a fresh dist/, and a build that died halfway, or a web root that
 * was never populated, leaves no (or a truncated) index.html. That is what
 * this checks. It does not send mail, so the contact form's SMTP account is
 * not probed here.
 */

header('Content-Type: text/plain; charset=utf-8');
header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');
header('Pragma: no-cache');

date_default_timezone_set('America/New_York');

try {
    $index = __DIR__ . '/index.html';
    if (!is_file($index)) {
        throw new \RuntimeException('index.html not found in web root');
    }
    if (!is_readable($index)) {
        throw new \RuntimeException('index.html is not readable');
    }
    $html = file_get_contents($index);
    if ($html === false || $html === '') {
        throw new \RuntimeException('index.html is empty');
    }
    // A build that was cut off mid-write has no closing tag.
    if (stripos($html, '</html>') === false) {
        throw new \RuntimeException('index.html is truncated (no </html>)');
    }

    echo 'success : ' . date('Y-m-d H:i:s T') . "\n";
} catch (\Throwable $e) {
    http_response_code(503);
    echo 'failure : ' . date('Y-m-d H:i:s T') . ' : ' . $e->getMessage() . "\n";
}
