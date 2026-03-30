function startHeartbeat(viewId) {
    if (!viewId) return;

    let startTime = Date.now();
    let elapsed = 0;
    let paused = false;
    let pauseStart = 0;
    let totalPaused = 0;

    // Pause timer when tab is hidden
    document.addEventListener('visibilitychange', function () {
        if (document.hidden) {
            paused = true;
            pauseStart = Date.now();
        } else {
            if (paused && pauseStart) {
                totalPaused += Date.now() - pauseStart;
            }
            paused = false;
        }
    });

    function getElapsed() {
        if (paused) {
            return Math.round((pauseStart - startTime - totalPaused) / 1000);
        }
        return Math.round((Date.now() - startTime - totalPaused) / 1000);
    }

    function sendPing() {
        elapsed = getElapsed();
        if (elapsed <= 0) return;

        fetch('/api/heartbeat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ view_id: viewId, duration: elapsed }),
        }).catch(function () { /* silent */ });
    }

    // Send heartbeat every 5 seconds
    setInterval(sendPing, 5000);

    // Final ping on page unload
    window.addEventListener('beforeunload', function () {
        elapsed = getElapsed();
        if (elapsed > 0 && navigator.sendBeacon) {
            navigator.sendBeacon(
                '/api/heartbeat',
                new Blob(
                    [JSON.stringify({ view_id: viewId, duration: elapsed })],
                    { type: 'application/json' }
                )
            );
        }
    });
}
