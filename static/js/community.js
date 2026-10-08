// kotak tulis post: tombol post, pilih foto, dan preview foto

const composer = document.querySelector("#composer");

if (composer) {
    const textarea = composer.querySelector("textarea");
    const postButton = composer.querySelector("#post-button");
    const photoButton = composer.querySelector("#photo-button");
    const photoInput = composer.querySelector("#photo-input");
    const previews = composer.querySelector("#photo-previews");
    const hint = composer.querySelector("#photo-hint");

    const MAX_PHOTOS = 3;
    let photos = []; // daftar foto yang sedang dipilih

    // tombol post baru aktif kalau sudah ada tulisan
    function updatePostButton() {
        postButton.disabled = textarea.value.trim() === "";
    }

    // kotak tulisan ikut meninggi mengikuti isinya
    function resizeTextarea() {
        textarea.style.height = "auto";
        textarea.style.height = textarea.scrollHeight + "px";
    }

    // gambar ulang preview dan menyamakan isi input file dengan daftar foto
    function showPhotos() {
        const transfer = new DataTransfer();
        photos.forEach((photo) => transfer.items.add(photo));
        photoInput.files = transfer.files;

        previews.innerHTML = "";
        photos.forEach((photo, index) => {
            const item = document.createElement("div");
            item.className = "cm-photo-preview";

            const image = document.createElement("img");
            image.src = URL.createObjectURL(photo);
            image.alt = photo.name;

            const removeButton = document.createElement("button");
            removeButton.type = "button";
            removeButton.setAttribute("aria-label", "Remove photo");
            removeButton.innerHTML = '<i class="fa-solid fa-xmark"></i>';
            removeButton.addEventListener("click", () => {
                photos.splice(index, 1);
                hint.hidden = true;
                showPhotos();
            });

            item.append(image, removeButton);
            previews.append(item);
        });

        previews.hidden = photos.length === 0;
    }

    textarea.addEventListener("input", () => {
        updatePostButton();
        resizeTextarea();
    });

    photoButton.addEventListener("click", () => photoInput.click());

    photoInput.addEventListener("change", () => {
        photos = photos.concat(Array.from(photoInput.files));

        if (photos.length > MAX_PHOTOS) {
            photos = photos.slice(0, MAX_PHOTOS);
            hint.textContent = "Up to 3 photos per post. Extra photos were left out.";
            hint.hidden = false;
        } else {
            hint.hidden = true;
        }

        showPhotos();
    });

    updatePostButton();
}


// comment: buka-tutup daftar komentar dan kotak balasan.

function setCommentsOpen(post, isOpen) {
    post.querySelector(".cm-comments").hidden = !isOpen;
    post.querySelector(".cm-toggle-comments").setAttribute("aria-expanded", String(isOpen));
}

// button "replies" di tiap post membuka atau menutup commentnya
document.querySelectorAll(".cm-post").forEach((post) => {
    post.querySelector(".cm-toggle-comments").addEventListener("click", () => {
        const isOpenNow = !post.querySelector(".cm-comments").hidden;
        setCommentsOpen(post, !isOpenNow);
    });
});


// button "Reply" di bawah comment nampilin kotak balasan kecil
document.querySelectorAll(".cm-toggle-reply").forEach((button) => {
    const form = button.closest(".cm-comment-main").querySelector(".cm-reply-inline");

    button.addEventListener("click", () => {
        form.hidden = !form.hidden;
        if (!form.hidden) {
            form.querySelector('input[name="content"]').focus();
        }
    });
});


// setelah ngirim comment, alamat halaman berakhiran #post-12
// komentar post itu langsung dibuka supaya komentar barunya terlihat
if (location.hash.startsWith("#post-")) {
    const post = document.getElementById(location.hash.slice(1));
    if (post) {
        setCommentsOpen(post, true);
    }
}

// edit: tombol "Edit" menukar tulisan dengan kotak edit, "Cancel" mengembalikannya
document.querySelectorAll(".cm-toggle-edit").forEach((button) => {
    const box = button.closest(".cm-post-main, .cm-comment-main");
    const view = box.querySelector(".cm-editable");
    const form = box.querySelector(".cm-edit-form");

    function setEditing(isEditing) {
        form.hidden = !isEditing;
        view.hidden = isEditing;
        if (isEditing) {
            form.querySelector("textarea").focus();
        }
    }

    button.addEventListener("click", () => setEditing(form.hidden));
    form.querySelector(".cm-cancel-edit").addEventListener("click", () => setEditing(false));
});


// Hapus: tanya dulu sebelum benar-benar menghapus
document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
        if (!confirm(form.dataset.confirm)) {
            event.preventDefault();
        }
    });
});


// Menu titik tiga: buka-tutup, dan tutup otomatis saat klik di luar atau tekan Escape.
function closeAllMenus() {
    document.querySelectorAll(".cm-menu-list").forEach((list) => {
        list.hidden = true;
    });
    document.querySelectorAll(".cm-menu-button").forEach((button) => {
        button.setAttribute("aria-expanded", "false");
    });
}

document.querySelectorAll(".cm-menu").forEach((menu) => {
    const button = menu.querySelector(".cm-menu-button");
    const list = menu.querySelector(".cm-menu-list");

    button.addEventListener("click", (event) => {
        event.stopPropagation(); // supaya klik ini ga dianggap "klik di luar"
        const willOpen = list.hidden;
        closeAllMenus();
        list.hidden = !willOpen;
        button.setAttribute("aria-expanded", String(willOpen));
    });
});

document.addEventListener("click", closeAllMenus);

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        closeAllMenus();
    }
});