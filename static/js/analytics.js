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

function loadAnalytics(deckId) {
    fetch('/admin/api/analytics/' + deckId)
        .then(function (r) { return r.json(); })
        .then(function (data) {
            // Summary
            document.getElementById('stat-views').textContent = data.summary.total_views;
            document.getElementById('stat-unique').textContent = data.summary.unique_viewers;
            document.getElementById('stat-avg-time').textContent = formatDuration(data.summary.avg_duration);
            document.getElementById('stat-forwarded').textContent = data.summary.forwarded_views;

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
                tbody.innerHTML = '<tr><td colspan="6" class="muted">No views yet</td></tr>';
                return;
            }
            var rows = '';
            data.views.forEach(function (v) {
                rows += '<tr>' +
                    '<td>' + v.viewer_email + '</td>' +
                    '<td>' + v.shared_with + '</td>' +
                    '<td>' + (v.is_forwarded ? '<span class="badge badge-inactive">Forwarded</span>' : '—') + '</td>' +
                    '<td>' + formatDuration(v.duration_seconds) + '</td>' +
                    '<td>' + v.viewed_at + '</td>' +
                    '<td>' + parseUA(v.user_agent) + '</td>' +
                    '</tr>';
            });
            tbody.innerHTML = rows;
        })
        .catch(function (err) {
            console.error('Failed to load analytics:', err);
        });
}
