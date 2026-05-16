document.addEventListener("DOMContentLoaded", () => {
    const revealItems = document.querySelectorAll(".reveal-up");

    if (!("IntersectionObserver" in window)) {
        revealItems.forEach((item) => item.classList.add("visible"));
        return;
    }

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
});
