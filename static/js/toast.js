(function () {
    "use strict";
    var stack = document.getElementById("toast-stack");
    if (!stack) return;

    var ICONS = { success: "fa-circle-check", error: "fa-circle-exclamation", loading: "fa-spinner fa-spin" };

    function dismiss(toast) {
        clearTimeout(toast._toastTimer);
        toast.classList.add("is-leaving");
        setTimeout(function () { toast.remove(); }, 250);
    }
    function arm(toast) {
        clearTimeout(toast._toastTimer);
        toast._toastTimer = setTimeout(function () { dismiss(toast); }, 4000);
    }

    stack.querySelectorAll(".toast").forEach(arm);

    window.showToast = function (type, text) {
        var t = document.createElement("div");
        t.className = "toast toast-" + type;
        t.setAttribute("role", "status");
        var icon = document.createElement("i");
        icon.className = "fa-solid " + ICONS[type];
        var span = document.createElement("span");
        span.textContent = text;
        t.appendChild(icon);
        t.appendChild(span);
        stack.appendChild(t);
        if (type !== "loading") arm(t);
        return t;
    };
    window.updateToast = function (toast, type, text) {
        if (!toast || !toast.isConnected) return window.showToast(type, text);
        toast.classList.remove("toast-success", "toast-error", "toast-loading", "is-leaving");
        toast.classList.add("toast-" + type);
        var icon = toast.querySelector("i");
        var span = toast.querySelector("span");
        if (icon) icon.className = "fa-solid " + ICONS[type];
        if (span) span.textContent = text;
        clearTimeout(toast._toastTimer);
        if (type !== "loading") arm(toast);
        return toast;
    };
    window.hideToast = dismiss;
})();
