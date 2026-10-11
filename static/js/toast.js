(function () {
    "use strict";
    var stack = document.getElementById("toast-stack");
    if (!stack) return;

    var ICONS = { success: "fa-circle-check", error: "fa-circle-exclamation", loading: "fa-spinner fa-spin" };

    function dismiss(toast) {
        toast.classList.add("is-leaving");
        setTimeout(function () { toast.remove(); }, 250);
    }
    function arm(toast) { setTimeout(function () { dismiss(toast); }, 4000); }

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
    window.hideToast = dismiss;
})();