function startHeartbeat(viewId) {
    if (!viewId) return;

    var startTime = Date.now();
    var elapsed = 0;
    var paused = false;
    var pauseStart = 0;
    var totalPaused = 0;
    var currentSlide = null;
    var totalSlides = null;
    var slideHistory = [];

    // Listen for slide change messages from the iframe
    var slideIndicator = document.getElementById('slide-indicator');

    // Method 1: postMessage from iframe
    window.addEventListener('message', function (e) {
        if (e.data && e.data.type === 'showroom_slide') {
            updateSlide(e.data.slide, e.data.total);
        }
    });

    // Method 2: localStorage (written by tracking script inside iframe)
    setInterval(function () {
        try {
            var raw = localStorage.getItem('showroom_current_slide');
            if (!raw) return;
            var data = JSON.parse(raw);
            if (data.slide && data.slide > 0) updateSlide(data.slide, data.total);
        } catch (e) {}
    }, 500);

    function updateSlide(slide, total) {
        if (typeof slide !== 'number' || slide < 1) return;
        if (slide === currentSlide) return;
        currentSlide = slide;
        totalSlides = total || totalSlides;
        slideHistory.push({ slide: currentSlide, time: getElapsed() });
        if (slideIndicator) {
            slideIndicator.textContent = 'Slide ' + currentSlide + (totalSlides ? ' of ' + totalSlides : '');
            slideIndicator.classList.add('visible');
        }
    }

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

    function buildPayload() {
        var payload = { view_id: viewId, duration: elapsed };
        if (currentSlide !== null) {
            payload.current_slide = currentSlide;
        }
        if (totalSlides !== null) {
            payload.total_slides = totalSlides;
        }
        return payload;
    }

    function sendPing() {
        elapsed = getElapsed();
        if (elapsed <= 0) return;

        fetch('/api/heartbeat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(buildPayload()),
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
                    [JSON.stringify(buildPayload())],
                    { type: 'application/json' }
                )
            );
        }
    });
}
