document.addEventListener("DOMContentLoaded", () => {

    const categorySelect = document.querySelector("#category-select");

    if (!categorySelect)
        return;

    new TomSelect(categorySelect, {

        plugins: [
            "remove_button"
        ],

        maxItems: null,

        create: false,

        closeAfterSelect: true,

        hideSelected: true,

        persist: false,

        placeholder: "Nhập để tìm danh mục...",

        render: {

            item(data, escape) {
                return `
                    <div class="badge rounded-pill bg-primary px-3 py-2 me-1">
                        ${escape(data.text)}
                    </div>
                `;
            }

        }

    });

});