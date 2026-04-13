function initFeedback(viewId) {
    if (!viewId) return;

    var currentSlide = 1;
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
    var slideSelect = document.getElementById('feedback-slide-select');

    if (!toggleBtn || !panel) return;

    // --- Slide picker: populate with slide numbers ---
    function populateSlideSelect(total) {
        if (!slideSelect) return;
        var current = slideSelect.value;
        slideSelect.innerHTML = '';
        var count = total || 20; // default max if unknown
        for (var i = 1; i <= count; i++) {
            var opt = document.createElement('option');
            opt.value = i;
            opt.textContent = i;
            slideSelect.appendChild(opt);
        }
        if (current) slideSelect.value = current;
    }
    populateSlideSelect(20);

    // When user changes the slide picker, update currentSlide
    if (slideSelect) {
        slideSelect.addEventListener('change', function () {
            currentSlide = parseInt(this.value) || 1;
            updateSlideLabel();
            renderPrior();
        });
    }

    // --- Auto-detect current slide ---
    // Method 1: postMessage from iframe tracking script
    window.addEventListener('message', function (e) {
        if (e.data && e.data.type === 'showroom_slide') {
            onSlideDetected(e.data.slide, e.data.total);
        }
    });

    // Method 2: localStorage (written by tracking script inside iframe)
    setInterval(function () {
        try {
            var raw = localStorage.getItem('showroom_current_slide');
            if (!raw) return;
            var data = JSON.parse(raw);
            if (data.slide && data.slide > 0) onSlideDetected(data.slide, data.total);
        } catch (e) {}
    }, 500);

    function onSlideDetected(slide, total) {
        if (typeof slide !== 'number' || slide < 1) return;
        if (total && slideSelect && slideSelect.options.length !== total) {
            populateSlideSelect(total);
        }
        if (slide === currentSlide) return;
        currentSlide = slide;
        if (slideSelect) slideSelect.value = slide;
        if (panelOpen) { updateSlideLabel(); renderPrior(); }
    }

    // --- Toggle panel ---
    toggleBtn.addEventListener('click', function () {
        if (panelOpen) closePanel(); else openPanel();
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
        panelSlideLabel.textContent = 'Feedback for Slide ' + currentSlide;
    }

    // --- Load all feedback for deck (own + others) ---
    function loadPriorFeedback() {
        panelPrior.innerHTML = '';

        fetch('/api/feedback/all?view_id=' + viewId)
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (!data.ok) return;

                var pendingItems = [];
                Object.keys(feedbackCache).forEach(function (slide) {
                    feedbackCache[slide].forEach(function (f) {
                        if (f._pending) pendingItems.push({ slide: parseInt(slide), item: f });
                    });
                });

                feedbackCache = {};
                data.feedback.forEach(function (f) {
                    if (!feedbackCache[f.slide_number]) feedbackCache[f.slide_number] = [];
                    feedbackCache[f.slide_number].push(f);
                });

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
            panelPrior.querySelectorAll('.feedback-delete-btn').forEach(function (btn) {
                btn.addEventListener('click', function () {
                    deleteFeedback(parseInt(this.dataset.id));
                });
            });
        }

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

        // Read slide from the picker (always accurate)
        var slideAtSubmit = slideSelect ? parseInt(slideSelect.value) || currentSlide : currentSlide;
        var tempId = '_temp_' + Math.random().toString(36).slice(2);

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
        showConfirmation(slideAtSubmit);

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
        var existing = panel.querySelector('.feedback-error');
        if (existing) existing.remove();

        var errDiv = document.createElement('div');
        errDiv.className = 'feedback-error';
        errDiv.textContent = message;

        var inputRow = panelInput.parentElement;
        inputRow.parentElement.insertBefore(errDiv, inputRow.nextSibling);

        setTimeout(function () {
            if (errDiv.parentElement) errDiv.remove();
        }, 4000);
    }

    function showConfirmation(slide) {
        panelConfirm.style.display = 'flex';
        panelConfirm.querySelector('.feedback-confirm-text').textContent =
            'Thanks for your feedback on Slide ' + slide + '!';

        setTimeout(function () {
            panelConfirm.style.display = 'none';
            renderPrior();
            panelInput.focus();
        }, 3000);
    }

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

    function deleteFeedback(feedbackId) {
        fetch('/api/feedback/' + feedbackId, { method: 'DELETE' })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.ok) {
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
