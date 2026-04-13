function initFeedback(viewId) {
    if (!viewId) return;

    var currentSlide = null;
    var panelOpen = false;
    var feedbackCache = {}; // { slideNumber: [{ id, comment, created_at }] }

    // --- DOM Elements ---
    var toggleBtn = document.getElementById('feedback-toggle');
    var panel = document.getElementById('feedback-panel');
    var panelSlideLabel = document.getElementById('feedback-slide-label');
    var panelClose = document.getElementById('feedback-close');
    var panelInput = document.getElementById('feedback-input');
    var panelSend = document.getElementById('feedback-send');
    var panelPrior = document.getElementById('feedback-prior');
    var panelConfirm = document.getElementById('feedback-confirm');

    if (!toggleBtn || !panel) return;

    // --- Detect current slide ---
    // Primary: listen for postMessage from iframe tracking script
    window.addEventListener('message', function (e) {
        if (e.data && e.data.type === 'showroom_slide') {
            currentSlide = e.data.slide;
            if (panelOpen) {
                updateSlideLabel();
                loadPriorFeedback();
            }
        }
    });

    // Fallback: continuously poll the iframe DOM for current slide
    function pollSlideFromIframe() {
        try {
            var iframe = document.getElementById('deck-frame');
            if (!iframe) return;
            var doc = iframe.contentDocument || iframe.contentWindow.document;
            if (!doc) return;
            // Method 1: active slide with data-slide
            var active = doc.querySelector('.slide.active[data-slide]');
            if (active) {
                var val = parseInt(active.dataset.slide);
                var first = doc.querySelector('.slide[data-slide]');
                var zeroIndexed = first && parseInt(first.dataset.slide) === 0;
                var detected = zeroIndexed ? val + 1 : val;
                if (detected > 0 && detected !== currentSlide) {
                    currentSlide = detected;
                    if (panelOpen) { updateSlideLabel(); loadPriorFeedback(); }
                }
                return;
            }
            // Method 2: slide indicator text
            var el = doc.getElementById('slideNum') || doc.getElementById('slideIndicator') || doc.querySelector('.slide-indicator');
            if (el) {
                var m = el.textContent.match(/(\d+)\s*\/\s*(\d+)/);
                if (m) {
                    var detected = parseInt(m[1]);
                    if (detected > 0 && detected !== currentSlide) {
                        currentSlide = detected;
                        if (panelOpen) { updateSlideLabel(); loadPriorFeedback(); }
                    }
                }
            }
        } catch (e) { /* cross-origin or not loaded yet */ }
    }
    // Poll continuously every second (handles both initial detection and slide changes)
    setInterval(pollSlideFromIframe, 1000);

    // --- Toggle panel ---
    toggleBtn.addEventListener('click', function () {
        if (panelOpen) {
            closePanel();
        } else {
            openPanel();
        }
    });

    panelClose.addEventListener('click', function () {
        closePanel();
    });

    function openPanel() {
        panelOpen = true;
        panel.classList.add('visible');
        toggleBtn.classList.add('active');
        panelConfirm.style.display = 'none';
        updateSlideLabel();
        loadPriorFeedback();
        panelInput.focus();
    }

    function closePanel() {
        panelOpen = false;
        panel.classList.remove('visible');
        toggleBtn.classList.remove('active');
        panelInput.value = '';
    }

    function updateSlideLabel() {
        panelSlideLabel.textContent = currentSlide
            ? 'Feedback for Slide ' + currentSlide
            : 'Feedback';
    }

    // --- Load all feedback for deck (own + others) ---
    function loadPriorFeedback() {
        panelPrior.innerHTML = '';

        fetch('/api/feedback/all?view_id=' + viewId)
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (!data.ok) return;

                // Collect pending optimistic entries before replacing cache
                var pendingItems = [];
                Object.keys(feedbackCache).forEach(function (slide) {
                    feedbackCache[slide].forEach(function (f) {
                        if (f._pending) pendingItems.push({ slide: parseInt(slide), item: f });
                    });
                });

                // Replace cache with server data
                feedbackCache = {};
                data.feedback.forEach(function (f) {
                    if (!feedbackCache[f.slide_number]) feedbackCache[f.slide_number] = [];
                    feedbackCache[f.slide_number].push(f);
                });

                // Re-add pending optimistic entries that aren't yet in server data
                pendingItems.forEach(function (p) {
                    if (!feedbackCache[p.slide]) feedbackCache[p.slide] = [];
                    feedbackCache[p.slide].push(p.item);
                });

                renderPrior();
            })
            .catch(function () { /* silent */ });
    }

    function renderPrior() {
        panelPrior.innerHTML = '';

        // Collect all feedback across all slides, sorted by slide number
        var allSlides = Object.keys(feedbackCache).map(Number).sort(function (a, b) { return a - b; });
        var totalItems = 0;
        allSlides.forEach(function (s) { totalItems += feedbackCache[s].length; });

        if (totalItems === 0) {
            var empty = document.createElement('p');
            empty.className = 'feedback-prior-empty';
            empty.textContent = 'No feedback yet.';
            panelPrior.appendChild(empty);
        } else {
            allSlides.forEach(function (slideNum) {
                var items = feedbackCache[slideNum];
                if (!items || items.length === 0) return;

                // Current slide items get highlighted
                var isCurrent = slideNum === currentSlide;

                items.forEach(function (f) {
                    var div = document.createElement('div');
                    var isOwn = f.is_own !== false;
                    var pendingClass = f._pending ? ' is-pending' : '';
                    var currentClass = isCurrent ? ' is-current-slide' : '';
                    div.className = 'feedback-prior-item' + (isOwn ? '' : ' is-other') + pendingClass + currentClass;
                    var authorLabel = isOwn ? 'You' : escapeHtml(f.viewer_email || '');
                    var deleteBtn = (isOwn && !f._pending && f.id && !String(f.id).startsWith('_temp'))
                        ? ' <button class="feedback-delete-btn" onclick="event.stopPropagation();" data-id="' + f.id + '" title="Delete">×</button>'
                        : '';
                    var slideTag = '<span class="feedback-slide-tag' + (isCurrent ? ' is-current' : '') + '">Slide ' + slideNum + '</span> ';
                    div.innerHTML = slideTag + '<p class="feedback-prior-text">' + escapeHtml(f.comment) + '</p>' +
                        '<span class="feedback-prior-time"><strong class="feedback-prior-author">' + authorLabel + '</strong> · ' + timeAgo(f.created_at) + deleteBtn + '</span>';
                    panelPrior.appendChild(div);
                });
            });
            // Attach delete handlers
            panelPrior.querySelectorAll('.feedback-delete-btn').forEach(function (btn) {
                btn.addEventListener('click', function () {
                    deleteFeedback(parseInt(this.dataset.id));
                });
            });
        }

        // Update input placeholder — check if viewer has own comments on this slide
        var currentItems = feedbackCache[currentSlide] || [];
        var hasOwn = currentItems.some(function (f) { return f.is_own !== false; });
        panelInput.placeholder = hasOwn
            ? 'Add another comment...'
            : 'Share your thoughts on this slide...';
    }

    // --- Submit feedback ---
    panelSend.addEventListener('click', submitFeedback);
    panelInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            submitFeedback();
        }
    });

    function submitFeedback() {
        var comment = panelInput.value.trim();
        if (!comment) return;
        // Default to slide 1 if slide detection hasn't fired yet
        if (!currentSlide) currentSlide = 1;

        var slideAtSubmit = currentSlide;
        var tempId = '_temp_' + Math.random().toString(36).slice(2);

        // Optimistic: add to cache and render immediately
        if (!feedbackCache[slideAtSubmit]) feedbackCache[slideAtSubmit] = [];
        feedbackCache[slideAtSubmit].push({
            id: tempId,
            comment: comment,
            viewer_email: 'You',
            is_own: true,
            created_at: new Date().toISOString(),
            _pending: true
        });

        panelInput.value = '';
        renderPrior();
        showConfirmation();

        // Fire API in background
        fetch('/api/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                view_id: viewId,
                slide_number: slideAtSubmit,
                comment: comment
            })
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.ok) {
                // Replace temp ID with real ID, clear pending
                var items = feedbackCache[slideAtSubmit] || [];
                for (var i = 0; i < items.length; i++) {
                    if (items[i].id === tempId) {
                        items[i].id = data.feedback_id;
                        delete items[i]._pending;
                        break;
                    }
                }
                renderPrior();
            } else {
                rollbackOptimistic(slideAtSubmit, tempId, data.error || 'Failed to save feedback.');
            }
        })
        .catch(function () {
            rollbackOptimistic(slideAtSubmit, tempId, 'Network error. Please try again.');
        });
    }

    function rollbackOptimistic(slide, tempId, errorMsg) {
        var items = feedbackCache[slide] || [];
        feedbackCache[slide] = items.filter(function (f) { return f.id !== tempId; });
        renderPrior();
        showError(errorMsg);
    }

    function showError(message) {
        // Remove any existing error
        var existing = panel.querySelector('.feedback-error');
        if (existing) existing.remove();

        var errDiv = document.createElement('div');
        errDiv.className = 'feedback-error';
        errDiv.textContent = message;

        // Insert after the input row
        var inputRow = panelInput.parentElement;
        inputRow.parentElement.insertBefore(errDiv, inputRow.nextSibling);

        setTimeout(function () {
            if (errDiv.parentElement) errDiv.remove();
        }, 4000);
    }

    // --- Confirmation ---
    function showConfirmation() {
        panelConfirm.style.display = 'flex';
        panelConfirm.querySelector('.feedback-confirm-text').textContent =
            'Thanks for your feedback on Slide ' + currentSlide + '!';

        setTimeout(function () {
            panelConfirm.style.display = 'none';
            renderPrior();
            panelInput.focus();
        }, 3000);
    }

    // --- Helpers ---
    function escapeHtml(str) {
        var div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function timeAgo(isoStr) {
        var diff = Math.floor((Date.now() - new Date(isoStr).getTime()) / 1000);
        if (diff < 60) return 'just now';
        if (diff < 3600) return Math.floor(diff / 60) + ' min ago';
        if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
        return new Date(isoStr).toLocaleDateString();
    }

    // --- Delete own feedback ---
    function deleteFeedback(feedbackId) {
        fetch('/api/feedback/' + feedbackId, { method: 'DELETE' })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.ok) {
                    // Remove from cache and re-render
                    Object.keys(feedbackCache).forEach(function (slide) {
                        feedbackCache[slide] = feedbackCache[slide].filter(function (f) {
                            return f.id !== feedbackId;
                        });
                    });
                    renderPrior();
                } else {
                    showError(data.error || 'Could not delete feedback.');
                }
            })
            .catch(function () {
                showError('Network error. Please try again.');
            });
    }
}
