document.addEventListener("DOMContentLoaded", () => {
    const formOverlay = document.getElementById("add-wishlist");
    const closeFormButton = document.getElementById("close-wishlist-form");
    const cancelFormButton = document.getElementById("clear-wishlist-form");
    const form = document.getElementById("wishlist-form");
    const container = document.getElementById("wishlist-items");

    // Modal Events (Delegate listener agar tombol add di manapun berfungsi)
    document.addEventListener("click", (e) => {
        if (e.target.closest("#open-wishlist-form") || e.target.closest(".wishlist-empty-card button")) {
            if (formOverlay) {
                formOverlay.hidden = false;
                document.body.style.overflow = "hidden";
            }
        }
    });

    function closeModal() {
        if (formOverlay) {
            formOverlay.hidden = true;
            document.body.style.overflow = "";
        }
    }

    closeFormButton?.addEventListener("click", closeModal);
    cancelFormButton?.addEventListener("click", closeModal);

    formOverlay?.addEventListener("click", (e) => {
        if (e.target === formOverlay) closeModal();
    });

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && formOverlay && !formOverlay.hidden) closeModal();
    });

    // Photo Preview
    const photoInput = document.getElementById("item-photo");
    const photoPlaceholder = document.getElementById("photo-placeholder");
    const photoPreview = document.getElementById("item-photo-preview");
    const removePhotoButton = document.getElementById("remove-item-photo");

    function clearPhoto() {
        if (photoInput) photoInput.value = "";
        if (photoPreview) {
            photoPreview.hidden = true;
            photoPreview.querySelector("img").src = "";
        }
        if (photoPlaceholder) photoPlaceholder.hidden = false;
    }

    photoInput?.addEventListener("change", () => {
        const file = photoInput.files[0];
        if (!file) return clearPhoto();

        const reader = new FileReader();
        reader.onload = (e) => {
            if (photoPreview) {
                photoPreview.querySelector("img").src = e.target.result;
                photoPreview.hidden = false;
            }
            if (photoPlaceholder) photoPlaceholder.hidden = true;
        };
        reader.readAsDataURL(file);
    });

    removePhotoButton?.addEventListener("click", (e) => {
        e.preventDefault();
        clearPhoto();
    });

    // Submit Form AJAX ke Backend Django
    form?.addEventListener("submit", (e) => {
        e.preventDefault();

        const formData = new FormData(form);
        const saveBtn = document.getElementById("save-btn");
        if (saveBtn) saveBtn.textContent = "Saving...";

        fetch(form.action, {
            method: "POST",
            body: formData,
            headers: {
                "X-Requested-With": "XMLHttpRequest",
            }
        })
        .then(res => {
            if (res.ok) {
                // Refresh halaman agar backend merecalculasi match Conscious Shopping
                window.location.reload();
            } else {
                alert("Gagal menambahkan item. Pastikan semua field wajib terisi.");
            }
        })
        .catch(err => {
            console.error("Error submitting form:", err);
            window.location.reload();
        })
        .finally(() => {
            if (saveBtn) saveBtn.textContent = "Save item";
        });
    });

    // Filter Bar & Interactive Category Pills
    const categoryButtons = document.querySelectorAll("#category-tabs .tab-btn");
    const clearFiltersBtn = document.getElementById("btn-clear-filters");
    const searchInput = document.getElementById("wishlist-search");
    const filterSelects = document.querySelectorAll(".wishlist-filterbar select");

    categoryButtons.forEach(button => {
        button.addEventListener("click", () => {
            categoryButtons.forEach(btn => btn.classList.remove("active"));
            button.classList.add("active");
            filterItems();
        });
    });

    function filterItems() {
        const activeCategory = document.querySelector("#category-tabs .tab-btn.active")?.getAttribute("data-category")?.toLowerCase() || "";
        const searchQuery = searchInput?.value.toLowerCase().trim() || "";
        const selectedColor = document.getElementById("filter-color")?.value.toLowerCase() || "";

        const cards = document.querySelectorAll(".product-card");
        let visibleCount = 0;

        cards.forEach(card => {
            const category = (card.getAttribute("data-category") || "").toLowerCase();
            const color = (card.getAttribute("data-color") || "").toLowerCase();
            const name = (card.getAttribute("data-name") || "").toLowerCase();

            const matchCategory = !activeCategory || category === activeCategory;
            const matchColor = !selectedColor || color === selectedColor;
            const matchSearch = !searchQuery || name.includes(searchQuery);

            if (matchCategory && matchColor && matchSearch) {
                card.style.display = "block";
                visibleCount++;
            } else {
                card.style.display = "none";
            }
        });

        if (container) {
            container.style.display = visibleCount > 0 ? "grid" : "none";
        }
    }

    searchInput?.addEventListener("input", filterItems);
    filterSelects.forEach(select => select.addEventListener("change", filterItems));

    clearFiltersBtn?.addEventListener("click", () => {
        if (searchInput) searchInput.value = "";
        filterSelects.forEach(select => select.selectedIndex = 0);
        categoryButtons.forEach(btn => btn.classList.remove("active"));
        categoryButtons[0]?.classList.add("active");
        filterItems();
    });
});