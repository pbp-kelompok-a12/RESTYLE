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

    function send(form, label) {
        var loading = window.showToast ? window.showToast("loading", label) : null;
        fetch(form.action, {
            method: "POST",
            body: new FormData(form),
            headers: { "X-Requested-With": "fetch" }
        })
            .then(function (res) {
                if (res.ok) { window.location.reload(); return; }
                if (res.status === 400) { return res.text().then(openModal); }
                throw new Error("failed");
            })
            .catch(function () {
                if (window.showToast) window.showToast("error", "Something went wrong. Please try again.");
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
            '<button type="button" class="btn tertiary-btn" data-close>Cancel</button>' +
            '<button type="button" class="btn primary-btn" data-confirm-yes>Delete</button>' +
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
})();