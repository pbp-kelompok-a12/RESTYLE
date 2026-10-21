document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("wishlist-form");
    const container = document.getElementById("wishlist-items");
    const search = document.getElementById("wishlist-search");
    const categoryFilter = document.getElementById("filter-category");
    const matchFilter = document.getElementById("filter-match");
    const count = document.getElementById("wishlist-count");
    const savedCount = document.getElementById("saved-item-count");

    if (!form || !container) return;

    const storageKey = "restyle_wishlist_demo";
    let items = JSON.parse(localStorage.getItem(storageKey) || "[]");

    // Contoh data closet sementara untuk demo pencocokan.
    // Ganti dengan data Digital Closet asli saat integrasi backend.
    const demoCloset = [
        { category: "Top", color: "White", name: "White shirt" },
        { category: "Bottom", color: "Blue", name: "Blue jeans" },
        { category: "Shoes", color: "Black", name: "Black shoes" }
    ];

    function hasClosetMatch(item) {
        return demoCloset.some(closetItem =>
            closetItem.category.toLowerCase() === item.category.toLowerCase() &&
            closetItem.color.toLowerCase() === item.color.toLowerCase()
        );
    }

    function renderItems() {
        const keyword = search.value.trim().toLowerCase();
        const category = categoryFilter.value;
        const match = matchFilter.value;

        const filtered = items.filter(item => {
            const matchesKeyword =
                item.name.toLowerCase().includes(keyword) ||
                item.category.toLowerCase().includes(keyword) ||
                item.color.toLowerCase().includes(keyword);

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

        count.textContent = items.length;
        savedCount.textContent =
            `${items.length} item${items.length === 1 ? "" : "s"}`;

        if (filtered.length === 0) {
            const empty = document.createElement("p");
            empty.className = "wishlist-empty";
            empty.textContent = items.length
                ? "No items match your search or filters."
                : "Your wishlist is empty. Add your first item above!";
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
                `Color: ${item.color}`,
                item.price ? `Estimated price: Rp ${Number(item.price).toLocaleString("id-ID")}` : "",
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
                    if (url.protocol === "https:" || url.protocol === "http:") {
                        const link = document.createElement("a");
                        link.href = url.href;
                        link.target = "_blank";
                        link.rel = "noopener noreferrer";
                        link.textContent = "View product";
                        card.appendChild(link);
                    }
                } catch (_) {
                    // Abaikan URL yang tidak valid.
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

        if (!name || !category || !color) {
            form.reportValidity();
            return;
        }

        items.push({
            id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
            name,
            category,
            color,
            price: document.getElementById("item-price").value,
            link: document.getElementById("item-link").value.trim(),
            reason: document.getElementById("item-reason").value.trim()
        });

        saveAndRender();
        form.reset();
    });

    search.addEventListener("input", renderItems);
    categoryFilter.addEventListener("change", renderItems);
    matchFilter.addEventListener("change", renderItems);

    renderItems();
});