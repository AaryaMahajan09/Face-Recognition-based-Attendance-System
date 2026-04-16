new Chart(document.getElementById("weeklyChart"), {
    type: "bar",
    data: {
        labels: weeklyData.labels,
        datasets: [
            {
                label: "Present",
                data: weeklyData.present,
                backgroundColor: "#22c55e"
            },
            {
                label: "Absent",
                data: weeklyData.absent,
                backgroundColor: "#ef4444"
            }
        ]
    },
    options: {
        responsive: true,
        scales: {
            x: { grid: { display: false } },
            y: { beginAtZero: true, max: total_students }
        },
        plugins: { legend: { display: false } }
    }
});