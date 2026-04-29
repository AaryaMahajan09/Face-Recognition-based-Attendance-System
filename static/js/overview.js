// overview.js
// Populates all dynamic elements on the Overview page.
// All data comes from /overview_data which is now scoped
// to the logged-in teacher's lectures only.

document.addEventListener("DOMContentLoaded", async () => {

    const data = await fetchData("/overview_data");
    if (!data) return;

    // ── Top stat cards
    document.getElementById("totalStudents").innerText = data.total_students;
    document.getElementById("avgAttendance").innerText = data.average + "%";

    // ── Student attendance bars
    const container = document.getElementById("studentBars");
    container.innerHTML = "";

    if (!data.students || data.students.length === 0) {
        container.innerHTML = `<p style="color:#94a3b8;font-size:14px;">No lecture data yet.</p>`;
    } else {
        data.students.forEach(s => {
            const color = s.percentage >= 80 ? "#22c55e" : "#ef4444";
            container.innerHTML += `
                <div class="bar-row">
                    <div class="bar-label">${s.name}</div>
                    <div class="bar">
                        <div class="fill" style="width:${s.percentage}%;background:${color};"></div>
                    </div>
                    <div style="min-width:40px;text-align:right;font-size:13px;color:${color};">
                        ${s.percentage}%
                    </div>
                </div>
            `;
        });
    }

    // ── Low attendance students
    const low = document.getElementById("lowStudents");
    low.innerHTML = "";

    if (!data.low_students || data.low_students.length === 0) {
        low.innerHTML = `<p style="color:#22c55e;font-size:14px;">✓ All students are above 80%</p>`;
    } else {
        data.low_students.forEach(s => {
            low.innerHTML += `
                <div class="student">
                    <div class="student-left">
                        <div class="badge">${s.name[0]}</div>
                        ${s.name}
                    </div>
                    <span class="danger">${s.percentage}%</span>
                </div>
            `;
        });
    }

    // ── Doughnut chart: Present vs Absent
    createChart(
        "pie",
        "doughnut",
        ["Present", "Absent"],
        [data.present, data.absent],
        "Attendance"
    );

    // ── 🔥 NEW: Subject attendance bar chart
    if (data.subjects && data.subjects.length > 0) {
        const subCtx = document.getElementById("subjectChart");
        if (subCtx) {
            new Chart(subCtx, {
                type: "bar",
                data: {
                    labels: data.subjects.map(s => s.subject),
                    datasets: [
                        {
                            label: "Present %",
                            data: data.subjects.map(s => s.percentage),
                            backgroundColor: data.subjects.map(s =>
                                s.percentage >= 80 ? "#22c55e" : "#ef4444"
                            ),
                            borderRadius: 6,
                            barThickness: 28
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
                                label(ctx) {
                                    const s = data.subjects[ctx.dataIndex];
                                    return [
                                        `Attendance: ${ctx.raw}%`,
                                        `Present: ${s.present} / ${s.total}`
                                    ];
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: { color: "#94a3b8" }
                        },
                        y: {
                            beginAtZero: true,
                            max: 100,
                            ticks: {
                                color: "#94a3b8",
                                callback: v => v + "%"
                            },
                            grid: { color: "#1e293b" }
                        }
                    }
                }
            });
        }
    } else {
        const subCtx = document.getElementById("subjectChart");
        if (subCtx) {
            subCtx.insertAdjacentHTML("afterend",
                `<p style="color:#94a3b8;font-size:14px;margin-top:8px;">No subject data yet.</p>`
            );
            subCtx.style.display = "none";
        }
    }

    // ── 🔥 NEW: Lecture history table
    const tbody = document.getElementById("lectureHistoryBody");
    if (tbody) {
        if (!data.history || data.history.length === 0) {
            tbody.innerHTML = `
                <tr>
                  <td colspan="6" style="padding:16px 8px;color:#94a3b8;">
                    No completed lectures yet.
                  </td>
                </tr>`;
        } else {
            tbody.innerHTML = data.history.map((h, i) => {
                const rateColor = h.percentage >= 80 ? "#22c55e" : "#ef4444";
                return `
                    <tr style="border-bottom:1px solid #1e293b;">
                        <td style="padding:10px 8px;color:#94a3b8;">${i + 1}</td>
                        <td style="padding:10px 8px;color:#e2e8f0;font-weight:500;">${h.subject}</td>
                        <td style="padding:10px 8px;color:#94a3b8;">${h.date ?? "--"}</td>
                        <td style="padding:10px 8px;color:#22c55e;">${h.present}</td>
                        <td style="padding:10px 8px;color:#ef4444;">${h.absent}</td>
                        <td style="padding:10px 8px;color:${rateColor};font-weight:600;">${h.percentage}%</td>
                    </tr>
                `;
            }).join("");
        }
    }

});