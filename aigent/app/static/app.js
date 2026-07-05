const dataStatus = document.querySelector("#dataStatus");
const searchInput = document.querySelector("#searchInput");
const positionSelect = document.querySelector("#positionSelect");
const presetSelect = document.querySelector("#presetSelect");
const regionSelect = document.querySelector("#regionSelect");
const nationalitySelect = document.querySelector("#nationalitySelect");
const leagueSelect = document.querySelector("#leagueSelect");
const maxAgeInput = document.querySelector("#maxAgeInput");
const maxValueInput = document.querySelector("#maxValueInput");
const refreshButton = document.querySelector("#refreshButton");
const positionSummary = document.querySelector("#positionSummary");
const positionCategoryButtons = document.querySelector("#positionCategoryButtons");
const playerRows = document.querySelector("#playerRows");
const playerCard = document.querySelector("#playerCard");
const scoreBars = document.querySelector("#scoreBars");
const reportSource = document.querySelector("#reportSource");
const chatLog = document.querySelector("#chatLog");
const chatForm = document.querySelector("#chatForm");
const chatInput = document.querySelector("#chatInput");
const teamLeagueSelect = document.querySelector("#teamLeagueSelect");
const teamClubSelect = document.querySelector("#teamClubSelect");
const formationSelect = document.querySelector("#formationSelect");
const tacticSelect = document.querySelector("#tacticSelect");
const planSelect = document.querySelector("#planSelect");
const resetSquadButton = document.querySelector("#resetSquadButton");
const formationPitch = document.querySelector("#formationPitch");
const slotSelect = document.querySelector("#slotSelect");
const slotHint = document.querySelector("#slotHint");
const benchList = document.querySelector("#benchList");
const squadTitle = document.querySelector("#squadTitle");
const squadMeta = document.querySelector("#squadMeta");

let currentPlayers = [];
let selectedPlayerId = null;
let availablePositions = [];
let availableClubs = [];
let leagueClubMap = {};
let selectedSlotId = "";
const squadState = {
  base: { starters: {}, bench: [] },
  plan_b: { starters: {}, bench: [] },
  plan_c: { starters: {}, bench: [] },
  plan_d: { starters: {}, bench: [] },
};

const POSITION_ORDER = ["ST", "LW", "RW", "LM", "RM", "CAM", "CM", "CDM", "CB", "LB", "RB", "GK"];
const FORMATIONS = {
  "4-5-1": [
    ["ST", 50, 12], ["LM", 18, 32], ["LCM", 35, 38], ["CM", 50, 40], ["RCM", 65, 38], ["RM", 82, 32],
    ["LB", 18, 66], ["LCB", 38, 72], ["RCB", 62, 72], ["RB", 82, 66], ["GK", 50, 90],
  ],
  "4-3-3": [
    ["LW", 22, 14], ["ST", 50, 10], ["RW", 78, 14], ["LCM", 32, 42], ["CM", 50, 47], ["RCM", 68, 42],
    ["LB", 18, 70], ["LCB", 38, 76], ["RCB", 62, 76], ["RB", 82, 70], ["GK", 50, 91],
  ],
  "4-4-2": [
    ["LS", 40, 13], ["RS", 60, 13], ["LM", 20, 39], ["LCM", 40, 45], ["RCM", 60, 45], ["RM", 80, 39],
    ["LB", 18, 70], ["LCB", 38, 76], ["RCB", 62, 76], ["RB", 82, 70], ["GK", 50, 91],
  ],
  "4-2-1-3": [
    ["LW", 22, 13], ["ST", 50, 10], ["RW", 78, 13], ["CAM", 50, 34], ["LCDM", 39, 54], ["RCDM", 61, 54],
    ["LB", 18, 72], ["LCB", 38, 78], ["RCB", 62, 78], ["RB", 82, 72], ["GK", 50, 92],
  ],
  "4123": [
    ["LW", 22, 13], ["ST", 50, 10], ["RW", 78, 13], ["LCM", 36, 39], ["RCM", 64, 39], ["CDM", 50, 58],
    ["LB", 18, 72], ["LCB", 38, 78], ["RCB", 62, 78], ["RB", 82, 72], ["GK", 50, 92],
  ],
  "4222": [
    ["LS", 39, 12], ["RS", 61, 12], ["LAM", 35, 35], ["RAM", 65, 35], ["LCDM", 39, 56], ["RCDM", 61, 56],
    ["LB", 18, 72], ["LCB", 38, 78], ["RCB", 62, 78], ["RB", 82, 72], ["GK", 50, 92],
  ],
  "343": [
    ["LW", 22, 12], ["ST", 50, 9], ["RW", 78, 12], ["LM", 18, 42], ["LCM", 39, 47], ["RCM", 61, 47], ["RM", 82, 42],
    ["LCB", 32, 76], ["CB", 50, 80], ["RCB", 68, 76], ["GK", 50, 93],
  ],
  "351": [
    ["ST", 50, 10], ["LM", 18, 34], ["LCM", 35, 42], ["CM", 50, 46], ["RCM", 65, 42], ["RM", 82, 34],
    ["LWB", 20, 63], ["RWB", 80, 63], ["LCB", 35, 78], ["RCB", 65, 78], ["GK", 50, 93],
  ],
  "3223": [
    ["LW", 22, 12], ["ST", 50, 9], ["RW", 78, 12], ["LAM", 38, 35], ["RAM", 62, 35], ["LCM", 39, 56], ["RCM", 61, 56],
    ["LCB", 32, 78], ["CB", 50, 82], ["RCB", 68, 78], ["GK", 50, 94],
  ],
  "3412": [
    ["LS", 39, 11], ["RS", 61, 11], ["CAM", 50, 33], ["LM", 18, 46], ["LCM", 40, 52], ["RCM", 60, 52], ["RM", 82, 46],
    ["LCB", 32, 78], ["CB", 50, 82], ["RCB", 68, 78], ["GK", 50, 94],
  ],
  "3142": [
    ["LS", 39, 11], ["RS", 61, 11], ["LM", 18, 41], ["LCM", 39, 47], ["RCM", 61, 47], ["RM", 82, 41], ["CDM", 50, 63],
    ["LCB", 32, 79], ["CB", 50, 83], ["RCB", 68, 79], ["GK", 50, 94],
  ],
};

