import { CarViewer, TEAM_CAR_COLORS } from "./car-viewer.js";

const TEAM_COLORS = Object.fromEntries(
  Object.entries(TEAM_CAR_COLORS).map(([name, palette]) => [name, palette.primary])
);

const refreshBtn = document.getElementById("refresh-btn");
const statusText = document.getElementById("status-text");
const seasonProgress = document.getElementById("season-progress");
const championCard = document.getElementById("champion-card");
const driversBody = document.querySelector("#drivers-table tbody");
const constructorsBody = document.querySelector("#constructors-table tbody");
const driversPanel = document.getElementById("drivers-panel");
const constructorsPanel = document.getElementById("constructors-panel");
const maeValue = document.getElementById("mae-value");
const yearValue = document.getElementById("year-value");
const predictorsList = document.getElementById("predictors-list");
const tabs = document.querySelectorAll(".tab");
const garageStage = document.getElementById("garage-stage");
const garageRank = document.getElementById("garage-rank");
const garageTeamName = document.getElementById("garage-team-name");
const garagePts = document.getElementById("garage-pts");
const garageDrivers = document.getElementById("garage-drivers");
const teamRail = document.getElementById("team-rail");

let latestData = null;
let selectedTeam = null;
const carViewer = new CarViewer(document.getElementById("car-canvas"));

function teamColor(team) {
  return TEAM_COLORS[team] || "#888";
}

function formatPoints(value) {
  return Number(value).toLocaleString(undefined, {
    maximumFractionDigits: 1,
    minimumFractionDigits: 0,
  });
}

function shortTeamName(name) {
  return String(name)
    .replace("Red Bull Racing", "Red Bull")
    .replace("Haas F1 Team", "Haas")
    .replace("Aston Martin", "Aston")
    .replace("Racing Bulls", "R. Bulls")
    .toUpperCase();
}

function podiumClass(rank) {
  if (rank === 1) return "pos podium-1";
  if (rank === 2) return "pos podium-2";
  if (rank === 3) return "pos podium-3";
  return "pos";
}

function driversForTeam(teamName, drivers) {
  return drivers
    .filter((d) => d.TeamName === teamName)
    .sort((a, b) => b.predicted_points - a.predicted_points);
}

function selectTeam(teamName) {
  if (!latestData) return;
  selectedTeam = teamName;

  const constructor = latestData.constructors.find((c) => c.TeamName === teamName);
  if (!constructor) return;

  const drivers = driversForTeam(teamName, latestData.drivers);
  const color = teamColor(teamName);

  garageStage.style.setProperty("--team-bg", color);
  garageRank.textContent = String(constructor.predicted_rank);
  garageTeamName.textContent = `${constructor.predicted_rank}. ${shortTeamName(teamName)}`;
  garagePts.textContent = `${formatPoints(constructor.predicted_points)} PTS`;
  garageDrivers.textContent = drivers.map((d) => d.FullName).join("  ·  ") || "Drivers TBA";

  carViewer.setTeam(teamName);

  teamRail.querySelectorAll(".team-chip").forEach((chip) => {
    chip.classList.toggle("active", chip.dataset.team === teamName);
  });
}

function renderTeamRail(constructors) {
  teamRail.innerHTML = constructors
    .map(
      (c) => `
      <button
        class="team-chip"
        type="button"
        role="tab"
        data-team="${c.TeamName}"
        style="--chip-color:${teamColor(c.TeamName)}"
      >
        <span class="chip-rank">${c.predicted_rank}</span>
        <span class="chip-name">${shortTeamName(c.TeamName)}</span>
      </button>
    `
    )
    .join("");

  teamRail.querySelectorAll(".team-chip").forEach((chip) => {
    chip.addEventListener("click", () => selectTeam(chip.dataset.team));
  });
}

function renderGarage(data) {
  latestData = data;
  renderTeamRail(data.constructors);

  const preferred =
    (selectedTeam && data.constructors.some((c) => c.TeamName === selectedTeam) && selectedTeam) ||
    data.champion?.constructor?.TeamName ||
    data.constructors[0]?.TeamName;

  if (preferred) selectTeam(preferred);
}

