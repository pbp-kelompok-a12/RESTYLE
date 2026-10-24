
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("wishlist-form");
    const container = document.getElementById("wishlist-items");
    const search = document.getElementById("wishlist-search");
    const categoryFilter = document.getElementById("filter-category");
    const matchFilter = document.getElementById("filter-match");
    const count = document.getElementById("wishlist-count");
    const savedCount = document.getElementById("saved-item-count");

    const formSection = document.getElementById("add-wishlist");
    const openFormButton = document.getElementById("open-wishlist-form");
    const closeFormButton = document.getElementById("close-wishlist-form");
    const clearFormButton = document.getElementById("clear-wishlist-form");

    if (!form || !container) return;

    // Keep the form hidden until the user opens it.
    function closeForm() {
        formSection.hidden = true;
        openFormButton?.setAttribute("aria-expanded", "false");
    }

    function openForm() {
        formSection.hidden = false;
        openFormButton?.setAttribute("aria-expanded", "true");

        formSection.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

        document.getElementById("item-name")?.focus({
            preventScroll: true
        });
    }

    openFormButton?.addEventListener("click", openForm);
    closeFormButton?.addEventListener("click", closeForm);

    clearFormButton?.addEventListener("click", () => {
        form.reset();
        document.getElementById("item-name")?.focus();
    });

    // Item photo: shrunk in the browser first, since the wishlist lives in localStorage
    // (about 5 MB per browser), then kept as a data URL.
    const photoInput = document.getElementById("item-photo");
    const photoPreview = document.getElementById("item-photo-preview");
    const removePhotoButton = document.getElementById("remove-item-photo");
    const MAX_PHOTO_SIDE = 600;
    let photoData = "";

    function clearPhoto() {
        photoData = "";
        if (photoInput) photoInput.value = "";
        if (photoPreview) {
            photoPreview.hidden = true;
            photoPreview.querySelector("img").src = "";
        }
    }

    function shrinkPhoto(file) {
        return createImageBitmap(file).then(bitmap => {
            const scale = Math.min(1, MAX_PHOTO_SIDE / Math.max(bitmap.width, bitmap.height));
            const canvas = document.createElement("canvas");
            canvas.width = Math.max(1, Math.round(bitmap.width * scale));
            canvas.height = Math.max(1, Math.round(bitmap.height * scale));
            const context = canvas.getContext("2d");
            context.fillStyle = "#ffffff"; // transparent PNGs get a white background
            context.fillRect(0, 0, canvas.width, canvas.height);
            context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
            bitmap.close?.();
            return canvas.toDataURL("image/jpeg", 0.75);
        });
    }

    photoInput?.addEventListener("change", () => {
        const file = photoInput.files[0];
        if (!file) {
            clearPhoto();
            return;
        }
        if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
            clearPhoto();
            window.showToast?.("error", "Choose a JPG, PNG, or WebP photo.");
            return;
        }
        shrinkPhoto(file).then(dataUrl => {
            photoData = dataUrl;
            photoPreview.querySelector("img").src = dataUrl;
            photoPreview.hidden = false;
        }).catch(() => {
            clearPhoto();
            window.showToast?.("error", "Could not read that photo. Try another image.");
        });
    });

    removePhotoButton?.addEventListener("click", clearPhoto);
    form.addEventListener("reset", clearPhoto);

    closeForm();

    const storageKey = "restyle_wishlist_demo";

    let items = [];

    try {
        items = JSON.parse(localStorage.getItem(storageKey) || "[]");

        if (!Array.isArray(items)) {
            items = [];
        }
    } catch (error) {
        items = [];
    }

    // DEMO DATA ONLY:
    // Replace with the logged-in user's real Digital Closet data
    // when the Django backend integration is ready.
    const demoCloset = [
        { category: "Top", color: "White", name: "White shirt" },
        { category: "Bottom", color: "Blue", name: "Blue jeans" },
        { category: "Shoes", color: "Black", name: "Black shoes" }
    ];

    function normalize(value) {
        return String(value || "").trim().toLowerCase();
    }

    function hasClosetMatch(item) {
        return demoCloset.some(closetItem =>
            normalize(closetItem.category) === normalize(item.category) &&
            normalize(closetItem.color) === normalize(item.color)
        );
    }

    function renderItems() {
        const keyword = normalize(search?.value);
        const category = categoryFilter?.value || "";
        const match = matchFilter?.value || "all";

        const filtered = items.filter(item => {
            const matchesKeyword = [
                item.name,
                item.category,
                item.color,
                item.reason
            ].some(value => normalize(value).includes(keyword));

            const matchesCategory =
                !category || item.category === category;

            const matched = hasClosetMatch(item);

            const matchesCloset =
                match === "all" ||
                (match === "matched" && matched) ||
                (match === "unmatched" && !matched);

            return matchesKeyword && matchesCategory && matchesCloset;
        });

        container.replaceChildren();

        if (count) {
            count.textContent = items.length;
        }

        if (savedCount) {
            savedCount.textContent =
                `${items.length} item${items.length === 1 ? "" : "s"}`;
        }

        if (filtered.length === 0) {
            const empty = document.createElement("p");
            empty.className = "wishlist-empty";
            empty.textContent = items.length
                ? "No items match your search or filters."
                : "Your wishlist is empty. Select “Add to wishlist” to save your first item.";

            container.appendChild(empty);
            return;
        }

        filtered.forEach(item => {
            const card = document.createElement("article");
            card.className = "wishlist-item-card";

            // Photo uploaded in the form, or the closet photo for items saved from Community.
            if (/^(\/|https?:\/\/|data:image\/)/i.test(item.photo || "")) {
                const image = document.createElement("img");
                image.className = "wishlist-item-photo";
                image.src = item.photo;
                image.alt = item.name;
                card.appendChild(image);
            }

            const title = document.createElement("h3");
            title.textContent = item.name;
            card.appendChild(title);

            [
                `Category: ${item.category}`,
                `Main color: ${item.color}`,
                item.price
                    ? `Estimated price: Rp ${Number(item.price).toLocaleString("id-ID")}`
                    : "",
                item.reason ? `Reason: ${item.reason}` : "",
                hasClosetMatch(item)
                    ? "Closet reminder: You may already own a similar item."
                    : "Closet reminder: No exact category-and-color match in demo data."
            ].filter(Boolean).forEach(text => {
                const paragraph = document.createElement("p");
                paragraph.textContent = text;
                card.appendChild(paragraph);
            });

            // Keep the product link and Remove button on one row at the bottom.
            const actions = document.createElement("div");
            actions.className = "wishlist-item-actions";

            if (item.link) {
                try {
                    const url = new URL(item.link);

                    if (["https:", "http:"].includes(url.protocol)) {
                        const link = document.createElement("a");
                        link.href = url.href;
                        link.target = "_blank";
                        link.rel = "noopener noreferrer";
                        link.className = "view-product";
                        link.textContent = "View product";
                        actions.appendChild(link);
                    }
                } catch (error) {
                    // Ignore invalid product URLs.
                }
            }

            const removeButton = document.createElement("button");
            removeButton.type = "button";
            removeButton.className = "remove-item";
            removeButton.textContent = "Remove";

            removeButton.addEventListener("click", () => {
                items = items.filter(saved => saved.id !== item.id);
                saveAndRender();
            });

            actions.appendChild(removeButton);
            card.appendChild(actions);
            container.appendChild(card);
        });
    }

    function saveAndRender() {
        try {
            localStorage.setItem(storageKey, JSON.stringify(items));
        } catch (error) {
            renderItems();
            return false; // usually the browser storage is full
        }
        renderItems();
        return true;
    }

    form.addEventListener("submit", event => {
        event.preventDefault();

        const name = document.getElementById("item-name").value.trim();
        const category = document.getElementById("item-category").value;
        const color = document.getElementById("item-color").value;
        const price = document.getElementById("item-price").value;
        const link = document.getElementById("item-link").value.trim();
        const reason = document.getElementById("item-reason").value.trim();

        if (!name || !category || !color) {
            form.reportValidity();
            return;
        }

        items.push({
            id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
            name,
            category,
            color,
            price,
            link,
            reason,
            photo: photoData
        });

        if (!saveAndRender()) {
            items.pop();
            window.showToast?.("error", "Your wishlist storage is full. Remove some items or use a smaller photo.");
            return;
        }
        form.reset();
        closeForm();
        window.showToast?.("success", "Added to your wishlist.");
    });

    search?.addEventListener("input", renderItems);
    categoryFilter?.addEventListener("change", renderItems);
    matchFilter?.addEventListener("change", renderItems);

    renderItems();
});