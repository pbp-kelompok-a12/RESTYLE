document.addEventListener("DOMContentLoaded", () => {
    const formOverlay = document.getElementById("add-wishlist");
    const viewOverlay = document.getElementById("view-detail-modal");
    const deleteOverlay = document.getElementById("delete-modal");

    const closeFormButton = document.getElementById("close-wishlist-form");
    const cancelFormButton = document.getElementById("clear-wishlist-form");
    const formModalTitle = document.getElementById("form-modal-title");
    const form = document.getElementById("wishlist-form");
    const container = document.getElementById("wishlist-items");

    let currentActiveItemId = null;

    function openModal(el) {
        if (el) {
            el.hidden = false;
            document.body.style.overflow = "hidden";
        }
    }

    function closeModal(el) {
        if (el) {
            el.hidden = true;
            document.body.style.overflow = "";
        }
    }

    // Modal Add Event Trigger
    document.addEventListener("click", (e) => {
        if (e.target.closest("#open-wishlist-form") || e.target.closest(".wishlist-empty-card button")) {
            if (form) {
                form.reset();
                form.action = "/wishlist/add/";
            }
            if (formModalTitle) formModalTitle.textContent = "Add new item";
            clearPhoto();
            openModal(formOverlay);
        }
    });

    closeFormButton?.addEventListener("click", () => closeModal(formOverlay));
    cancelFormButton?.addEventListener("click", () => closeModal(formOverlay));

    // View Matching Items Action
    const viewMatchingBtn = document.getElementById("btn-view-matching");
    viewMatchingBtn?.addEventListener("click", () => {
        const cards = document.querySelectorAll(".product-card");
        let firstMatchCard = null;

        cards.forEach(card => {
            const hasMatch = card.getAttribute("data-has-match") === "true";
            if (hasMatch) {
                card.style.display = "block";
                if (!firstMatchCard) firstMatchCard = card;
            } else {
                card.style.display = "none";
            }
        });

        if (firstMatchCard) {
            firstMatchCard.scrollIntoView({ behavior: "smooth", block: "center" });
        }
    });

    // 1. DETAIL VIEW MODAL
    function openDetailModal(itemId) {
        currentActiveItemId = itemId;
        fetch(`/wishlist/${itemId}/detail/`)
            .then(res => res.json())
            .then(data => {
                document.getElementById("detail-title").textContent = data.name;
                document.getElementById("detail-category-pill").textContent = data.category;
                document.getElementById("detail-color-text").textContent = data.color;
                document.getElementById("detail-color-dot").style.backgroundColor = data.color_hex;
                document.getElementById("detail-material").textContent = data.material;
                document.getElementById("detail-brand").textContent = data.brand;
                document.getElementById("detail-price").textContent = data.price;
                document.getElementById("detail-style").textContent = data.style_tag;

                const photoEl = document.getElementById("detail-photo");
                photoEl.src = data.photo_url || "/static/img/bunglon_hires.png";

                const linkEl = document.getElementById("detail-link");
                if (data.link && data.link !== "") {
                    linkEl.innerHTML = `<a href="${data.link}" target="_blank" style="color:#3F6699;">Open link ↗</a>`;
                } else {
                    linkEl.textContent = "-";
                }

                openModal(viewOverlay);
            });
    }

    document.getElementById("close-detail-modal")?.addEventListener("click", () => closeModal(viewOverlay));

    // 2. EDIT MODAL
    function openEditModal(itemId) {
        currentActiveItemId = itemId;
        closeModal(viewOverlay);

        fetch(`/wishlist/${itemId}/detail/`)
            .then(res => res.json())
            .then(data => {
                if (formModalTitle) formModalTitle.textContent = "Edit item";
                if (form) form.action = `/wishlist/${itemId}/edit/`;

                document.getElementById("item-name").value = data.name;
                document.getElementById("item-brand").value = data.brand !== "-" ? data.brand : "";
                document.getElementById("item-link").value = data.link;
                document.getElementById("item-price").value = data.raw_price;
                document.getElementById("item-material").value = data.material !== "-" ? data.material : "";

                const catRadio = form.querySelector(`input[name="category"][value="${data.category}"]`);
                if (catRadio) catRadio.checked = true;

                const colorRadio = form.querySelector(`input[name="color"][value="${data.color}"]`);
                if (colorRadio) colorRadio.checked = true;

                if (data.photo_url) {
                    const preview = document.getElementById("item-photo-preview");
                    preview.querySelector("img").src = data.photo_url;
                    preview.hidden = false;
                    document.getElementById("photo-placeholder").hidden = true;
                }

                openModal(formOverlay);
            });
    }

    document.getElementById("btn-edit-from-view")?.addEventListener("click", () => {
        if (currentActiveItemId) openEditModal(currentActiveItemId);
    });

    // 3. DELETE MODAL
    function openDeleteModal(itemId, itemName) {
        currentActiveItemId = itemId;
        closeModal(viewOverlay);
        document.getElementById("delete-item-name").textContent = itemName || "this item";
        openModal(deleteOverlay);
    }

    document.getElementById("close-delete-modal")?.addEventListener("click", () => closeModal(deleteOverlay));
    document.getElementById("cancel-delete-btn")?.addEventListener("click", () => closeModal(deleteOverlay));

    document.getElementById("btn-delete-from-view")?.addEventListener("click", () => {
        const title = document.getElementById("detail-title").textContent;
        openDeleteModal(currentActiveItemId, title);
    });

    document.getElementById("confirm-delete-btn")?.addEventListener("click", () => {
        if (!currentActiveItemId) return;
        fetch(`/wishlist/${currentActiveItemId}/delete/`, {
            method: "POST",
            headers: {
                "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
            }
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === "success") {
                window.location.reload();
            }
        });
    });

    // 4. DELEGATED CLICK HANDLERS FOR DROPDOWN & ACTIONS
    document.addEventListener("click", (e) => {
        const viewBtn = e.target.closest(".view-action");
        if (viewBtn) {
            const id = viewBtn.getAttribute("data-id");
            if (id) openDetailModal(id);
            return;
        }

        const editBtn = e.target.closest(".edit-action");
        if (editBtn) {
            const id = editBtn.getAttribute("data-id");
            if (id) openEditModal(id);
            return;
        }

        const deleteBtn = e.target.closest(".delete-action");
        if (deleteBtn) {
            const id = deleteBtn.getAttribute("data-id");
            const name = deleteBtn.getAttribute("data-name");
            if (id) openDeleteModal(id, name);
            return;
        }

        const menuBtn = e.target.closest(".product-card-menu");
        document.querySelectorAll(".menu-dropdown").forEach(dd => {
            if (!menuBtn || dd.previousElementSibling !== menuBtn) {
                dd.classList.add("hidden");
            }
        });
        if (menuBtn) {
            menuBtn.nextElementSibling?.classList.toggle("hidden");
        }
    });

    // Photo Preview Logic
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

    // Form Submit Logic (AJAX)
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
                window.location.reload();
            } else {
                alert("Gagal menyimpan item. Pastikan field wajib sudah terisi.");
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

    // Filter Logic
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