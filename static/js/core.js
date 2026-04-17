// ==========================
// UNIVERSAL FETCH
// ==========================
async function fetchData(url) {
    try {
        const res = await fetch(url);
        if (!res.ok) throw new Error("Fetch failed");
        return await res.json();
    } catch (err) {
        console.error("Error:", err);
        return null;
    }
}

// ==========================
// CHART STORAGE
// ==========================
let charts = {};

// ==========================
// CREATE CHART
// ==========================
function createChart(canvasId, type, labels, data, labelName) {
    if (charts[canvasId]) {
        charts[canvasId].destroy();
    }

    const ctx = document.getElementById(canvasId);

    charts[canvasId] = new Chart(ctx, {
        type,
        data: {
            labels,
            datasets: [{
                label: labelName,
                data,
                tension: 0.4,
                fill: true
            }]
        }
    });
}

// ==========================
// UNIVERSAL LOADER
// ==========================
async function loadChart(config) {
    const data = await fetchData(config.url);
    if (!data) return;

    createChart(
        config.canvasId,
        config.type,
        config.transformLabels(data),
        config.transformData(data),
        config.label
    );
}