const installButton = document.getElementById("install-button");
const topMetrics = document.getElementById("top-metrics");
const weeklyNarrative = document.getElementById("weekly-narrative");
const bestDayNarrative = document.getElementById("best-day-narrative");
const worstDayNarrative = document.getElementById("worst-day-narrative");
const weeklyComparison = document.getElementById("weekly-comparison");
const bestDays = document.getElementById("best-days");
const worstDays = document.getElementById("worst-days");
const fatigueAlerts = document.getElementById("fatigue-alerts");
const form = document.getElementById("manual-checkin-form");
const formStatus = document.getElementById("form-status");

let deferredPrompt = null;

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

function createMetricTile(label, value) {
  const div = document.createElement("div");
  div.className = "metric-tile";
  div.innerHTML = `<span>${label}</span><strong>${value}</strong>`;
  return div;
}

function renderListRows(container, rows, formatter) {
  container.innerHTML = "";
  if (!rows.length) {
    container.innerHTML = `<div class="mini-item"><small>Sin datos disponibles.</small></div>`;
    return;
  }
  rows.forEach((row) => {
    const div = document.createElement("div");
    div.className = "mini-item";
    div.innerHTML = formatter(row);
    container.appendChild(div);
  });
}

async function loadDashboard() {
  try {
    const [daily, weekly, best, worst, alerts, weeklyText, bestText, worstText] = await Promise.all([
      fetchJson("/daily"),
      fetchJson("/performance/weekly-comparison"),
      fetchJson("/performance/best-days"),
      fetchJson("/performance/worst-days"),
      fetchJson("/performance/fatigue-alerts"),
      fetchJson("/narrative/weekly"),
      fetchJson("/narrative/best-day"),
      fetchJson("/narrative/worst-day"),
    ]);

    const latest = daily.rows[daily.rows.length - 1] || {};
    topMetrics.innerHTML = "";
    [
      ["Sueno", `${Number(latest.duration_hours || 0).toFixed(1)} h`],
      ["HRV", `${Number(latest.overnight_avg || 0).toFixed(1)}`],
      ["Resting HR", `${Number(latest.resting_hr_bpm || 0).toFixed(1)} bpm`],
      ["Pasos", `${Number(latest.steps || 0).toFixed(0)}`],
      ["Carga", `${Number(latest.total_training_load || 0).toFixed(0)}`],
    ].forEach(([label, value]) => topMetrics.appendChild(createMetricTile(label, value)));

    weeklyNarrative.textContent = weeklyText.message;
    bestDayNarrative.textContent = bestText.message;
    worstDayNarrative.textContent = worstText.message;

    weeklyComparison.innerHTML = "";
    weekly.rows.forEach((row) => {
      const div = document.createElement("div");
      div.className = "list-row";
      div.innerHTML = `
        <strong>${row.metric}</strong>
        <div class="mini-meta">${row.recent} ${row.unit || ""} vs ${row.previous} ${row.unit || ""}</div>
        <span class="pill">${row.direction} ${row.delta > 0 ? "+" : ""}${row.delta}</span>
      `;
      weeklyComparison.appendChild(div);
    });

    renderListRows(bestDays, best.rows, (row) => `
      <strong>${String(row.metric_date).slice(0, 10)}</strong>
      <div class="mini-meta">Sueno ${Number(row.duration_hours || 0).toFixed(1)}h · HRV ${Number(row.overnight_avg || 0).toFixed(1)} · RHR ${Number(row.resting_hr_bpm || 0).toFixed(1)}</div>
    `);

    renderListRows(worstDays, worst.rows, (row) => `
      <strong>${String(row.metric_date).slice(0, 10)}</strong>
      <div class="mini-meta">Sueno ${Number(row.duration_hours || 0).toFixed(1)}h · HRV ${Number(row.overnight_avg || 0).toFixed(1)} · RHR ${Number(row.resting_hr_bpm || 0).toFixed(1)}</div>
    `);

    renderListRows(fatigueAlerts, alerts.rows, (row) => `
      <div class="alert-item ${row.severity}">
        <strong>${row.metric_date}</strong>
        <div class="mini-meta">${row.signals}</div>
        <span class="pill">${row.severity}</span>
      </div>
    `);
  } catch (error) {
    weeklyNarrative.textContent = `No se pudo cargar la PWA: ${error.message}`;
  }
}

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(form).entries());
  for (const [key, value] of Object.entries(payload)) {
    if (value === "") {
      payload[key] = null;
    } else if (["perceived_energy", "work_stress", "muscle_soreness", "hydration", "nutrition_quality", "mood", "strength_training_load"].includes(key)) {
      payload[key] = Number(value);
    }
  }
  try {
    const result = await fetchJson("/manual-checkins", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    formStatus.textContent = result.message;
    loadDashboard();
  } catch (error) {
    formStatus.textContent = `No se pudo guardar: ${error.message}`;
  }
});

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  deferredPrompt = event;
  installButton.classList.remove("hidden");
});

installButton?.addEventListener("click", async () => {
  if (!deferredPrompt) return;
  deferredPrompt.prompt();
  await deferredPrompt.userChoice;
  deferredPrompt = null;
  installButton.classList.add("hidden");
});

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js"));
}

const dateInput = form?.querySelector("input[name='checkin_date']");
if (dateInput) {
  dateInput.value = new Date().toISOString().slice(0, 10);
}

loadDashboard();
