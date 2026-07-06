/* ============================================================
   charts.js - رسوم بيانية للوحة التحكم (باستخدام Chart.js)
   بيجيب البيانات من reports API اللي في reports_routes.py
   ============================================================ */

document.addEventListener("DOMContentLoaded", function () {
    renderMonthlyChart();
    renderStatusChart();
});

const CHART_COLORS = {
    primary: "#0E4D46",
    accent: "#B8892B",
    danger: "#A23B3B",
    grid: "#D3DBD6",
    text: "#3C4F49",
};

async function renderMonthlyChart() {
    const canvas = document.getElementById("monthlyChart");
    if (!canvas || typeof Chart === "undefined") return;

    const res = await fetch("/reports/api/monthly-summary");
    const data = await res.json();

    new Chart(canvas, {
        type: "bar",
        data: {
            labels: data.map(d => d.month),
            datasets: [
                {
                    label: "الإيرادات",
                    data: data.map(d => parseFloat(d.revenue) || 0),
                    backgroundColor: CHART_COLORS.primary,
                    borderRadius: 4,
                },
                {
                    label: "المصروفات",
                    data: data.map(d => parseFloat(d.expense) || 0),
                    backgroundColor: CHART_COLORS.accent,
                    borderRadius: 4,
                },
            ],
        },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: CHART_COLORS.text, font: { family: "Cairo" } } },
            },
            scales: {
                x: { grid: { display: false }, ticks: { color: CHART_COLORS.text } },
                y: { grid: { color: CHART_COLORS.grid }, ticks: { color: CHART_COLORS.text } },
            },
        },
    });
}

async function renderStatusChart() {
    const canvas = document.getElementById("statusChart");
    if (!canvas || typeof Chart === "undefined") return;

    const res = await fetch("/reports/api/invoice-status-breakdown");
    const data = await res.json();

    const statusLabels = { draft: "مسودة", confirmed: "مؤكدة", paid: "مدفوعة", cancelled: "ملغاة" };
    const statusColors = { draft: "#B0B8B4", confirmed: CHART_COLORS.primary, paid: "#2F7A4F", cancelled: CHART_COLORS.danger };

    new Chart(canvas, {
        type: "doughnut",
        data: {
            labels: data.map(d => statusLabels[d.status] || d.status),
            datasets: [{
                data: data.map(d => d.count),
                backgroundColor: data.map(d => statusColors[d.status] || "#999"),
                borderWidth: 2,
                borderColor: "#fff",
            }],
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: "bottom", labels: { color: CHART_COLORS.text, font: { family: "Cairo" } } },
            },
        },
    });
}
