document.addEventListener("DOMContentLoaded", () => {
    const formOverlay = document.getElementById("add-wishlist");
    const viewOverlay = document.getElementById("view-detail-modal");
    const deleteOverlay = document.getElementById("delete-modal");

    const closeFormButton = document.getElementById("close-wishlist-form");
    const cancelFormButton = document.getElementById("clear-wishlist-form");
    const formModalTitle = document.getElementById("form-modal-title");
    const form = document.getElementById("wishlist-form");
    const container = document.getElementById("wishlist-items");
    const noMatchSection = document.getElementById("wishlist-no-match");
    const priceInput = document.getElementById("item-price");

    let currentActiveItemId = null;
    let onlyShowMatches = false;

    // Helper: Format angka ke titik ribuan (misal: 100000 -> 100.000)
    function formatNumberWithDots(val) {
        if (!val) return "";
        const cleanNumber = val.toString().replace(/\D/g, "");
        return cleanNumber.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    }

    // Event listener auto-format saat ketik harga
    priceInput?.addEventListener("input", (e) => {
        const cursorPosition = e.target.selectionStart;
        const originalLength = e.target.value.length;
        
        e.target.value = formatNumberWithDots(e.target.value);
        
        const newLength = e.target.value.length;
        const newPosition = cursorPosition + (newLength - originalLength);
        e.target.setSelectionRange(newPosition, newPosition);
    });

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
        const addBtn = e.target.closest(".open-wishlist-form-btn") || e.target.closest("#open-wishlist-form");
        if (addBtn) {
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

    // INTERACTIVE STAT CARDS & VIEW MATCHING ITEMS ACTION
    const statCardAll = document.getElementById("stat-card-all");
    const statCardMatches = document.getElementById("stat-card-matches");
    const viewMatchingBtn = document.getElementById("btn-view-matching");

    function showAllWishlistItems() {
        onlyShowMatches = false;
        clearAllFilters();
        if (container) {
            container.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    }

    function showMatchingWishlistItems() {
        onlyShowMatches = true;
        filterItems();
        if (container) {
            container.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    }

    statCardAll?.addEventListener("click", showAllWishlistItems);
    statCardMatches?.addEventListener("click", showMatchingWishlistItems);
    viewMatchingBtn?.addEventListener("click", showMatchingWishlistItems);

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

                // Render Digital Closet Similar Items
                const similarContainer = document.getElementById("similar-closet-container");
                const similarList = document.getElementById("similar-closet-list");
                
                if (data.has_match && data.matched_items && data.matched_items.length > 0) {
                    similarList.innerHTML = "";
                    data.matched_items.forEach(match => {
                        const itemBox = document.createElement("div");
                        itemBox.style.cssText = "display: flex; align-items: center; gap: 8px; background: #FFF; border: 1px solid #8FB0D4; border-radius: 999px; padding: 4px 12px;";
                        itemBox.innerHTML = `
                            <img src="${match.photo_url}" style="width: 24px; height: 24px; border-radius: 50%; object-fit: cover;">
                            <span style="font-size: 12px; font-weight: 600; color: #3A2B48;">${match.name}</span>
                        `;
                        similarList.appendChild(itemBox);
                    });
                    similarContainer.style.display = "block";
                } else {
                    similarContainer.style.display = "none";
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
                document.getElementById("item-price").value = formatNumberWithDots(data.raw_price);
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

    // 4. DELEGATED CLICK HANDLERS FOR DROPDOWN & MENU BUTTON STATE
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
        
        document.querySelectorAll(".product-card-menu").forEach(btn => {
            if (btn !== menuBtn) btn.classList.remove("active");
        });

        document.querySelectorAll(".menu-dropdown").forEach(dd => {
            if (!menuBtn || dd.previousElementSibling !== menuBtn) {
                dd.classList.add("hidden");
            }
        });

        if (menuBtn) {
            menuBtn.classList.toggle("active");
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

    // Form Submit Logic (AJAX) - Bersihkan titik pada harga sebelum submit
    form?.addEventListener("submit", (e) => {
        e.preventDefault();
        
        // Simpan nilai terformat
        const originalPrice = priceInput ? priceInput.value : "";
        if (priceInput) {
            priceInput.value = priceInput.value.replace(/\D/g, "");
        }

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
                if (priceInput) priceInput.value = originalPrice;
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

    // FILTER LOGIC & NO MATCH CARD CONTROL
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
        const selectedStyle = document.getElementById("filter-style")?.value.toLowerCase() || "";
        const selectedStatus = document.getElementById("filter-status")?.value.toLowerCase() || "";
        const selectedSeason = document.getElementById("filter-season")?.value.toLowerCase() || "";
        const selectedWeather = document.getElementById("filter-weather")?.value.toLowerCase() || "";

        const cards = document.querySelectorAll(".product-card");
        const totalItemsInDatabase = cards.length;
        let visibleCount = 0;

        cards.forEach(card => {
            const category = (card.getAttribute("data-category") || "").toLowerCase();
            const color = (card.getAttribute("data-color") || "").toLowerCase();
            const style = (card.getAttribute("data-style") || "").toLowerCase();
            const season = (card.getAttribute("data-season") || "").toLowerCase();
            const weather = (card.getAttribute("data-weather") || "").toLowerCase();
            const name = (card.getAttribute("data-name") || "").toLowerCase();
            const hasMatch = card.getAttribute("data-has-match") === "true";

            const matchCategory = !activeCategory || category === activeCategory;
            const matchColor = !selectedColor || color === selectedColor;
            const matchStyle = !selectedStyle || style === selectedStyle;
            const matchSeason = !selectedSeason || season.includes(selectedSeason);
            const matchWeather = !selectedWeather || weather.includes(selectedWeather);
            const matchSearch = !searchQuery || name.includes(searchQuery);
            const matchStatCard = !onlyShowMatches || hasMatch;

            let matchStatus = true;
            if (selectedStatus === "similar item found") {
                matchStatus = hasMatch;
            } else if (selectedStatus === "no similar item found") {
                matchStatus = !hasMatch;
            }

            if (matchCategory && matchColor && matchStyle && matchSeason && matchWeather && matchSearch && matchStatCard && matchStatus) {
                card.style.display = "block";
                visibleCount++;
            } else {
                card.style.display = "none";
            }
        });

        const emptyDatabaseCard = document.getElementById("wishlist-empty");

        if (totalItemsInDatabase === 0) {
            if (container) container.style.display = "none";
            if (noMatchSection) noMatchSection.style.display = "none";
            if (emptyDatabaseCard) emptyDatabaseCard.style.display = "flex";
        } else if (visibleCount === 0) {
            if (container) container.style.display = "none";
            if (emptyDatabaseCard) emptyDatabaseCard.style.display = "none";
            if (noMatchSection) noMatchSection.style.display = "flex";
        } else {
            if (container) container.style.display = "grid";
            if (emptyDatabaseCard) emptyDatabaseCard.style.display = "none";
            if (noMatchSection) noMatchSection.style.display = "none";
        }
    }

    function clearAllFilters() {
        onlyShowMatches = false;
        if (searchInput) searchInput.value = "";
        filterSelects.forEach(select => select.selectedIndex = 0);
        categoryButtons.forEach(btn => btn.classList.remove("active"));
        categoryButtons[0]?.classList.add("active");
        filterItems();
    }

    searchInput?.addEventListener("input", filterItems);
    filterSelects.forEach(select => select.addEventListener("change", filterItems));

    clearFiltersBtn?.addEventListener("click", clearAllFilters);

    document.addEventListener("click", (e) => {
        if (e.target.closest(".btn-trigger-clear-filters")) {
            clearAllFilters();
        }
    });
});