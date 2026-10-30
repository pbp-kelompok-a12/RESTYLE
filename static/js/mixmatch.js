(function () {
    "use strict";

    var form = document.getElementById("mm-form");
    if (!form) return;

    var none = form.querySelector(".mm-none");
    var chips = Array.prototype.slice.call(
        form.querySelectorAll(".mm-chip")
    );
    var items = Array.prototype.slice.call(
        form.querySelectorAll(".mm-item")
    );

    var slots = {};

    form.querySelectorAll(".mm-slot").forEach(function (el) {
        slots[el.dataset.slot] = el;
    });

    var error = document.getElementById("mm-error");

    /* ---------- slot helpers ---------- */
    function slotInput(key) {
        return slots[key].querySelector('input[type="hidden"]');
    }

    function accessoryIds() {
        if (!slots.accessories) return [];

        return Array.prototype.slice.call(
            slots.accessories.querySelectorAll(
                '.mm-accessory-piece input[name="accessories"]'
            )
        ).map(function (input) {
            return input.value;
        });
    }

    /* ---------- render multiple accessories ---------- */
    function renderAccessories(ids) {
        var slot = slots.accessories;
        if (!slot) return;

        var container = slot.querySelector(".mm-accessory-pieces");
        var clearButton = slot.querySelector(".mm-slot-clear");

        // Hindari ID yang sama muncul dua kali.
        ids = ids.filter(function (id, index) {
            return ids.indexOf(id) === index;
        });

        container.innerHTML = "";

        ids.forEach(function (id) {
            var item = items.find(function (el) {
                return el.dataset.id === id;
            });

            if (!item) return;

            var piece = document.createElement("div");
            piece.className = "mm-accessory-piece";

            var input = document.createElement("input");
            input.type = "hidden";
            input.name = "accessories";
            input.value = id;

            var photo = item.dataset.photo;

            if (photo) {
                var img = document.createElement("img");
                img.src = photo;
                img.alt = item.dataset.name;
                piece.appendChild(img);
            } else {
                var swatch = document.createElement("i");
                swatch.className = "mm-swatch";
                swatch.style.background = item.dataset.color;
                piece.appendChild(swatch);
            }

            var name = document.createElement("span");
            name.className = "mm-slot-name";
            name.textContent = item.dataset.name;

            var remove = document.createElement("button");
            remove.type = "button";
            remove.className = "mm-accessory-remove";
            remove.textContent = "×";
            remove.setAttribute(
                "aria-label",
                "Remove " + item.dataset.name
            );

            remove.addEventListener("click", function () {
                renderAccessories(
                    accessoryIds().filter(function (selectedId) {
                        return selectedId !== id;
                    })
                );
            });

            piece.appendChild(name);
            piece.appendChild(remove);
            piece.appendChild(input);
            container.appendChild(piece);
        });

        var hasAccessories = container.children.length > 0;

        container.hidden = !hasAccessories;
        slot.classList.toggle("is-filled", hasAccessories);

        if (clearButton) {
            clearButton.hidden = !hasAccessories;
        }

        markPicked();
    }
    
    /* ---------- remove accessories ---------- */
    if (slots.accessories) {
        var accessoryContainer = slots.accessories.querySelector(
            ".mm-accessory-pieces"
        );

        if (accessoryContainer) {
            accessoryContainer.addEventListener("click", function (event) {
                var removeButton = event.target.closest(
                    ".mm-accessory-remove"
                );

                if (!removeButton) return;

                event.preventDefault();
                event.stopPropagation();

                var piece = removeButton.closest(".mm-accessory-piece");
                var input = piece.querySelector(
                    'input[name="accessories"]'
                );

                if (!input) return;

                var idToRemove = input.value;

                renderAccessories(
                    accessoryIds().filter(function (id) {
                        return id !== idToRemove;
                    })
                );
            });
        }
    }

    /* ---------- isi / kosongkan slot ---------- */
    function setSlot(key, item) {
        if (key === "accessories") {
            renderAccessories(item ? [item.dataset.id] : []);
            return;
        }

        var slot = slots[key];
        if (!slot) return;

        var piece = slot.querySelector(".mm-slot-piece");
        var img = piece.querySelector("img");
        var swatch = piece.querySelector(".mm-swatch");
        var clearButton = slot.querySelector(".mm-slot-clear");

        slotInput(key).value = item ? item.dataset.id : "";

        slot.classList.toggle("is-filled", !!item);
        piece.hidden = !item;
        clearButton.hidden = !item;

        if (item) {
            var photo = item.dataset.photo;

            if (photo) {
                img.src = photo;
                img.alt = item.dataset.name;
                img.hidden = false;
                swatch.hidden = true;
            } else {
                img.removeAttribute("src");
                img.hidden = true;
                swatch.style.background = item.dataset.color;
                swatch.hidden = false;
            }

            piece.querySelector(".mm-slot-name").textContent =
                item.dataset.name;
        }

        markPicked();
    }

    function markPicked() {
        var selectedAccessories = accessoryIds();

        items.forEach(function (el) {
            var key = el.dataset.slot;
            var picked = false;

            if (key === "accessories") {
                picked = selectedAccessories.includes(el.dataset.id);
            } else if (slots[key]) {
                picked = slotInput(key).value === el.dataset.id;
            }

            el.classList.toggle("is-picked", picked);
        });
    }

    /* ---------- filter kategori ---------- */
    function applyFilter(category) {
        var shown = 0;

        chips.forEach(function (chip) {
            chip.classList.toggle(
                "is-active",
                chip.dataset.category === category
            );
        });

        items.forEach(function (el) {
            var match = !category || el.dataset.category === category;

            el.hidden = !match;

            if (match) shown += 1;
        });

        if (none) {
            none.hidden = shown !== 0;
        }
    }

    chips.forEach(function (chip) {
        chip.addEventListener("click", function () {
            applyFilter(chip.dataset.category);
        });
    });

    /* ---------- klik item di closet ---------- */
    items.forEach(function (el) {
        el.addEventListener("click", function () {
            if (el.disabled || !slots[el.dataset.slot]) return;

            var key = el.dataset.slot;

            if (key === "accessories") {
                var selected = accessoryIds();
                var id = el.dataset.id;

                if (selected.includes(id)) {
                    renderAccessories(
                        selected.filter(function (selectedId) {
                            return selectedId !== id;
                        })
                    );
                } else {
                    renderAccessories(selected.concat(id));
                }
            } else if (slotInput(key).value === el.dataset.id) {
                setSlot(key, null);
            } else {
                setSlot(key, el);
            }

            if (error) error.hidden = true;
        });
    });

    /* ---------- detail item ---------- */
    form.querySelectorAll(".mm-item-detail-link").forEach(function (button) {
        button.addEventListener("click", function () {
            var url = button.dataset.detailUrl;

            if (url) {
                window.location.href = url;
            }
        });
    });

    /* ---------- tombol di slot ---------- */
    Object.keys(slots).forEach(function (key) {
        var slot = slots[key];
        var clearButton = slot.querySelector(".mm-slot-clear");
        var addButton = slot.querySelector(".mm-slot-add");

        if (clearButton) {
            clearButton.addEventListener("click", function () {
                if (key === "accessories") {
                    renderAccessories([]);
                } else {
                    setSlot(key, null);
                }
            });
        }

        if (addButton) {
            addButton.addEventListener("click", function () {
                var categories = slot.dataset.categories
                    .split(",")
                    .map(function (category) {
                        return category.trim();
                    });

                applyFilter(categories[0] || "");

                var panel = form.querySelector(".mm-closet");

                if (
                    panel &&
                    window.matchMedia("(max-width: 1100px)").matches
                ) {
                    panel.scrollIntoView({
                        behavior: "smooth",
                        block: "start"
                    });
                }
            });
        }
    });

    /* ---------- Reset ---------- */
    var resetButton = form.querySelector(".mm-reset");

    if (resetButton) {
        resetButton.addEventListener("click", function () {
            Object.keys(slots).forEach(function (key) {
                if (key === "accessories") {
                    renderAccessories([]);
                } else {
                    setSlot(key, null);
                }
            });

            if (error) error.hidden = true;
        });
    }

    /* ---------- Shuffle ---------- */
    var shuffleButton = form.querySelector(".mm-shuffle");

    if (shuffleButton) {
        shuffleButton.addEventListener("click", function () {
            Object.keys(slots).forEach(function (key) {
                var options = items.filter(function (el) {
                    return el.dataset.slot === key && !el.disabled;
                });

                if (!options.length) return;

                if (key === "accessories") {
                    // Acak satu atau beberapa aksesori.
                    var shuffled = options.slice();

                    for (var i = shuffled.length - 1; i > 0; i--) {
                        var j = Math.floor(Math.random() * (i + 1));
                        var temp = shuffled[i];
                        shuffled[i] = shuffled[j];
                        shuffled[j] = temp;
                    }

                    var count = Math.floor(
                        Math.random() * shuffled.length
                    ) + 1;

                    renderAccessories(
                        shuffled.slice(0, count).map(function (el) {
                            return el.dataset.id;
                        })
                    );

                    return;
                }

                var current = slotInput(key).value;

                var others = options.filter(function (el) {
                    return el.dataset.id !== current;
                });

                var pool = others.length ? others : options;

                setSlot(
                    key,
                    pool[Math.floor(Math.random() * pool.length)]
                );
            });

            if (error) error.hidden = true;
        });
    }

    /* ---------- validasi sebelum submit ---------- */
    form.addEventListener("submit", function (event) {
        var filled = Object.keys(slots).some(function (key) {
            if (key === "accessories") {
                return accessoryIds().length > 0;
            }

            return slotInput(key).value !== "";
        });

        if (!filled) {
            event.preventDefault();

            if (error) {
                error.hidden = false;
                error.scrollIntoView({
                    behavior: "smooth",
                    block: "center"
                });
            }
        }
    });

    /* ---------- konfirmasi hapus outfit ---------- */
    var overlay = document.getElementById("mm-overlay");
    var modalText = document.getElementById("mm-modal-text");
    var confirmYes = document.getElementById("mm-confirm-yes");
    var pendingForm = null;

    function closeModal() {
        if (!overlay) return;

        overlay.hidden = true;
        document.body.style.overflow = "";
        pendingForm = null;
    }

    function openConfirm(deleteForm) {
        pendingForm = deleteForm;

        modalText.textContent =
            '"' + deleteForm.dataset.confirm +
            '" will be removed from your saved outfits. This can\'t be undone.';

        overlay.hidden = false;
        document.body.style.overflow = "hidden";

        var cancelButton = overlay.querySelector(".mm-modal-cancel");

        if (cancelButton) cancelButton.focus();
    }

    if (overlay && modalText && confirmYes) {
        document.querySelectorAll(".mm-outfit-delete").forEach(function (deleteForm) {
            deleteForm.addEventListener("submit", function (event) {
                event.preventDefault();
                openConfirm(deleteForm);
            });
        });

        confirmYes.addEventListener("click", function () {
            var deleteForm = pendingForm;

            closeModal();

            if (deleteForm) {
                deleteForm.submit();
            }
        });

        overlay.addEventListener("click", function (event) {
            if (
                event.target === overlay ||
                (event.target.closest && event.target.closest("[data-close]"))
            ) {
                closeModal();
            }
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && !overlay.hidden) {
                closeModal();
            }
        });
    }

    /* ---------- detail saved outfit ---------- */
    var detailOverlay = document.getElementById("mm-detail-overlay");
    var detailTitle = document.getElementById("mm-detail-title");
    var detailTags = document.getElementById("mm-detail-tags");
    var detailPieces = document.getElementById("mm-detail-pieces");
    var detailNotesWrap = document.getElementById("mm-detail-notes-wrap");
    var detailNotes = document.getElementById("mm-detail-notes");
    var detailEdit = document.getElementById("mm-detail-edit");
    var detailDelete = document.getElementById("mm-detail-delete");

    var activeDetailCard = null;

    function closeDetailModal() {
        if (!detailOverlay) return;

        detailOverlay.hidden = true;
        document.body.style.overflow = "";
        activeDetailCard = null;
    }

    function openDetailModal(card) {
        if (!detailOverlay) return;

        var source = card.querySelector(".mm-outfit-detail-source");
        if (!source) return;

        activeDetailCard = card;

        detailTitle.textContent = source.dataset.outfitName || "Saved Outfit";

        var tags = source.dataset.outfitTags || "";
        detailTags.textContent = tags;
        detailTags.hidden = !tags.trim();

        var notes = source.dataset.outfitNotes || "";
        detailNotes.textContent = notes;
        detailNotesWrap.hidden = !notes.trim();

        detailPieces.replaceChildren();

        source.querySelectorAll(".mm-detail-source-piece").forEach(function (piece) {
            var itemCard = document.createElement("div");
            itemCard.className = "mm-detail-piece-card";

            var visual = document.createElement("div");
            visual.className = "mm-detail-piece-visual";

            if (piece.dataset.photo) {
                var img = document.createElement("img");
                img.src = piece.dataset.photo;
                img.alt = piece.dataset.name || "";
                img.loading = "lazy";
                visual.appendChild(img);
            } else {
                var swatch = document.createElement("i");
                swatch.className = "mm-swatch";
                swatch.style.background = piece.dataset.color || "transparent";
                visual.appendChild(swatch);
            }

            var slotName = document.createElement("span");
            slotName.className = "mm-detail-piece-slot";
            slotName.textContent = (piece.dataset.slot || "")
                .replace(/_/g, " ")
                .replace(/\b\w/g, function (letter) {
                    return letter.toUpperCase();
                });

            var itemName = document.createElement("p");
            itemName.className = "mm-detail-piece-name";
            itemName.textContent = piece.dataset.name || "Unnamed item";

            itemCard.appendChild(visual);
            itemCard.appendChild(slotName);
            itemCard.appendChild(itemName);
            detailPieces.appendChild(itemCard);
        });

        if (!detailPieces.children.length) {
            detailPieces.textContent = "No clothing items in this outfit.";
        }

        detailOverlay.hidden = false;
        document.body.style.overflow = "hidden";
    }

    document.querySelectorAll("[data-outfit-detail-trigger]").forEach(function (link) {
        link.addEventListener("click", function (event) {
            var card = link.closest(".mm-outfit");
            if (!card || !card.querySelector(".mm-outfit-detail-source")) return;

            event.preventDefault();
            openDetailModal(card);
        });
    });

    if (detailOverlay) {
        detailOverlay.addEventListener("click", function (event) {
            if (
                event.target === detailOverlay ||
                (event.target.closest && event.target.closest("[data-detail-close]"))
            ) {
                closeDetailModal();
            }
        });
    }

    if (detailEdit) {
        detailEdit.addEventListener("click", function () {
            if (!activeDetailCard) return;

            var source = activeDetailCard.querySelector(".mm-outfit-detail-source");
            if (source && source.dataset.editUrl) {
                window.location.href = source.dataset.editUrl;
            }
        });
    }

    if (detailDelete) {
        detailDelete.addEventListener("click", function () {
            if (!activeDetailCard) return;

            var deleteForm = activeDetailCard.querySelector(".mm-outfit-delete");

            if (deleteForm) {
                closeDetailModal();

                var deleteButton = deleteForm.querySelector('button[type="submit"]');
                if (deleteButton) {
                    deleteButton.click();
                }
            }
        });
    }

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && detailOverlay && !detailOverlay.hidden) {
            closeDetailModal();
        }
    });

    /* ---------- initial state ---------- */
    markPicked();
    })();