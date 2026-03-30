// Admin dashboard interactions (placeholder for future enhancements)
document.addEventListener('DOMContentLoaded', function () {
    // Auto-dismiss flash messages after 5 seconds
    var flashes = document.querySelectorAll('.flash');
    flashes.forEach(function (el) {
        setTimeout(function () {
            el.style.transition = 'opacity 0.3s';
            el.style.opacity = '0';
            setTimeout(function () { el.remove(); }, 300);
        }, 5000);
    });
});
