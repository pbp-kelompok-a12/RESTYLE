(function () {
    "use strict";

    var overlay = document.getElementById("cl-overlay");
    var body = document.getElementById("cl-modal-body");

    /* ---------- menu titik tiga di card ---------- */
    function closeMenus() {
        document.querySelectorAll(".cl-menu-list").forEach(function (list) {
            list.hidden = true;
            var btn = list.previousElementSibling;
            if (btn) btn.setAttribute("aria-expanded", "false");
        });
    }

    /* ---------- preview foto di form ---------- */
    function initPhoto(root) {
        var input = root.querySelector("#photo-input");
        if (!input) return;
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
    initPhoto(document);

    /* ---------- pop-up ---------- */
    function openModal(html) {
        body.innerHTML = html;
        overlay.hidden = false;
        document.body.style.overflow = "hidden";
        initPhoto(body);
        body.querySelectorAll("[data-money]").forEach(formatMoney);
    }

    function closeModal() {
        if (!overlay) return;
        overlay.hidden = true;
        body.innerHTML = "";
        document.body.style.overflow = "";
    }

    function loadModal(url) {
        var sep = url.indexOf("?") === -1 ? "?" : "&";
        fetch(url + sep + "modal=1", { headers: { "X-Requested-With": "fetch" } })
            .then(function (res) {
                if (!res.ok) throw new Error("load failed");
                return res.text();
            })
            .then(openModal)
            .catch(function () { window.location.href = url; });
    }

    function compressPhoto(form) {
        var input = form.querySelector('#photo-input');
        var file = input && input.files && input.files[0];
        // Most pictures are already small enough; avoid needless recompression.
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

    function send(form, label) {
        var loading = window.showToast ? window.showToast("loading", label) : null;
        compressPhoto(form).then(function () {
            return fetch(form.action, {
                method: "POST",
                body: new FormData(form),
                headers: { "X-Requested-With": "fetch" }
            });
        })
            .then(function (res) {
                if (!res) throw new Error("Image compression failed.");
                if (res.ok) { window.location.reload(); return; }
                if (res.status === 400) { return res.text().then(openModal); }
                throw new Error("failed");
            })
            .catch(function () {
                if (window.showToast) window.showToast("error", "Could not compress or upload the photo. Try a smaller image.");
            })
            .finally(function () {
                if (loading && window.hideToast) window.hideToast(loading);
            });
    }

    function confirmDelete(form) {
        var name = form.getAttribute("data-confirm");
        openModal(
            '<div class="cl-confirm"><h2 class="cl-modal-title">Delete this item?</h2><p></p>' +
            '<div class="cl-form-actions">' +
            '<button type="button" class="btn primary-btn" data-close>Cancel</button>' +
            '<button type="button" class="btn tertiary-btn" data-confirm-yes>Delete</button>' +
            "</div></div>"
        );
        body.querySelector("p").textContent = '"' + name + "\" will be removed from your closet. This can't be undone.";
        body.querySelector("[data-confirm-yes]").addEventListener("click", function () {
            send(form, "Deleting...");
        });
    }

    document.addEventListener("click", function (e) {
        var btn = e.target.closest(".cl-menu-button");
        if (btn) {
            var list = btn.nextElementSibling;
            var wasOpen = !list.hidden;
            closeMenus();
            list.hidden = wasOpen;
            btn.setAttribute("aria-expanded", String(!wasOpen));
            return;
        }

        var link = e.target.closest("a[data-modal]");
        if (link && overlay) {
            e.preventDefault();
            closeMenus();
            loadModal(link.href);
            return;
        }

        if (e.target.closest("[data-close]")) {
            e.preventDefault();
            closeModal();
            return;
        }
        if (overlay && e.target === overlay) { closeModal(); return; }
        if (!e.target.closest(".cl-menu-list")) closeMenus();
    });

    document.addEventListener("submit", function (e) {
        var form = e.target;

        if (form.hasAttribute("data-confirm")) {
            if (!overlay) {
                // halaman penuh (bukan closet): pakai konfirmasi bawaan browser
                if (!window.confirm('Delete "' + form.getAttribute("data-confirm") + '"?')) e.preventDefault();
                return;
            }
            e.preventDefault();
            closeMenus();
            confirmDelete(form);
            return;
        }

        if (form.hasAttribute("data-modal-form")) {
            e.preventDefault();
            send(form, "Saving...");
            return;
        }

        if (form.matches(".cl-form") && form.querySelector("#photo-input")) {
            e.preventDefault();
            compressPhoto(form).then(function () {
                form.submit();
            }).catch(function () {
                if (window.showToast) window.showToast("error", "Could not compress the photo. Try a smaller image.");
            });
        }
    });

    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") { closeMenus(); closeModal(); }
    });

    /* all year round gaboleh dipilih barengan sama musim lain */
    document.addEventListener("change", function (e) {
        var input = e.target;
        if (!input.matches || !input.matches('input[name="seasons"]') || !input.checked) return;
        var ALL_YEAR = "All year round";
        input.form.querySelectorAll('input[name="seasons"]').forEach(function (other) {
            if (other !== input && (input.value === ALL_YEAR || other.value === ALL_YEAR)) {
                other.checked = false;
            }
        });
    });

    /* format harga jd ada pemisah dengan . */
    function formatMoney(input) {
        input.value = input.value.replace(/\D/g, "").replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    }
    document.addEventListener("input", function (e) {
        if (e.target.matches && e.target.matches("[data-money]")) formatMoney(e.target);
    });
    document.querySelectorAll("[data-money]").forEach(formatMoney);

    /* filter */
    document.addEventListener("change", function (e) {
        if (e.target.matches && e.target.matches("select[data-autosubmit]")) {
            e.target.form.submit();
        }
    });

    /* auto redirect/sync parameter URL 'category' ke 'cat' jika dikirim dari community */
    (function syncUrlParams() {
        var params = new URLSearchParams(window.location.search);
        var categoryParam = params.get("category");
        
        if (categoryParam && !params.get("cat")) {
            params.set("cat", categoryParam);
            params.delete("category");
            window.location.search = params.toString();
        }
    })();
})();
