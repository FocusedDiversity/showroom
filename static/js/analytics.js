function formatDuration(seconds) {
    if (seconds < 60) return seconds + 's';
    var m = Math.floor(seconds / 60);
    var s = seconds % 60;
    return m + 'm ' + s + 's';
}

function parseUA(ua) {
    if (!ua) return 'Unknown';
    if (ua.indexOf('Mobile') !== -1) return 'Mobile';
    if (ua.indexOf('Tablet') !== -1) return 'Tablet';
    return 'Desktop';
}

function escapeHtml(str) {
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function loadAnalytics(deckId) {
    // Tab switching
    var tabs = document.querySelectorAll('.analytics-tab');
    var tabContents = document.querySelectorAll('.analytics-tab-content');
    tabs.forEach(function (tab) {
        tab.addEventListener('click', function () {
            tabs.forEach(function (t) { t.classList.remove('active'); });
            tabContents.forEach(function (c) { c.classList.remove('active'); });
            tab.classList.add('active');
            document.getElementById('tab-' + tab.dataset.tab).classList.add('active');
        });
    });

    fetch('/admin/api/analytics/' + deckId)
        .then(function (r) { return r.json(); })
        .then(function (data) {
            // Summary
            document.getElementById('stat-views').textContent = data.summary.total_views;
            document.getElementById('stat-unique').textContent = data.summary.unique_viewers;
            document.getElementById('stat-avg-time').textContent = formatDuration(data.summary.avg_duration);
            document.getElementById('stat-forwarded').textContent = data.summary.forwarded_views;
            document.getElementById('stat-feedback').textContent = data.feedback_count;

            // Chart
            var container = document.getElementById('chart-container');
            if (data.daily.length > 0) {
                var maxCount = Math.max.apply(null, data.daily.map(function (d) { return d.count; }));
                var html = '';
                data.daily.forEach(function (d) {
                    var pct = Math.max((d.count / maxCount) * 100, 4);
                    html += '<div class="chart-bar-row">' +
                        '<div class="chart-bar-label">' + d.day + '</div>' +
                        '<div class="chart-bar-track"><div class="chart-bar-fill" style="width:' + pct + '%">' +
                        '<span class="chart-bar-value">' + d.count + '</span></div></div>' +
                        '</div>';
                });
                container.innerHTML = html;
            }

            // Views table
            var tbody = document.getElementById('views-tbody');
            if (data.views.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="muted">No views yet</td></tr>';
            } else {
                var rows = '';
                data.views.forEach(function (v) {
                    var slideInfo = '—';
                    if (v.current_slide) {
                        slideInfo = v.current_slide + (v.total_slides ? ' / ' + v.total_slides : '');
                    }
                    rows += '<tr>' +
                        '<td>' + escapeHtml(v.viewer_email) + '</td>' +
                        '<td>' + escapeHtml(v.shared_with) + '</td>' +
                        '<td>' + (v.is_forwarded ? '<span class="badge badge-inactive">Forwarded</span>' : '—') + '</td>' +
                        '<td>' + formatDuration(v.duration_seconds) + '</td>' +
                        '<td>' + slideInfo + '</td>' +
                        '<td>' + v.viewed_at + '</td>' +
                        '<td>' + parseUA(v.user_agent) + '</td>' +
                        '</tr>';
                });
                tbody.innerHTML = rows;
            }

            // Feedback tab
            renderFeedback(data.feedback || []);
        })
        .catch(function (err) {
            console.error('Failed to load analytics:', err);
        });
}

function renderFeedback(feedback) {
    var emptyEl = document.getElementById('feedback-empty');
    var tableEl = document.getElementById('feedback-table');
    var filtersEl = document.getElementById('feedback-filters');
    var tbody = document.getElementById('feedback-tbody');
    var slideFilter = document.getElementById('feedback-filter-slide');
    var viewerFilter = document.getElementById('feedback-filter-viewer');

    if (feedback.length === 0) {
        emptyEl.style.display = '';
        tableEl.style.display = 'none';
        filtersEl.style.display = 'none';
        return;
    }

    emptyEl.style.display = 'none';
    tableEl.style.display = '';
    filtersEl.style.display = 'flex';

    // Populate filter options
    var slides = [];
    var viewers = [];
    feedback.forEach(function (f) {
        if (slides.indexOf(f.slide_number) === -1) slides.push(f.slide_number);
        if (viewers.indexOf(f.viewer_email) === -1) viewers.push(f.viewer_email);
    });
    slides.sort(function (a, b) { return a - b; });
    viewers.sort();

    slideFilter.innerHTML = '<option value="">All slides</option>';
    slides.forEach(function (s) {
        slideFilter.innerHTML += '<option value="' + s + '">Slide ' + s + '</option>';
    });

    viewerFilter.innerHTML = '<option value="">All viewers</option>';
    viewers.forEach(function (v) {
        viewerFilter.innerHTML += '<option value="' + escapeHtml(v) + '">' + escapeHtml(v) + '</option>';
    });

    function applyFilters() {
        var slideVal = slideFilter.value;
        var viewerVal = viewerFilter.value;

        var filtered = feedback.filter(function (f) {
            if (slideVal && f.slide_number !== parseInt(slideVal)) return false;
            if (viewerVal && f.viewer_email !== viewerVal) return false;
            return true;
        });

        var rows = '';
        if (filtered.length === 0) {
            rows = '<tr><td colspan="4" class="muted">No feedback matches filters</td></tr>';
        } else {
            filtered.forEach(function (f) {
                var date = f.created_at;
                try {
                    date = new Date(f.created_at).toLocaleDateString('en-US', {
                        year: 'numeric', month: 'short', day: 'numeric'
                    });
                } catch (e) { /* use raw */ }
                rows += '<tr>' +
                    '<td><span class="slide-badge">' + f.slide_number + '</span></td>' +
                    '<td>' + escapeHtml(f.viewer_email) + '</td>' +
                    '<td>' + escapeHtml(f.comment) + '</td>' +
                    '<td>' + date + '</td>' +
                    '</tr>';
            });
        }
        tbody.innerHTML = rows;
    }

    slideFilter.addEventListener('change', applyFilters);
    viewerFilter.addEventListener('change', applyFilters);

    // Initial render
    applyFilters();
}
