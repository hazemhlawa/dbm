document.addEventListener('DOMContentLoaded', function () {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const content = document.getElementById('content');

    sidebarToggle.addEventListener('click', function () {
        sidebar.classList.toggle('minimized');
        content.classList.toggle('minimized');
    });
});