function escapeHTML(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function optionList(values, label) {
  return [`<option value="">${escapeHTML(label)}</option>`, ...values.map((value) => `<option value="${escapeHTML(value)}">${escapeHTML(value)}</option>`)].join("");
}

function orderedPositions(values) {
  const unique = [...new Set(values.map((value) => String(value).trim().toUpperCase()).filter(Boolean))];
  return unique.sort((a, b) => {
    const aIndex = POSITION_ORDER.indexOf(a);
    const bIndex = POSITION_ORDER.indexOf(b);
    if (aIndex !== -1 && bIndex !== -1) return aIndex - bIndex;
    if (aIndex !== -1) return -1;
    if (bIndex !== -1) return 1;
    return a.localeCompare(b);
  });
}

function renderPositionCategories(positions) {
  const selected = positionSelect.value;
  const buttons = [
    `<button type="button" class="${selected ? "" : "active"}" data-position="">전체</button>`,
    ...positions.map((position) => {
      const active = selected === position ? "active" : "";
      return `<button type="button" class="${active}" data-position="${escapeHTML(position)}">${escapeHTML(position)}</button>`;
    }),
  ];

  positionCategoryButtons.innerHTML = buttons.join("");
  positionSummary.textContent = selected ? `${selected} 가능 선수` : "전체 포지션";

  positionCategoryButtons.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      positionSelect.value = button.dataset.position;
      renderPositionCategories(availablePositions);
      loadPlayers();
    });
  });
}

function currentPlan() {
  return squadState[planSelect.value] || squadState.base;
}

function currentFormationSlots() {
  return FORMATIONS[formationSelect.value] || FORMATIONS["4-3-3"];
}

function slotBasePosition(slot) {
  const normalized = String(slot || "").replace(/^L|^R/, "").replace(/^LC|^RC/, "C");
  if (["LS", "RS"].includes(slot)) return "ST";
  if (["LAM", "RAM"].includes(slot)) return "CAM";
  if (["LCDM", "RCDM"].includes(slot)) return "CDM";
  if (["LCM", "RCM"].includes(slot)) return "CM";
  if (["LCB", "RCB"].includes(slot)) return "CB";
  if (slot === "LWB") return "LB";
  if (slot === "RWB") return "RB";
  return normalized;
}

function playerPositions(player) {
  return String(player.player_positions || "")
    .split(",")
    .map((position) => position.trim().toUpperCase())
    .filter(Boolean);
}

function canPlaySlot(player, slot) {
  return playerPositions(player).includes(slotBasePosition(slot));
}

function playerSummary(player) {
  return `${player.short_name} · ${player.player_positions} · OVR ${player.overall}`;
}

