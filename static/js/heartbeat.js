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
    window.addEventListener('message', function (e) {
        if (e.data && e.data.type === 'showroom_slide') {
            updateSlide(e.data.slide, e.data.total);
        }
    });

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

    // Fallback: poll iframe DOM directly if postMessage isn't working
    function pollIframe() {
        if (currentSlide) return;
        try {
            var iframe = document.getElementById('deck-frame');
            if (!iframe || !iframe.contentDocument) return;
            var doc = iframe.contentDocument;
            var active = doc.querySelector('.slide.active[data-slide]');
            if (active) {
                var val = parseInt(active.dataset.slide);
                var first = doc.querySelector('.slide[data-slide]');
                var zeroIndexed = first && parseInt(first.dataset.slide) === 0;
                var slide = zeroIndexed ? val + 1 : val;
                var total = doc.querySelectorAll('.slide[data-slide]').length || doc.querySelectorAll('.slide').length || null;
                updateSlide(slide, total);
            }
        } catch (e) { /* cross-origin or not loaded */ }
    }
    var iframePollCount = 0;
    var iframePollTimer = setInterval(function () {
        pollIframe();
        iframePollCount++;
        if (currentSlide || iframePollCount >= 10) clearInterval(iframePollTimer);
    }, 1000);

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
