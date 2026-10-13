// LocalDrop: Dark Mode and Table Interactions

document.addEventListener("DOMContentLoaded", () => {
    // Theme Switcher
    const themeBtn = document.getElementById("themeToggle");
    const savedTheme = localStorage.getItem("localdrop-theme") || "light";
    document.documentElement.setAttribute("data-theme", savedTheme);

    if (themeBtn) {
        themeBtn.textContent = savedTheme === "dark" ? "Light mode" : "Dark mode";
        themeBtn.addEventListener("click", () => {
            const currentTheme = document.documentElement.getAttribute("data-theme");
            const newTheme = currentTheme === "dark" ? "light" : "dark";
            document.documentElement.setAttribute("data-theme", newTheme);
            localStorage.setItem("localdrop-theme", newTheme);
            themeBtn.textContent = newTheme === "dark" ? "Light mode" : "Dark mode";
        });
    }

    // Chart.js Default styling tweaks for academic sober look
    if (window.Chart) {
        Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif';
        Chart.defaults.font.size = 12;
        Chart.defaults.color = '#475569';
        Chart.defaults.plugins.legend.labels.boxWidth = 12;
        Chart.defaults.plugins.legend.labels.boxHeight = 12;
    }
});
