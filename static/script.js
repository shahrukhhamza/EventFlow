document.addEventListener("DOMContentLoaded", () => {
    document.documentElement.classList.add("js-enabled");

    const revealItems = document.querySelectorAll(".reveal-up");

    if (!("IntersectionObserver" in window)) {
        revealItems.forEach((item) => item.classList.add("visible"));
    } else {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("visible");
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.2 }
        );

        revealItems.forEach((item) => observer.observe(item));
    }

    const eventFilterForm = document.querySelector("form[data-event-filter]");

    if (eventFilterForm) {
        const textInput = eventFilterForm.querySelector("input[type='search']");
        const categorySelect = eventFilterForm.querySelector("select");
        let debounceTimer = null;

        if (textInput) {
            textInput.addEventListener("input", () => {
                window.clearTimeout(debounceTimer);
                debounceTimer = window.setTimeout(() => {
                    eventFilterForm.requestSubmit();
                }, 300);
            });
        }

        if (categorySelect) {
            categorySelect.addEventListener("change", () => eventFilterForm.requestSubmit());
        }
    }
});