function renderFormationOptions() {
  formationSelect.innerHTML = Object.keys(FORMATIONS)
    .map((formation) => `<option value="${escapeHTML(formation)}">${escapeHTML(formation)}</option>`)
    .join("");
  formationSelect.value = "4-3-3";
}

function renderTeamControls() {
  const leagues = Object.keys(leagueClubMap).sort();
  const selectedLeague = teamLeagueSelect.value;
  const clubs = selectedLeague ? leagueClubMap[selectedLeague] || [] : availableClubs;
  teamLeagueSelect.innerHTML = optionList(leagues, "전체 리그");
  teamLeagueSelect.value = selectedLeague;
  teamClubSelect.innerHTML = optionList(clubs, "클럽 선택");
}

function renderSlotOptions() {
  const slots = currentFormationSlots().map(([slot]) => slot);
  if (!slots.includes(selectedSlotId)) selectedSlotId = slots[0] || "";
  slotSelect.innerHTML = slots
    .map((slot) => `<option value="${escapeHTML(slot)}">${escapeHTML(slot)}</option>`)
    .join("");
  slotSelect.value = selectedSlotId;
}

function renderSquadMeta() {
  const plan = currentPlan();
  const activeSlots = currentFormationSlots().map(([slot]) => slot);
  const starters = activeSlots.filter((slot) => plan.starters[slot]).length;
  const bench = plan.bench.length;
  const club = teamClubSelect.value || "팀 미선택";
  squadTitle.textContent = `${club} 스쿼드`;
  squadMeta.textContent = `${formationSelect.value} · ${tacticSelect.value} · 주전 ${starters}/11 · 예비 ${bench}명`;
  slotHint.textContent = selectedSlotId ? `${selectedSlotId} 슬롯 선택 중` : "포지션 카드를 선택해주세요.";
}

function renderBench() {
  const plan = currentPlan();
  if (!plan.bench.length) {
    benchList.innerHTML = `<div class="empty-bench">예비 선수가 없습니다.</div>`;
    return;
  }
  benchList.innerHTML = plan.bench
    .map((player, index) => `
      <div class="bench-player">
        ${playerImage(player.player_image_path || player.player_face_url, player.short_name)}
        <div>
          <strong>${escapeHTML(player.short_name)}</strong>
          <span>${escapeHTML(player.player_positions)} · OVR ${escapeHTML(player.overall)}</span>
        </div>
        <button type="button" data-bench-index="${index}">삭제</button>
      </div>
    `)
    .join("");
  activateImageFallbacks(benchList);
  benchList.querySelectorAll("button[data-bench-index]").forEach((button) => {
    button.addEventListener("click", () => {
      plan.bench.splice(Number(button.dataset.benchIndex), 1);
      renderTeamBoard();
    });
  });
}

function renderFormationBoard() {
  const plan = currentPlan();
  formationPitch.innerHTML = currentFormationSlots()
    .map(([slot, left, top]) => {
      const player = plan.starters[slot];
      const active = selectedSlotId === slot ? "active" : "";
      return `
        <button type="button" class="pitch-slot ${active}" style="left:${left}%; top:${top}%;" data-slot="${escapeHTML(slot)}">
          <span class="slot-position">${escapeHTML(slot)}</span>
          ${player ? playerImage(player.player_image_path || player.player_face_url, player.short_name, "slot-image") : `<span class="slot-plus">+</span>`}
          <strong>${player ? escapeHTML(player.short_name) : "선수 선택"}</strong>
          <small>${player ? `OVR ${escapeHTML(player.overall)} · ${escapeHTML(player.player_positions)}` : slotBasePosition(slot)}</small>
        </button>
      `;
    })
    .join("");
  activateImageFallbacks(formationPitch);
  formationPitch.querySelectorAll(".pitch-slot").forEach((button) => {
    button.addEventListener("click", () => {
      selectedSlotId = button.dataset.slot;
      positionSelect.value = slotBasePosition(selectedSlotId);
      renderPositionCategories(availablePositions);
      renderTeamBoard();
      loadPlayers();
    });
  });
}

function renderTeamBoard() {
  renderSlotOptions();
  renderFormationBoard();
  renderBench();
  renderSquadMeta();
}

function addStarter(playerId) {
  const player = currentPlayers.find((item) => String(item.player_id) === String(playerId));
  if (!player || !selectedSlotId) return;
  const plan = currentPlan();
  plan.starters[selectedSlotId] = player;
  renderTeamBoard();
}

function addBench(playerId) {
  const player = currentPlayers.find((item) => String(item.player_id) === String(playerId));
  if (!player) return;
  const plan = currentPlan();
  if (!plan.bench.some((item) => String(item.player_id) === String(player.player_id))) {
    plan.bench.push(player);
  }
  renderTeamBoard();
}

