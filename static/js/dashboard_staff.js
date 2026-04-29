document.addEventListener("DOMContentLoaded", function () {

    const el = document.getElementById("weekly-data");
    if (!el) {
        console.error("❌ weekly-data script not found");
        return;
    }

    let raw;
    try {
        raw = JSON.parse(el.textContent);
    } catch (e) {
        console.error("❌ JSON parse error:", e);
        return;
    }

    console.log("📊 Weekly Data:", raw);

    // 🔹 Extract values
    const labels = raw.map(d => d.day);
    const present = raw.map(d => d.present);
    const absent = raw.map(d => d.absent);

    // 🔥 Find max value for proper scaling
    const maxValue = Math.max(...present, ...absent, 5);

    const ctx = document.getElementById('attendanceChart');
    if (!ctx) {
        console.error("❌ Canvas not found");
        return;
    }

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Present',
                    data: present,
                    backgroundColor: '#22c55e',
                    borderRadius: 6,
                    barThickness: 18
                },
                {
                    label: 'Absent',
                    data: absent,
                    backgroundColor: '#ef4444',
                    borderRadius: 6,
                    barThickness: 18
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,

            plugins: {
                legend: { display: false },

                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const value = context.raw;
                            if (value === 0) return "No Lecture / No Data";
                            return context.dataset.label + ": " + value;
                        }
                    }
                }
            },

            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' }
                },

                y: {
                    beginAtZero: true,
                    suggestedMax: maxValue + 2,   // 🔥 dynamic scaling
                    ticks: {
                        stepSize: 1,
                        color: '#94a3b8'
                    },
                    grid: { color: '#1e293b' }
                }
            }
        }
    });

});