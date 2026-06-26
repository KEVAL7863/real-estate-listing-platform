// Favorite toggle via AJAX
document.addEventListener("click", function (e) {
    const btn = e.target.closest(".fav-btn[data-url]");
    if (!btn) return;
    e.preventDefault();

    fetch(btn.dataset.url, {
        method: "GET",
        headers: { "X-Requested-With": "XMLHttpRequest" },
    })
        .then((r) => {
            if (r.status === 403 || r.redirected) {
                window.location.href = "/accounts/login/";
                throw new Error("login required");
            }
            return r.json();
        })
        .then((data) => {
            btn.classList.toggle("active", data.favorited);
            const icon = btn.querySelector("i");
            if (icon) {
                icon.className = data.favorited ? "bi bi-heart-fill" : "bi bi-heart";
            }
        })
        .catch(() => {});
});

// Auto-scroll chat to bottom
const chat = document.querySelector(".chat-box");
if (chat) chat.scrollTop = chat.scrollHeight;

// Fade-in on load
window.addEventListener("load", () => {
    document.querySelectorAll(".fade-up").forEach((el, i) => {
        el.style.animationDelay = `${i * 0.05}s`;
    });
});
