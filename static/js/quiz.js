// Style quiz: satu pertanyaan per layar, lalu layar hasil persona sebelum dikirim.
// Tanpa JS, semua pertanyaan tampil sekaligus dan form tetap bisa dikirim seperti biasa.
(function () {
    const form = document.getElementById("quizForm");
    if (!form) return;

    const steps = [...form.querySelectorAll(".quiz-step")];
    const questionCount = steps.length - 1; // langkah terakhir = layar hasil
    const backButton = form.querySelector(".quiz-back");
    const nextButton = form.querySelector(".quiz-next");
    const progressFill = document.querySelector(".quiz-progress-fill");
    const progressLabel = document.querySelector(".quiz-progress-label");
    const personas = JSON.parse(document.getElementById("quiz-personas").textContent);
    let current = 0;
    let advanceTimer = null;
    let pickedWithPointer = false; // lanjut otomatis hanya kalau jawaban dipilih dengan klik / ketukan

    form.classList.add("is-stepped"); // CSS baru menyembunyikan langkah lain setelah class ini ada

    function stepAnswered(index) {
        return Boolean(steps[index].querySelector("input:checked"));
    }

    function fillResult() {
        const style = form.querySelector("input[name='style_persona']:checked");
        const persona = personas[style ? style.value : "Minimal"] || personas.Minimal;
        const result = steps[questionCount];
        result.querySelector(".quiz-result-icon i").className = "fa-solid " + persona.icon;
        result.querySelector(".quiz-result-title").textContent = persona.title;
        result.querySelector(".quiz-result-description").textContent = persona.description;
    }

    function show(index, moveFocus = true) {
        clearTimeout(advanceTimer);
        current = index;
        const onResult = index === questionCount;
        if (onResult) fillResult();

        steps.forEach((step, i) => {
            step.hidden = i !== index;
            step.classList.toggle("is-active", i === index);
        });

        backButton.hidden = index === 0;
        nextButton.hidden = onResult;
        nextButton.disabled = !onResult && !stepAnswered(index);
        form.classList.toggle("is-result", onResult);

        const done = onResult ? questionCount : index;
        progressFill.style.width = `${(done / questionCount) * 100}%`;
        progressLabel.textContent = onResult ? "All done!" : `Step ${index + 1} of ${questionCount}`;

        // pindahkan fokus ke judul langkah, supaya pembaca layar ikut membaca pertanyaan baru
        const heading = steps[index].querySelector("legend, h2");
        if (heading && moveFocus) {
            heading.setAttribute("tabindex", "-1");
            heading.focus({ preventScroll: true });
        }
    }

    // memilih jawaban: tombol Next aktif, lalu lanjut otomatis sebentar kemudian
    form.addEventListener("pointerdown", () => { pickedWithPointer = true; });
    form.addEventListener("keydown", () => { pickedWithPointer = false; });

    form.addEventListener("change", (event) => {
        if (event.target.type !== "radio") return;
        nextButton.disabled = false;
        clearTimeout(advanceTimer);
        // dengan keyboard (tombol panah), tunggu sampai pengguna menekan Next sendiri
        if (pickedWithPointer) advanceTimer = setTimeout(() => show(current + 1), 450);
    });

    nextButton.addEventListener("click", () => {
        if (stepAnswered(current)) show(current + 1);
    });

    backButton.addEventListener("click", () => {
        if (current > 0) show(current - 1);
    });

    show(0, false);
})();
