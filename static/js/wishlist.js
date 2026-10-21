
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

            if (item.link) {
                try {
                    const url = new URL(item.link);

                    if (["https:", "http:"].includes(url.protocol)) {
                        const link = document.createElement("a");
                        link.href = url.href;
                        link.target = "_blank";
                        link.rel = "noopener noreferrer";
                        link.textContent = "View product";
                        card.appendChild(link);
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

            card.appendChild(removeButton);
            container.appendChild(card);
        });
    }

    function saveAndRender() {
        localStorage.setItem(storageKey, JSON.stringify(items));
        renderItems();
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
            reason
        });

        saveAndRender();
        form.reset();
        closeForm();
    });

    search?.addEventListener("input", renderItems);
    categoryFilter?.addEventListener("change", renderItems);
    matchFilter?.addEventListener("change", renderItems);

    renderItems();
});