function renderChampion(data) {
  const driver = data.champion?.driver;
  if (!driver) {
    championCard.innerHTML = `
      <div class="panel-label">Projected champion</div>
      <div class="champion-skeleton">No prediction available</div>
    `;
    return;
  }

  championCard.innerHTML = `
    <div class="panel-label">Projected champion · ${data.year}</div>
    <div class="champion-rank">P${driver.predicted_rank}</div>
    <h2 class="champion-name">${driver.FullName}</h2>
    <p class="champion-team">${driver.TeamName}</p>
    <div class="champion-points">
      <strong>${formatPoints(driver.predicted_points)}</strong>
      <span>predicted pts</span>
    </div>
  `;
}

function renderDrivers(drivers) {
  driversBody.innerHTML = drivers
    .map(
      (d) => `
      <tr>
        <td class="${podiumClass(d.predicted_rank)}">${d.predicted_rank}</td>
        <td>
          <div class="driver-cell">
            <span class="driver-name">${d.FullName}</span>
            <span class="driver-code">${d.Abbreviation}</span>
          </div>
        </td>
        <td>
          <div class="team-cell">
            <span class="team-swatch" style="background:${teamColor(d.TeamName)}"></span>
            <span>${d.TeamName}</span>
          </div>
        </td>
        <td class="pts">${formatPoints(d.PreviousPoints)}</td>
        <td class="pts">${d.current_rank}</td>
        <td class="pts predicted">${formatPoints(d.predicted_points)}</td>
      </tr>
    `
    )
    .join("");
}

function renderConstructors(constructors) {
  constructorsBody.innerHTML = constructors
    .map(
      (c) => `
      <tr>
        <td class="${podiumClass(c.predicted_rank)}">${c.predicted_rank}</td>
        <td>
          <div class="team-cell">
            <span class="team-swatch" style="background:${teamColor(c.TeamName)}"></span>
            <span>${c.TeamName}</span>
          </div>
        </td>
        <td class="pts predicted">${formatPoints(c.predicted_points)}</td>
      </tr>
    `
    )
    .join("");
}

function renderModelMeta(data) {
  maeValue.textContent = data.mae.toFixed(1);
  yearValue.textContent = String(data.year);

  const labels = {
    points_so_far: "points so far",
    avg_points_per_race: "avg points / race",
    current_rank: "current rank",
    PreviousPoints: "previous season points",
  };

  predictorsList.innerHTML = (data.predictors || [])
    .map((p) => `<li>${labels[p] || p}</li>`)
    .join("");
}

function renderSeasonProgress(data) {
  const season = data.season || {};
  const completedName = season.latest_completed_name || `Race ${data.up_to_race}`;
  const nextBit = season.next_race
    ? ` · next: R${season.next_race} ${season.next_race_name}`
    : " · season complete";

  seasonProgress.textContent = `Through R${data.up_to_race} ${completedName}${nextBit}`;
}

async function loadPredictions({ refresh = false } = {}) {
  statusText.textContent = refresh ? "Refreshing live data…" : "Running model…";
  statusText.classList.remove("error");
  refreshBtn.disabled = true;

  const params = new URLSearchParams({ year: "2026" });
  if (refresh) params.set("refresh", "1");

  try {
    const res = await fetch(`/api/predictions?${params.toString()}`);
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || "Request failed");
    }

    renderChampion(data);
    renderDrivers(data.drivers);
    renderConstructors(data.constructors);
    renderModelMeta(data);
    renderSeasonProgress(data);
    renderGarage(data);

    statusText.textContent = `Auto-updated · through race ${data.up_to_race} · MAE ${data.mae} pts`;
  } catch (err) {
    statusText.textContent = err.message;
    statusText.classList.add("error");
    championCard.innerHTML = `
      <div class="panel-label">Projected champion</div>
      <div class="champion-skeleton">Could not load predictions</div>
    `;
  } finally {
    refreshBtn.disabled = false;
  }
}

function switchTab(name) {
  tabs.forEach((tab) => {
    const active = tab.dataset.tab === name;
    tab.classList.toggle("active", active);
    tab.setAttribute("aria-selected", active ? "true" : "false");
  });

  const showDrivers = name === "drivers";
  driversPanel.classList.toggle("hidden", !showDrivers);
  constructorsPanel.classList.toggle("hidden", showDrivers);
  driversPanel.hidden = !showDrivers;
  constructorsPanel.hidden = showDrivers;
}

tabs.forEach((tab) => {
  tab.addEventListener("click", () => switchTab(tab.dataset.tab));
});

refreshBtn.addEventListener("click", () => loadPredictions({ refresh: true }));

loadPredictions();
