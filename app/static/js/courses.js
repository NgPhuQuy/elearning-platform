document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('courseSearch');
    const levelFilters = document.querySelectorAll('.level-filter');
    const items = document.querySelectorAll('.course-item');

    if (!searchInput || !items.length) return;

    function applyFilter() {
        const keyword = searchInput.value.trim().toLowerCase();
        const checkedLevel = document.querySelector('.level-filter:checked');
        const level = checkedLevel ? checkedLevel.value : 'ALL';

        items.forEach(function (item) {
            const matchName = item.dataset.name.includes(keyword);
            const matchLevel = level === 'ALL' || item.dataset.level === level;
            item.style.display = (matchName && matchLevel) ? '' : 'none';
        });
    }

    searchInput.addEventListener('input', applyFilter);
    levelFilters.forEach(function (radio) {
        radio.addEventListener('change', applyFilter);
    });
});