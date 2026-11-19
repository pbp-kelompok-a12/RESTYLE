(function () {
    "use strict";
    var bar = document.querySelector(".cl-filterbar");
    if (!bar || !document.querySelector(".cl-grid")) return; // bukan halaman daftar closet

    var FETCH_HEADERS = { "X-Requested-With": "fetch" };
    var FIELDS = ["q", "color", "style", "season", "weather", "status"];
    var latest = 0; 
    var deleteForm = null;
    var timer = null;

    function toast(type, text) {
        return window.showToast ? window.showToast(type, text) : null;
    }

    function closeModal() {
        var button = document.querySelector("#cl-overlay [data-close]");
        if (button) button.click(); // closet.js yang menutup pop-up
    }

    /* refresh */

    // pesan flash dari server ("... was removed from your closet.") tampil sebagai toast
    function toastsFrom(doc) {
        doc.querySelectorAll("#toast-stack .toast").forEach(function (item) {
            var text = item.querySelector("span");
            if (text) toast(item.classList.contains("toast-error") ? "error" : "success", text.textContent);
        });
    }

    function swap(doc) {
        var oldGrid = document.querySelector(".cl-grid");
        var newGrid = doc.querySelector(".cl-grid");
        if (oldGrid && newGrid) oldGrid.replaceWith(document.importNode(newGrid, true));

        var oldCount = document.querySelector(".cl-count");
        var newCount = doc.querySelector(".cl-count");
        if (oldCount && newCount) oldCount.textContent = newCount.textContent;

        // chip kategori ikut diganti karena link-nya membawa filter yang sedang aktif
        var oldCats = document.querySelector(".cl-cats");
        var newCats = doc.querySelector(".cl-cats");
        if (oldCats && newCats) oldCats.replaceWith(document.importNode(newCats, true));

        // link "Clear filters" hanya ada kalau ada filter aktif
        var oldClear = bar.querySelector(".cl-clear");
        var newClear = doc.querySelector(".cl-filterbar .cl-clear");
        if (oldClear && !newClear) oldClear.remove();
        else if (!oldClear && newClear) bar.appendChild(document.importNode(newClear, true));
    }

    function refresh(opts) {
        opts = opts || {};
        var mine = ++latest;
        var url = opts.url || location.pathname + location.search;

        return fetch(url, { cache: "no-store" })
            .then(function (res) {
                if (!res.ok) throw new Error("load failed");
                return res.text();
            })
            .then(function (html) {
                var doc = new DOMParser().parseFromString(html, "text/html");
                toastsFrom(doc);              // pesan flash sudah "dimakan" server, jadi selalu ditampilkan
                if (mine !== latest) return;  // ada refresh yang lebih baru, hasil ini dibuang
                swap(doc);
                if (opts.push) history.pushState(null, "", url); // URL ikut berubah, bisa di-refresh / dishare
            })
            .catch(function () {
                toast("error", "Could not update your closet. Please try again.");
            });
    }

    /* add/edit */

    // foto > 4 MB dikecilkan dulu di browser (sama seperti di closet.js)
    function compressPhoto(form) {
        var input = form.querySelector("#photo-input");
        var file = input && input.files && input.files[0];
        if (!file || file.size <= 4 * 1024 * 1024) return Promise.resolve();

        return createImageBitmap(file).then(function (bitmap) {
            var scale = Math.min(1, 1800 / Math.max(bitmap.width, bitmap.height));
            var canvas = document.createElement("canvas");
            canvas.width = Math.max(1, Math.round(bitmap.width * scale));
            canvas.height = Math.max(1, Math.round(bitmap.height * scale));
            canvas.getContext("2d").drawImage(bitmap, 0, 0, canvas.width, canvas.height);
            bitmap.close();

            function encode(quality) {
                return new Promise(function (resolve, reject) {
                    canvas.toBlob(function (blob) {
                        if (!blob) return reject(new Error("Image compression is unavailable."));
                        if (blob.size <= 4 * 1024 * 1024) return resolve(blob);
                        if (quality <= 0.5) return reject(new Error("Image is still too large after compression."));
                        resolve(encode(quality - 0.12));
                    }, "image/webp", quality);
                });
            }

            return encode(0.82).then(function (blob) {
                var transfer = new DataTransfer();
                transfer.items.add(new File([blob], file.name.replace(/\.[^.]+$/, "") + ".webp", {
                    type: "image/webp",
                    lastModified: Date.now()
                }));
                input.files = transfer.files;
            });
        });
    }

    // form yang ditampilkan ulang dengan pesan error: pasang lagi preview foto dan format harga
    function initModalForm(root) {
        var input = root.querySelector("#photo-input");
        if (input) {
            var preview = root.querySelector("#photo-preview");
            var placeholder = root.querySelector("#photo-placeholder");
            input.addEventListener("change", function () {
                var file = input.files[0];
                if (!file) return;
                preview.src = URL.createObjectURL(file);
                preview.hidden = false;
                placeholder.hidden = true;
            });
        }
        root.querySelectorAll("[data-money]").forEach(function (el) {
            el.value = el.value.replace(/\D/g, "").replace(/\B(?=(\d{3})+(?!\d))/g, ".");
        });
    }

    function saveForm(form) {
        var loading = toast("loading", "Saving...");
        compressPhoto(form)
            .then(function () {
                return fetch(form.action, { method: "POST", body: new FormData(form), headers: FETCH_HEADERS });
            })
            .then(function (res) {
                if (res.ok) {
                    closeModal();
                    return refresh(); // pesan "Yay! ... is now in your closet!" ikut tampil dari sini
                }
                if (res.status === 400) {  // validasi gagal: tampilkan form lagi beserta error-nya
                    return res.text().then(function (html) {
                        var body = document.getElementById("cl-modal-body");
                        body.innerHTML = html;
                        initModalForm(body);
                    });
                }
                throw new Error("save failed");
            })
            .catch(function () {
                toast("error", "Could not compress or upload the photo. Try a smaller image.");
            })
            .finally(function () {
                if (loading && window.hideToast) window.hideToast(loading);
            });
    }

    /* delete */

    function deleteItem(form) {
        var match = /\/item\/(\d+)\/delete\/?$/.exec(form.getAttribute("action"));
        var link = match && document.querySelector('.cl-card-link[href$="/item/' + match[1] + '/"]');
        var card = link && link.closest(".cl-card");

        closeModal();
        if (card) card.hidden = true;

        fetch(form.getAttribute("action"), { method: "POST", body: new FormData(form), headers: FETCH_HEADERS })
            .then(function (res) {
                if (!res.ok && res.status !== 404) throw new Error("delete failed"); // 404 = sudah terhapus duluan
                if (card) card.remove();
                return refresh(); // pesan "was removed from your closet." ikut tampil dari sini
            })
            .catch(function () {
                if (card) card.hidden = false; // rollback
                toast("error", "Could not delete the item. Please try again.");
            });
    }

    // klik "Delete" di pop-up konfirmasi: hentikan handler lama closet.js (yang reload), pakai deleteItem
    document.addEventListener("click", function (e) {
        if (!deleteForm || !e.target.closest("[data-confirm-yes]")) return;
        e.stopPropagation();
        deleteItem(deleteForm);
    }, true);

    /* ganti status */

    var BADGE = { ready: "Ready to Wear", washing: "In the Wash" };
    var BUTTON = { ready: "Change to In The Wash", washing: "Change to Ready" };

    function statusOf(card) {
        return card.querySelector(".cl-badge").classList.contains("cl-badge-washing") ? "washing" : "ready";
    }

    function paint(card, form, status) {
        var badge = card.querySelector(".cl-badge");
        badge.className = "cl-badge cl-badge-" + status;
        badge.textContent = BADGE[status];
        form.querySelector("button").textContent = BUTTON[status];
    }

    function toggleStatus(form) {
        var card = form.closest(".cl-card");
        if (!card || form.dataset.pending) return; // abaikan klik berulang selagi menunggu server
        var before = statusOf(card);
        form.dataset.pending = "1";

        var list = form.closest(".cl-menu-list"); // tutup menu titik tiga
        if (list) {
            list.hidden = true;
            list.previousElementSibling.setAttribute("aria-expanded", "false");
        }

        paint(card, form, before === "ready" ? "washing" : "ready"); // optimistic: langsung berubah

        fetch(form.action, { method: "POST", body: new FormData(form) })
            .then(function (res) {
                if (!res.ok) throw new Error("status failed");
                return res.text(); // server redirect ke halaman closet, di dalamnya ada pesan flash-nya
            })
            .then(function (html) {
                toastsFrom(new DOMParser().parseFromString(html, "text/html"));
                // kalau filter status sedang aktif, kartu ini mungkin sudah tidak cocok lagi
                if (new URLSearchParams(location.search).has("status")) refresh();
            })
            .catch(function () {
                paint(card, form, before); // rollback
                toast("error", "Could not update the status. Please try again.");
            })
            .finally(function () { delete form.dataset.pending; });
    }

    /* filter */

    // kategori (cat) ikut URL karena diatur lewat chip; sisanya diambil dari isi form
    function buildUrl() {
        var params = new URLSearchParams(location.search);
        FIELDS.forEach(function (name) {
            var value = bar.elements[name].value.trim();
            if (value) params.set(name, value);
            else params.delete(name);
        });
        var query = params.toString();
        return location.pathname + (query ? "?" + query : "");
    }

    function applyFilters() {
        clearTimeout(timer);
        refresh({ url: buildUrl(), push: true });
    }

    // pilih filter: langsung jalan, form.submit() lama di closet.js dilewati
    document.addEventListener("change", function (e) {
        if (e.target.matches && e.target.matches("select[data-autosubmit]")) {
            e.stopImmediatePropagation();
            applyFilters();
        }
    }, true);

    // search: tunggu 300 ms setelah berhenti mengetik supaya tidak kirim request di tiap huruf
    bar.elements.q.addEventListener("input", function () {
        clearTimeout(timer);
        timer = setTimeout(applyFilters, 300);
    });

    document.addEventListener("click", function (e) {
        var chip = e.target.closest(".cl-cat");
        if (chip) {
            e.preventDefault();
            refresh({ url: chip.pathname + chip.search, push: true });
            return;
        }
        // "Clear filters" di bar filter dan di tampilan "No items match"
        var clear = e.target.closest(".cl-clear, .cl-empty a:not([data-modal])");
        if (clear) {
            e.preventDefault();
            FIELDS.forEach(function (name) { bar.elements[name].value = ""; });
            refresh({ url: location.pathname, push: true });
        }
    });

    // tombol Back / Forward browser
    window.addEventListener("popstate", function () {
        var params = new URLSearchParams(location.search);
        FIELDS.forEach(function (name) { bar.elements[name].value = params.get(name) || ""; });
        refresh();
    });

    /* SUBMIT */
    document.addEventListener("submit", function (e) {
        var form = e.target;

        if (form === bar) {
            e.preventDefault();
            e.stopImmediatePropagation();
            applyFilters();
            return;
        }
        if (form.hasAttribute("data-modal-form")) { 
            e.preventDefault();
            e.stopImmediatePropagation();
            saveForm(form);
            return;
        }
        if (form.matches('form[action$="/status/"]')) {       
            e.preventDefault();
            e.stopImmediatePropagation();
            toggleStatus(form);
            return;
        }
        if (form.hasAttribute("data-confirm")) {
            deleteForm = form;
        }
    }, true);
})();