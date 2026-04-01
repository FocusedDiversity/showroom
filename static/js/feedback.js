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

    // --- Listen for slide changes from heartbeat ---
    window.addEventListener('message', function (e) {
        if (e.data && e.data.type === 'showroom_slide') {
            currentSlide = e.data.slide;
            if (panelOpen) {
                updateSlideLabel();
                loadPriorFeedback();
            }
        }
    });

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

    // --- Load prior feedback for current slide ---
    function loadPriorFeedback() {
        panelPrior.innerHTML = '';

        fetch('/api/feedback?view_id=' + viewId)
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (!data.ok) return;

                // Cache all feedback
                feedbackCache = {};
                data.feedback.forEach(function (f) {
                    if (!feedbackCache[f.slide_number]) feedbackCache[f.slide_number] = [];
                    feedbackCache[f.slide_number].push(f);
                });

                renderPrior();
            })
            .catch(function () { /* silent */ });
    }

    function renderPrior() {
        panelPrior.innerHTML = '';
        var items = feedbackCache[currentSlide] || [];

        if (items.length === 0) {
            var empty = document.createElement('p');
            empty.className = 'feedback-prior-empty';
            empty.textContent = 'No feedback on this slide yet.';
            panelPrior.appendChild(empty);
        } else {
            items.forEach(function (f) {
                var div = document.createElement('div');
                div.className = 'feedback-prior-item';
                div.innerHTML = '<p class="feedback-prior-text">' + escapeHtml(f.comment) + '</p>' +
                    '<span class="feedback-prior-time">You, ' + timeAgo(f.created_at) + '</span>';
                panelPrior.appendChild(div);
            });
        }

        // Update input placeholder
        panelInput.placeholder = items.length > 0
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
        if (!comment || !currentSlide) return;

        panelSend.disabled = true;

        fetch('/api/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                view_id: viewId,
                slide_number: currentSlide,
                comment: comment
            })
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            panelSend.disabled = false;
            if (data.ok) {
                // Add to cache
                if (!feedbackCache[currentSlide]) feedbackCache[currentSlide] = [];
                feedbackCache[currentSlide].push({
                    id: data.feedback_id,
                    comment: comment,
                    created_at: new Date().toISOString()
                });

                panelInput.value = '';
                showConfirmation();
            }
        })
        .catch(function () {
            panelSend.disabled = false;
        });
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
}