function money(value) {
  const number = Number(value || 0);
  if (number >= 1000000) return `€${(number / 1000000).toFixed(1)}M`;
  if (number >= 1000) return `€${Math.round(number / 1000)}K`;
  return `€${number}`;
}

function initials(name) {
  return (name || "?")
    .split(/[\s.]+/)
    .filter(Boolean)
    .map((part) => part[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

function playerImage(url, name, sizeClass = "avatar") {
  if (!url) {
    return `<div class="${escapeHTML(sizeClass)} fallback">${escapeHTML(initials(name))}</div>`;
  }
  return `<img class="${escapeHTML(sizeClass)}" src="${escapeHTML(url)}" alt="${escapeHTML(name)}" loading="lazy" data-fallback="${escapeHTML(initials(name))}" />`;
}

function activateImageFallbacks(root = document) {
  root.querySelectorAll("img[data-fallback]").forEach((image) => {
    image.addEventListener("error", () => {
      const fallback = document.createElement("div");
      fallback.className = `${image.className} fallback`;
      fallback.textContent = image.dataset.fallback || "?";
      image.replaceWith(fallback);
    }, { once: true });
  });
}

function queryParams() {
  const params = new URLSearchParams();
  const values = {
    search: searchInput.value.trim(),
    position: positionSelect.value,
    preset: presetSelect.value,
    region: regionSelect.value,
    nationality: nationalitySelect.value,
    league: leagueSelect.value,
    max_age: maxAgeInput.value,
    max_value: maxValueInput.value,
    limit: 80,
  };
  for (const [key, value] of Object.entries(values)) {
    if (value !== "") params.set(key, value);
  }
  return params;
}

async function loadMeta() {
  const response = await fetch("/api/fc26/meta");
  const meta = await response.json();
  dataStatus.textContent = meta.data_loaded ? `${meta.count.toLocaleString()}명 로딩됨` : "CSV 없음";
  availablePositions = orderedPositions(meta.filters.positions);
  availableClubs = meta.filters.clubs || [];
  leagueClubMap = meta.filters.league_clubs || {};
  positionSelect.innerHTML = optionList(availablePositions, "전체");
  renderPositionCategories(availablePositions);
  regionSelect.innerHTML = optionList(meta.filters.regions, "전체");
  nationalitySelect.innerHTML = optionList(meta.filters.nationalities, "전체");
  leagueSelect.innerHTML = optionList(meta.filters.leagues, "전체");
  renderFormationOptions();
  renderTeamControls();
  renderTeamBoard();
}

async function loadPlayers() {
  const response = await fetch(`/api/fc26/players?${queryParams().toString()}`);
  const data = await response.json();
  currentPlayers = data.players;
  renderPlayers(currentPlayers);
  if (currentPlayers.length) await loadReport(currentPlayers[0].player_id);
}

function renderPlayers(players) {
  if (!players.length) {
    playerRows.innerHTML = `<tr><td colspan="10">조건에 맞는 선수가 없습니다.</td></tr>`;
    return;
  }
  playerRows.innerHTML = players
    .map((player, index) => {
      const starterDisabled = selectedSlotId && canPlaySlot(player, selectedSlotId) ? "" : "disabled";
      return `
        <tr data-player-id="${player.player_id}">
          <td>${index + 1}</td>
          <td>
            <div class="player-cell">
              ${playerImage(player.player_image_path || player.player_face_url, player.short_name)}
              <div><strong>${escapeHTML(player.short_name)}</strong><br><span>${money(player.value_eur)}</span></div>
            </div>
          </td>
          <td>${escapeHTML(player.player_positions)}</td>
          <td>${escapeHTML(player.club_name || "-")}</td>
          <td>${escapeHTML(player.nationality_name)}</td>
          <td>${escapeHTML(player.age)}</td>
          <td>${escapeHTML(player.overall)}</td>
          <td>${escapeHTML(player.potential)}</td>
          <td>${Number(player.scouting_score).toFixed(1)}</td>
          <td>
            <div class="squad-actions">
              <button type="button" data-action="starter" data-player-id="${player.player_id}" ${starterDisabled}>주전</button>
              <button type="button" data-action="bench" data-player-id="${player.player_id}">예비</button>
            </div>
          </td>
        </tr>
      `;
    })
    .join("");
  activateImageFallbacks(playerRows);

  playerRows.querySelectorAll("tr").forEach((row) => {
    row.addEventListener("click", () => loadReport(row.dataset.playerId));
  });
  playerRows.querySelectorAll("button[data-action]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      if (button.dataset.action === "starter") addStarter(button.dataset.playerId);
      if (button.dataset.action === "bench") addBench(button.dataset.playerId);
    });
  });
}

