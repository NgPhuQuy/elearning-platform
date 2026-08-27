document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById("courseSearch");
  const levelFilters = document.querySelectorAll(".level-filter");
  const categoryFilter = document.getElementById("categoryFilter");
  const items = document.querySelectorAll("#courseGrid .course-item");

  function applyFilters() {
    const keyword = (searchInput.value || "").trim().toLowerCase();

        const checkedLevel = document.querySelector(".level-filter:checked");
    const level = checkedLevel ? checkedLevel.value : "ALL";

    const category = categoryFilter ? categoryFilter.value : "ALL";

    items.forEach(function (item) {
      const name = item.dataset.name || "";
      const teacher = item.dataset.teacher || "";
      const itemLevel = item.dataset.level || "";
      const itemCategories = (item.dataset.categories || "")
        .split(",")
        .map(function (c) { return c.trim(); })
        .filter(Boolean);

      const matchesKeyword =
        keyword === "" ||
        name.includes(keyword) ||
        teacher.includes(keyword);

      const matchesLevel = level === "ALL" || itemLevel === level;

      const matchesCategory =
        category === "ALL" || itemCategories.includes(category);

      item.style.display =
        matchesKeyword && matchesLevel && matchesCategory ? "" : "none";
    });
  }

  if (searchInput) {
    searchInput.addEventListener("input", applyFilters);
  }

    levelFilters.forEach(function (radio) {
    radio.addEventListener("change", applyFilters);
  });

  if (categoryFilter) {
    categoryFilter.addEventListener("change", applyFilters);
  }
});