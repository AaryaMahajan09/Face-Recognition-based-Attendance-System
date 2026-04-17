function loadDashboard() {

    loadChart({
        url: "/weekly_attendance",
        canvasId: "attendanceChart",
        type: "line",
        label: "Weekly %",
        transformLabels: (data) => {
            const days = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
            return data.labels.map(d => {
                let date = new Date(d);
                return days[date.getDay()];
            });
        },
        transformData: (data) => data.values
    });

    loadChart({
        url: "/subject_attendance",
        canvasId: "subjectChart",
        type: "bar",
        label: "Subject %",
        transformLabels: (data) => data.subjects.map(s => s.subject),
        transformData: (data) => data.subjects.map(s => s.percentage)
    });
}

function checkAttendanceStatus(percentage, attended, total) {
    const warningBox = document.getElementById("attendanceWarning");
    const text = document.getElementById("warningText");

    const required = 75;

    if (percentage >= required) {
        warningBox.style.border = "1px solid #22c55e";
        text.innerHTML = "✅ You are safe. Keep it up!";
    } else {
        let needed = 0;
        let newAttended = attended;
        let newTotal = total;

        while ((newAttended / newTotal) * 100 < required) {
            newAttended++;
            newTotal++;
            needed++;
        }

        warningBox.style.border = "1px solid #ef4444";
        text.innerHTML = `⚠️ You need <b>${needed}</b> more classes to reach 75%`;
    }
}

document.addEventListener("DOMContentLoaded", () => {

    const dashboardData = JSON.parse(
        document.getElementById("dashboard-data").textContent
    );
    
    loadDashboard();

    checkAttendanceStatus(
        dashboardData.percentage,
        dashboardData.attended,
        dashboardData.total
    );
});