async function loadReport(playerId) {
  selectedPlayerId = playerId;
  const params = queryParams();
  const response = await fetch(`/api/fc26/report/${playerId}?${params.toString()}`);
  const data = await response.json();
  renderReport(data.player, data.report, data.report_source);
}

function renderReport(player, report, source) {
  reportSource.textContent = source === "openai" ? "OpenAI" : "Local fallback";
  playerCard.innerHTML = `
    ${playerImage(player.player_image_path || player.player_face_url, player.short_name, "profile-image")}
    <div>
      <h3>${escapeHTML(player.short_name)}</h3>
      <p>${escapeHTML(player.long_name)}</p>
      <p>${escapeHTML(player.club_name || "-")} · ${escapeHTML(player.league_name || "-")} · ${escapeHTML(player.nationality_name)}</p>
    </div>
  `;
  activateImageFallbacks(playerCard);

  const bars = [
    ["능력", player.ability_score],
    ["잠재력", player.potential_score],
     ["포지션 Fit", player.fit_score],
  ];

  //["가성비", player.value_score],["지역 Fit", player.geo_score], '

  scoreBars.innerHTML = bars
    .map(([label, score]) => {
      const pct = Math.max(4, Number(score || 0) * 100);
      return `
        <div class="bar-row">
          <strong>${label}</strong>
          <div class="track"><div class="fill" style="width:${pct}%"></div></div>
          <span>${pct.toFixed(0)}</span>
        </div>
      `;
    })
    .join("");
  chatLog.innerHTML = "";
  appendMessage("agent", report);
}

function appendMessage(role, text) {
  const message = document.createElement("div");
  message.className = `chat-message ${role}`;
  message.textContent = text;
  chatLog.appendChild(message);
  chatLog.scrollTop = chatLog.scrollHeight;
}

async function askQuestion(question) {
  if (!selectedPlayerId || !question.trim()) return;
  appendMessage("user", question);
  chatInput.value = "";
  reportSource.textContent = "답변 생성 중";

  const params = queryParams();
  const response = await fetch(`/api/fc26/chat/${selectedPlayerId}?${params.toString()}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  const data = await response.json();
  reportSource.textContent = data.source === "openai" ? "OpenAI" : "Local fallback";
  appendMessage("agent", data.answer || "답변을 생성하지 못했습니다.");
}

refreshButton.addEventListener("click", loadPlayers);
[searchInput, maxAgeInput, maxValueInput].forEach((input) => input.addEventListener("keydown", (event) => {
  if (event.key === "Enter") loadPlayers();
}));
[positionSelect, presetSelect, regionSelect, nationalitySelect, leagueSelect].forEach((select) => {
  select.addEventListener("change", () => {
    if (select === positionSelect) renderPositionCategories(availablePositions);
    loadPlayers();
  });
});
teamLeagueSelect.addEventListener("change", () => {
  const selectedLeague = teamLeagueSelect.value;
  const clubs = selectedLeague ? leagueClubMap[selectedLeague] || [] : availableClubs;
  teamClubSelect.innerHTML = optionList(clubs, "클럽 선택");
  renderTeamBoard();
});
teamClubSelect.addEventListener("change", renderTeamBoard);
formationSelect.addEventListener("change", () => {
  currentPlan().starters = {};
  selectedSlotId = "";
  renderTeamBoard();
  renderPlayers(currentPlayers);
});
tacticSelect.addEventListener("change", renderTeamBoard);
planSelect.addEventListener("change", () => {
  selectedSlotId = "";
  renderTeamBoard();
  renderPlayers(currentPlayers);
});
slotSelect.addEventListener("change", () => {
  selectedSlotId = slotSelect.value;
  positionSelect.value = slotBasePosition(selectedSlotId);
  renderPositionCategories(availablePositions);
  renderTeamBoard();
  loadPlayers();
});
resetSquadButton.addEventListener("click", () => {
  const plan = currentPlan();
  plan.starters = {};
  plan.bench = [];
  renderTeamBoard();
  renderPlayers(currentPlayers);
});
document.querySelectorAll(".quick-questions button").forEach((button) => {
  button.addEventListener("click", () => askQuestion(button.dataset.question));
});
chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  askQuestion(chatInput.value.trim());
});

loadMeta().then(loadPlayers);
