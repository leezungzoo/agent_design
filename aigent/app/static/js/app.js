const dataStatus = document.querySelector("#dataStatus");
const searchInput = document.querySelector("#searchInput");
const positionSelect = document.querySelector("#positionSelect");
const presetSelect = document.querySelector("#presetSelect");
const regionSelect = document.querySelector("#regionSelect");
const nationalitySelect = document.querySelector("#nationalitySelect");
const leagueSelect = document.querySelector("#leagueSelect");
const clubSelect = document.querySelector("#clubSelect");
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
const teamRegionSelect = document.querySelector("#teamRegionSelect");
const teamNationalitySelect = document.querySelector("#teamNationalitySelect");
const teamCandidateLeagueSelect = document.querySelector("#teamCandidateLeagueSelect");
const saveSquadButton = document.querySelector("#saveSquadButton");
const resetSquadButton = document.querySelector("#resetSquadButton");
const formationPitch = document.querySelector("#formationPitch");
const slotSelect = document.querySelector("#slotSelect");
const slotHint = document.querySelector("#slotHint");
const benchList = document.querySelector("#benchList");
const slotCandidateTitle = document.querySelector("#slotCandidateTitle");
const slotCandidateSearch = document.querySelector("#slotCandidateSearch");
const slotCandidateList = document.querySelector("#slotCandidateList");
const squadTitle = document.querySelector("#squadTitle");
const squadMeta = document.querySelector("#squadMeta");
const squadScoreSummary = document.querySelector("#squadScoreSummary");
const savedSquadList = document.querySelector("#savedSquadList");
const teamAnalysisBox = document.querySelector("#teamAnalysisBox");
const teamRecommendationList = document.querySelector("#teamRecommendationList");

let currentPlayers = [];
let selectedPlayerId = null;
let availablePositions = [];
let availableClubs = [];
let leagueClubMap = {};
let selectedSlotId = "";
let dragState = null;
let slotCandidateRequestId = 0;
let slotCandidatePlayers = [];
const squadState = {
  base: { starters: {}, bench: [], positions: {}, labels: {} },
  plan_b: { starters: {}, bench: [], positions: {}, labels: {} },
  plan_c: { starters: {}, bench: [], positions: {}, labels: {} },
  plan_d: { starters: {}, bench: [], positions: {}, labels: {} },
};

const SQUAD_STORAGE_KEY = "fc26-scouting-squad-v2";
const POSITION_ORDER = ["ST", "LW", "RW", "LM", "RM", "CAM", "CM", "CDM", "CB", "LB", "RB", "GK"];
const LEAGUE_KOREAN_LABELS = {
  "1. Division": "덴마크 1부",
  "2. Bundesliga": "독일 2. 분데스리가",
  "3. Liga": "독일 3. 리가",
  "A-League Men": "호주 A리그",
  "Allsvenskan": "스웨덴 알스벤스칸",
  "Bundesliga": "독일 분데스리가",
  "Categoría Primera A": "콜롬비아 카테고리아 프리메라 A",
  "Championship": "잉글랜드 챔피언십",
  "División Profesional": "파라과이 디비시온 프로페시오날",
  "División de Fútbol Profesional": "볼리비아 프로축구 디비전",
  "Ekstraklasa": "폴란드 엑스트라클라사",
  "Eliteserien": "노르웨이 엘리테세리엔",
  "Eredivisie": "네덜란드 에레디비시",
  "Hrvatska nogometna liga": "크로아티아 1부 리그",
  "K League 1": "K리그1",
  "La Liga": "스페인 프리메라리가(라리가)",
  "La Liga 2": "스페인 세군다 디비시온(라리가2)",
  "League One": "잉글랜드 리그 원",
  "League Two": "잉글랜드 리그 투",
  "Liga 1": "루마니아 리가 1",
  "Liga I": "루마니아 리가 I",
  "Liga Profesional de Fútbol": "아르헨티나 리가 프로페시오날",
  "Ligue 1": "프랑스 리그 1",
  "Ligue 2": "프랑스 리그 2",
  "Major League Soccer": "미국 MLS",
  "Nemzeti Bajnokság I": "헝가리 NB I",
  "Premier Division": "아일랜드 프리미어 디비전",
  "Premier League": "잉글랜드 프리미어리그",
  "Premiership": "스코틀랜드 프리미어십",
  "Premyer Liqa": "아제르바이잔 프리미어리그",
  "Primeira Liga": "포르투갈 프리메이라리가",
  "Primera Division": "칠레 프리메라 디비시온",
  "Primera División": "우루과이 프리메라 디비시온",
  "Pro League": "벨기에 프로 리그",
  "První liga": "체코 1부 리그",
  "Serie A": "이탈리아 세리에 A",
  "Serie B": "이탈리아 세리에 B",
  "Super League": "스위스 슈퍼리그",
  "Superliga": "덴마크 수페르리가",
  "Série A": "브라질 세리에 A",
  "Süper Lig": "튀르키예 쉬페르리그",
  "Veikkausliiga": "핀란드 베이카우스리가",
};
const KOREAN_PLAYER_ALIASES = {
  메시: ["messi", "lionel messi"],
  리오넬메시: ["messi", "lionel messi"],
  호날두: ["ronaldo", "cristiano ronaldo"],
  크리스티아누호날두: ["ronaldo", "cristiano ronaldo"],
  음바페: ["mbappe", "mbappé", "kylian mbappe"],
  홀란: ["haaland", "erling haaland"],
  홀란드: ["haaland", "erling haaland"],
  손흥민: ["son", "heung min son", "heung-min son"],
  손: ["son", "heung min son"],
  살라: ["salah", "mohamed salah"],
  더브라위너: ["de bruyne", "kevin de bruyne"],
  덕배: ["de bruyne", "kevin de bruyne"],
  벨링엄: ["bellingham", "jude bellingham"],
  비니시우스: ["vinicius", "vinícius", "vini"],
  비니시우스주니오르: ["vinicius", "vinícius", "vini"],
  야말: ["yamal", "lamine yamal"],
  무시알라: ["musiala", "jamal musiala"],
  페드리: ["pedri"],
  가비: ["gavi"],
  케인: ["kane", "harry kane"],
  레반도프스키: ["lewandowski", "robert lewandowski"],
  네이마르: ["neymar"],
  모드리치: ["modric", "modrić", "luka modric"],
  김민재: ["kim min jae", "kim min-jae", "min jae kim"],
  이강인: ["lee kang in", "kang in lee", "kang-in lee"],
};
const SLOT_BASE_POSITIONS = {
  LS: "ST",
  RS: "ST",
  LAM: "CAM",
  RAM: "CAM",
  LCM: "CM",
  RCM: "CM",
  LCDM: "CDM",
  RCDM: "CDM",
  LCB: "CB",
  RCB: "CB",
  LWB: "LB",
  RWB: "RB",
};
const FORMATION_GROUPS = {
  "4백 포메이션": ["4-5-1", "4-3-3", "4-4-2", "4-2-1-3", "4-1-2-3", "4-2-2-2"],
  "3백 포메이션": ["3-4-3", "3-5-1", "3-2-2-3", "3-4-1-2"],
};
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
  "4-1-2-3": [
    ["LW", 22, 13], ["ST", 50, 10], ["RW", 78, 13], ["LCM", 36, 39], ["RCM", 64, 39], ["CDM", 50, 58],
    ["LB", 18, 72], ["LCB", 38, 78], ["RCB", 62, 78], ["RB", 82, 72], ["GK", 50, 92],
  ],
  "4-2-2-2": [
    ["LS", 39, 12], ["RS", 61, 12], ["LAM", 35, 35], ["RAM", 65, 35], ["LCDM", 39, 56], ["RCDM", 61, 56],
    ["LB", 18, 72], ["LCB", 38, 78], ["RCB", 62, 78], ["RB", 82, 72], ["GK", 50, 92],
  ],
  "3-4-3": [
    ["LW", 22, 12], ["ST", 50, 9], ["RW", 78, 12], ["LM", 18, 42], ["LCM", 39, 47], ["RCM", 61, 47], ["RM", 82, 42],
    ["LCB", 32, 76], ["CB", 50, 80], ["RCB", 68, 76], ["GK", 50, 93],
  ],
  "3-5-1": [
    ["ST", 50, 10], ["LM", 18, 34], ["LCM", 35, 42], ["CM", 50, 46], ["RCM", 65, 42], ["RM", 82, 34],
    ["LWB", 20, 63], ["RWB", 80, 63], ["LCB", 35, 78], ["RCB", 65, 78], ["GK", 50, 93],
  ],
  "3-2-2-3": [
    ["LW", 22, 12], ["ST", 50, 9], ["RW", 78, 12], ["LAM", 38, 35], ["RAM", 62, 35], ["LCM", 39, 56], ["RCM", 61, 56],
    ["LCB", 32, 78], ["CB", 50, 82], ["RCB", 68, 78], ["GK", 50, 94],
  ],
  "3-4-1-2": [
    ["LS", 39, 11], ["RS", 61, 11], ["CAM", 50, 33], ["LM", 18, 46], ["LCM", 40, 52], ["RCM", 60, 52], ["RM", 82, 46],
    ["LCB", 32, 78], ["CB", 50, 82], ["RCB", 68, 78], ["GK", 50, 94],
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

function normalizeSearchText(value) {
  return String(value || "")
    .normalize("NFKC")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .normalize("NFC")
    .replace(/[\s.'’\-]/g, "")
    .toLowerCase();
}

function searchTerms(value) {
  const raw = String(value || "").trim();
  if (!raw) return [];
  const normalized = normalizeSearchText(raw);
  const aliases = KOREAN_PLAYER_ALIASES[normalized] || [];
  return [raw, normalized, ...aliases].map(normalizeSearchText).filter(Boolean);
}

function primarySearchTerm(value) {
  const terms = searchTerms(value);
  return terms.length > 2 ? terms[2] : String(value || "").trim();
}

function playerMatchesSearch(player, value) {
  const terms = searchTerms(value);
  if (!terms.length) return true;
  const haystack = normalizeSearchText(`${player.short_name || ""} ${player.long_name || ""}`);
  return terms.some((term) => haystack.includes(term));
}

function leagueLabel(value) {
  return LEAGUE_KOREAN_LABELS[value] || value;
}

function optionList(values, label, displayLabel = (value) => value) {
  return [
    `<option value="">${escapeHTML(label)}</option>`,
    ...values.map((value) => `<option value="${escapeHTML(value)}">${escapeHTML(displayLabel(value))}</option>`),
  ].join("");
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
  const plan = squadState.base;
  plan.positions ||= {};
  plan.labels ||= {};
  return plan;
}

function currentFormationSlots() {
  return FORMATIONS[formationSelect.value] || FORMATIONS["4-3-3"];
}

function slotBasePosition(slot) {
  const normalized = String(slot || "").trim().toUpperCase();
  return SLOT_BASE_POSITIONS[normalized] || normalized;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function defaultSlotPosition(slot, left, top) {
  return {
    left: top,
    top: 100 - left,
  };
}

function slotDisplayLabel(slot) {
  return currentPlan().labels?.[slot] || slot;
}

function visualPositionRole(left, top) {
  const side = top < 38 ? "R" : top > 62 ? "L" : "";
  if (left <= 18) {
    if (top < 35) return "RW";
    if (top > 65) return "LW";
    return "ST";
  }
  if (left <= 34) {
    if (top < 38) return "RAM";
    if (top > 62) return "LAM";
    return "CAM";
  }
  if (left <= 58) {
    if (top < 34) return "RM";
    if (top > 66) return "LM";
    return side ? `${side}CM` : "CM";
  }
  if (left <= 72) {
    if (top < 35) return "RWB";
    if (top > 65) return "LWB";
    return side ? `${side}CDM` : "CDM";
  }
  if (left <= 88) {
    if (top < 34) return "RB";
    if (top > 66) return "LB";
    return side ? `${side}CB` : "CB";
  }
  return "GK";
}

function updateSlotLabel(slot, label) {
  const plan = currentPlan();
  const nextLabel = String(label || "").trim().toUpperCase();
  if (nextLabel) {
    plan.labels[slot] = nextLabel;
  } else {
    delete plan.labels[slot];
  }
}

function getSlotPosition(slot, left, top) {
  const plan = currentPlan();
  return plan.positions[slot] || defaultSlotPosition(slot, left, top);
}

function playerPositions(player) {
  return String(player.player_positions || "")
    .split(",")
    .map((position) => position.trim().toUpperCase())
    .filter(Boolean);
}

function canPlaySlot(player, slot) {
  return true;
}

function assignedPlayerIds() {
  const plan = currentPlan();
  const ids = new Set(plan.bench.map((player) => String(player.player_id)));
  Object.values(plan.starters).forEach((player) => {
    if (player?.player_id !== undefined) ids.add(String(player.player_id));
  });
  return ids;
}

function isPlayerAssigned(playerId) {
  return assignedPlayerIds().has(String(playerId));
}

function isPlayerInSelectedSlot(playerId) {
  const player = currentPlan().starters[selectedSlotId];
  return player && String(player.player_id) === String(playerId);
}

function resetCurrentSquad(keepBench = false) {
  const plan = currentPlan();
  plan.starters = {};
  if (!keepBench) plan.bench = [];
  plan.positions = {};
  plan.labels = {};
  selectedSlotId = "";
}

function sortByTeamPriority(players) {
  return [...players].sort((a, b) => {
    const overallDiff = Number(b.overall || 0) - Number(a.overall || 0);
    if (overallDiff) return overallDiff;
    const scoreDiff = Number(b.scouting_score || 0) - Number(a.scouting_score || 0);
    if (scoreDiff) return scoreDiff;
    return Number(b.potential || 0) - Number(a.potential || 0);
  });
}

function bestPlayerForSlot(players, usedIds, slot) {
  const label = slotDisplayLabel(slot);
  const basePosition = slotBasePosition(label);
  const positionMatched = players.find((player) => {
    return !usedIds.has(String(player.player_id)) && playerPositions(player).includes(basePosition);
  });
  if (positionMatched) return positionMatched;
  return players.find((player) => !usedIds.has(String(player.player_id)));
}

function playerSummary(player) {
  return `${player.short_name} · ${player.player_positions} · OVR ${player.overall}`;
}

function renderFormationOptions() {
  formationSelect.innerHTML = Object.entries(FORMATION_GROUPS)
    .map(([group, formations]) => `
      <optgroup label="${escapeHTML(group)}">
        ${formations
          .filter((formation) => FORMATIONS[formation])
          .map((formation) => `<option value="${escapeHTML(formation)}">${escapeHTML(formation)}</option>`)
          .join("")}
      </optgroup>
    `)
    .join("");
  formationSelect.value = "4-3-3";
}

function renderTeamControls() {
  const leagues = Object.keys(leagueClubMap).sort();
  const selectedLeague = teamLeagueSelect.value;
  const clubs = selectedLeague ? leagueClubMap[selectedLeague] || [] : availableClubs;
  teamLeagueSelect.innerHTML = optionList(leagues, "전체 리그", leagueLabel);
  teamLeagueSelect.value = selectedLeague;
  teamClubSelect.innerHTML = optionList(clubs, "클럽 선택");
}

function renderClubFilter() {
  const selectedClub = clubSelect.value;
  const selectedLeague = leagueSelect.value;
  const clubs = selectedLeague ? leagueClubMap[selectedLeague] || [] : availableClubs;
  clubSelect.innerHTML = optionList(clubs, "전체");
  if (selectedClub && clubs.includes(selectedClub)) {
    clubSelect.value = selectedClub;
  }
}

function renderSlotOptions() {
  const slots = currentFormationSlots().map(([slot]) => slot);
  if (!slots.includes(selectedSlotId)) selectedSlotId = slots[0] || "";
  slotSelect.innerHTML = slots
    .map((slot) => {
      const label = slotDisplayLabel(slot);
      const text = label === slot ? slot : `${slot} -> ${label}`;
      return `<option value="${escapeHTML(slot)}">${escapeHTML(text)}</option>`;
    })
    .join("");
  slotSelect.value = selectedSlotId;
}

function selectSlot(slot, shouldLoadPlayers = true) {
  selectedSlotId = slot || "";
  if (selectedSlotId) {
    positionSelect.value = "";
    renderPositionCategories(availablePositions);
  }
  renderTeamBoard();
  renderPlayers(currentPlayers);
  if (shouldLoadPlayers) loadPlayers();
}

function nextEmptySlot(fromSlot) {
  const plan = currentPlan();
  const slots = currentFormationSlots().map(([slot]) => slot);
  if (!slots.length) return "";

  const startIndex = Math.max(0, slots.indexOf(fromSlot));
  const orderedSlots = [...slots.slice(startIndex + 1), ...slots.slice(0, startIndex + 1)];
  return orderedSlots.find((slot) => !plan.starters[slot]) || "";
}

function renderSquadMeta() {
  const plan = currentPlan();
  const activeSlots = currentFormationSlots().map(([slot]) => slot);
  const starters = activeSlots.filter((slot) => plan.starters[slot]).length;
  const bench = plan.bench.length;
  const selectedPlayers = activeSlots.map((slot) => plan.starters[slot]).filter(Boolean);
  const avgScore = selectedPlayers.length
    ? selectedPlayers.reduce((sum, player) => sum + Number(player.scouting_score || 0), 0) / selectedPlayers.length
    : 0;
  const avgOverall = selectedPlayers.length
    ? selectedPlayers.reduce((sum, player) => sum + Number(player.overall || 0), 0) / selectedPlayers.length
    : 0;
  const avgPotential = selectedPlayers.length
    ? selectedPlayers.reduce((sum, player) => sum + Number(player.potential || 0), 0) / selectedPlayers.length
    : 0;
  const club = teamClubSelect.value || "팀 미선택";
  squadTitle.textContent = `${club} 스쿼드`;
  squadMeta.textContent = `${formationSelect.value} · 주전 ${starters}/11 · 예비 ${bench}명`;
  squadScoreSummary.innerHTML = `
    <div><strong>${avgScore.toFixed(1)}</strong><span>종합</span></div>
    <div><strong>${avgOverall.toFixed(1)}</strong><span>OVR 평균</span></div>
    <div><strong>${avgPotential.toFixed(1)}</strong><span>POT 평균</span></div>
  `;
  if (savedSquadList) {
    savedSquadList.innerHTML = activeSlots
      .map((slot) => {
        const player = plan.starters[slot];
        const label = slotDisplayLabel(slot);
        return `
          <div class="saved-squad-item">
            <strong>${escapeHTML(label)}</strong>
            <span>${player ? `${escapeHTML(player.short_name)} · ${Number(player.scouting_score || 0).toFixed(1)}` : "미배치"}</span>
          </div>
        `;
      })
      .join("");
  }
  const label = selectedSlotId ? slotDisplayLabel(selectedSlotId) : "";
  slotHint.textContent = selectedSlotId ? `${selectedSlotId} 슬롯 선택 중 · 현재 역할 ${label}` : "포지션 카드를 선택해주세요.";
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

async function renderSlotCandidates() {
  if (!slotCandidateList || !slotCandidateTitle) return;
  if (!selectedSlotId) {
    slotCandidateTitle.textContent = "선수 선택";
    slotCandidateList.innerHTML = `<div class="empty-bench">포지션 슬롯을 먼저 선택하세요.</div>`;
    return;
  }

  const displayLabel = slotDisplayLabel(selectedSlotId);
  const basePosition = slotBasePosition(displayLabel);
  const candidateSearch = slotCandidateSearch?.value || "";
  const requestId = ++slotCandidateRequestId;
  const params = new URLSearchParams({
    preset: presetSelect.value,
    position: basePosition,
    limit: "80",
  });

  const filterValues = {
    search: primarySearchTerm(candidateSearch),
    region: teamRegionSelect.value,
    nationality: teamNationalitySelect.value,
    league: teamCandidateLeagueSelect.value,
  };
  for (const [key, value] of Object.entries(filterValues)) {
    if (value !== "") params.set(key, value);
  }

  slotCandidateTitle.textContent = `${displayLabel} 배치 후보`;
  slotCandidateList.innerHTML = `<div class="empty-bench">${displayLabel} 후보 불러오는 중</div>`;

  let candidates = [];
  try {
    const response = await fetch(`/api/fc26/players?${params.toString()}`);
    const data = await response.json();
    if (requestId !== slotCandidateRequestId) return;
    candidates = data.players || [];
    slotCandidatePlayers = candidates;
  } catch {
    if (requestId !== slotCandidateRequestId) return;
    slotCandidateList.innerHTML = `<div class="empty-bench">후보를 불러오지 못했습니다.</div>`;
    return;
  }

  if (!candidates.length) {
    const message = candidateSearch
      ? `${displayLabel} 후보 중 '${candidateSearch}' 검색 결과가 없습니다.`
      : `${displayLabel} 포지션에 맞는 후보가 없습니다.`;
    slotCandidateList.innerHTML = `<div class="empty-bench">${escapeHTML(message)}</div>`;
    return;
  }

  slotCandidateList.innerHTML = candidates
    .map((player) => {
      const assigned = isPlayerAssigned(player.player_id);
      const inCurrentSlot = isPlayerInSelectedSlot(player.player_id);
      const disabled = assigned ? "disabled" : "";
      const label = inCurrentSlot ? "선택됨" : assigned ? "배정됨" : "넣기";
      return `
        <button type="button" class="slot-candidate" data-player-id="${player.player_id}" ${disabled}>
          ${playerImage(player.player_image_path || player.player_face_url, player.short_name)}
          <span>
            <strong>${escapeHTML(player.short_name)}</strong>
            <small>${escapeHTML(player.player_positions)} · OVR ${escapeHTML(player.overall)} · ${Number(player.scouting_score).toFixed(1)}</small>
          </span>
          <em>${label}</em>
        </button>
      `;
    })
    .join("");

  activateImageFallbacks(slotCandidateList);
  slotCandidateList.querySelectorAll(".slot-candidate:not(:disabled)").forEach((button) => {
    button.addEventListener("click", () => addStarter(button.dataset.playerId));
  });
}

function handleSlotPointerDown(event) {
  const button = event.currentTarget;
  const slot = button.dataset.slot;
  if (!slot || event.button !== 0) return;
  const rect = formationPitch.getBoundingClientRect();
  dragState = {
    slot,
    pointerId: event.pointerId,
    startX: event.clientX,
    startY: event.clientY,
    moved: false,
    rect,
  };
  button.setPointerCapture(event.pointerId);
  button.classList.add("dragging");
}

function handleSlotPointerMove(event) {
  if (!dragState || event.pointerId !== dragState.pointerId) return;
  const delta = Math.hypot(event.clientX - dragState.startX, event.clientY - dragState.startY);
  if (delta > 4) dragState.moved = true;
  if (!dragState.moved) return;

  const rect = dragState.rect;
  const left = clamp(((event.clientX - rect.left) / rect.width) * 100, 6, 94);
  const top = clamp(((event.clientY - rect.top) / rect.height) * 100, 8, 92);
  const plan = currentPlan();
  plan.positions[dragState.slot] = { left, top };
  updateSlotLabel(dragState.slot, visualPositionRole(left, top));

  const button = formationPitch.querySelector(`.pitch-slot[data-slot="${CSS.escape(dragState.slot)}"]`);
  if (button) {
    button.style.left = `${left}%`;
    button.style.top = `${top}%`;
    const label = button.querySelector(".slot-position");
    if (label) label.textContent = slotDisplayLabel(dragState.slot);
  }
  renderSlotOptions();
  renderSquadMeta();
}

function handleSlotPointerUp(event) {
  if (!dragState || event.pointerId !== dragState.pointerId) return;
  const { slot, moved } = dragState;
  const button = event.currentTarget;
  button.classList.remove("dragging");
  dragState = null;
  if (!moved) {
    selectSlot(slot);
  } else {
    selectSlot(slot);
  }
}

function renderFormationBoard() {
  const plan = currentPlan();
  formationPitch.innerHTML = currentFormationSlots()
    .map(([slot, left, top]) => {
      const position = getSlotPosition(slot, left, top);
      const player = plan.starters[slot];
      const active = selectedSlotId === slot ? "active" : "";
      const label = slotDisplayLabel(slot);
      return `
        <button type="button" class="pitch-slot ${active}" style="left:${position.left}%; top:${position.top}%;" data-slot="${escapeHTML(slot)}">
          <span class="slot-position">${escapeHTML(label)}</span>
          ${player ? playerImage(player.player_image_path || player.player_face_url, player.short_name, "slot-image") : `<span class="slot-plus">+</span>`}
          <strong>${player ? escapeHTML(player.short_name) : "선수 선택"}</strong>
          <small>${player ? `OVR ${escapeHTML(player.overall)} · ${escapeHTML(player.player_positions)}` : slotBasePosition(label)}</small>
        </button>
      `;
    })
    .join("");
  activateImageFallbacks(formationPitch);
  formationPitch.querySelectorAll(".pitch-slot").forEach((button) => {
    button.addEventListener("pointerdown", handleSlotPointerDown);
    button.addEventListener("pointermove", handleSlotPointerMove);
    button.addEventListener("pointerup", handleSlotPointerUp);
    button.addEventListener("pointercancel", handleSlotPointerUp);
  });
}

function renderTeamBoard() {
  renderFormationBoard();
  renderSlotOptions();
  renderBench();
  renderSlotCandidates();
  renderSquadMeta();
  renderTeamAnalysis();
}

function buildSquadPayload() {
  return {
    squadState,
    selectedSlotId,
    controls: {
      teamLeague: teamLeagueSelect.value,
      teamClub: teamClubSelect.value,
      formation: formationSelect.value,
      plan: "base",
      teamRegion: teamRegionSelect.value,
      teamNationality: teamNationalitySelect.value,
      teamCandidateLeague: teamCandidateLeagueSelect.value,
    },
  };
}

async function saveSquadState() {
  const payload = buildSquadPayload();
  localStorage.setItem(SQUAD_STORAGE_KEY, JSON.stringify(payload));
  try {
    const response = await fetch("/api/fc26/squads", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    dataStatus.textContent = result.path ? `저장 완료: ${result.path}` : "스쿼드 저장 완료";
  } catch {
    dataStatus.textContent = "브라우저 저장 완료 · 서버 파일 저장 실패";
  }
}

async function renderTeamAnalysis() {
  const plan = currentPlan();
  const starters = Object.values(plan.starters || {}).filter(Boolean);
  if (!starters.length) {
    if (teamAnalysisBox) teamAnalysisBox.textContent = "선수를 배치하면 팀의 문제와 약점을 분석합니다.";
    if (teamRecommendationList) teamRecommendationList.textContent = "추천 후보를 계산하려면 스쿼드를 구성하세요.";
    return;
  }

  try {
    const response = await fetch("/api/fc26/team-analysis", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildSquadPayload()),
    });
    const data = await response.json();
    const analysis = data.analysis || {};
    if (teamAnalysisBox) {
      teamAnalysisBox.innerHTML = `
        <p>${escapeHTML(analysis.summary || "")}</p>
        <strong>문제/단점</strong>
        <ul>${(analysis.weaknesses || []).map((item) => `<li>${escapeHTML(item)}</li>`).join("")}</ul>
        <strong>강점</strong>
        <ul>${(analysis.strengths || []).map((item) => `<li>${escapeHTML(item)}</li>`).join("")}</ul>
      `;
    }
    if (teamRecommendationList) {
      const recommendations = data.recommendations || [];
      teamRecommendationList.innerHTML = recommendations.length
        ? recommendations.map((item) => `
            <article class="recommendation-card">
              <div>
                <strong>${escapeHTML(item.player.short_name)}</strong>
                <span>${escapeHTML(item.target_position)} 보강 · ${escapeHTML(item.current_player)} 대비 ${Number(item.score_lift || 0).toFixed(1)}</span>
              </div>
              <ul>${(item.reasons || []).map((reason) => `<li>${escapeHTML(reason)}</li>`).join("")}</ul>
            </article>
          `).join("")
        : "조건에 맞는 추천 후보가 없습니다.";
    }
  } catch {
    if (teamAnalysisBox) teamAnalysisBox.textContent = "팀 분석을 불러오지 못했습니다.";
  }
}

async function autoFillTeamSquad() {
  const league = teamLeagueSelect.value;
  const club = teamClubSelect.value;
  resetCurrentSquad();

  if (!club) {
    renderTeamBoard();
    renderPlayers(currentPlayers);
    return;
  }

  const params = new URLSearchParams({
    club,
    preset: presetSelect.value || "balanced",
    limit: "200",
  });
  if (league) params.set("league", league);

  dataStatus.textContent = `${club} 자동 스쿼드 구성 중`;

  try {
    const response = await fetch(`/api/fc26/players?${params.toString()}`);
    const data = await response.json();
    const players = sortByTeamPriority(data.players || []);
    const plan = currentPlan();
    const usedIds = new Set();
    const slots = currentFormationSlots();

    slots.forEach(([slot]) => {
      const selected = bestPlayerForSlot(players, usedIds, slot);
      if (!selected) return;
      plan.starters[slot] = selected;
      usedIds.add(String(selected.player_id));
    });

    selectedSlotId = slots[0]?.[0] || "";
    dataStatus.textContent = players.length
      ? `${club} 자동 스쿼드 구성 완료`
      : `${club} 선수 데이터를 찾지 못했습니다`;
    renderTeamBoard();
    renderPlayers(currentPlayers);
  } catch {
    dataStatus.textContent = "자동 스쿼드 구성 실패";
    renderTeamBoard();
    renderPlayers(currentPlayers);
  }
}

function restorePlan(target, saved = {}) {
  target.starters = saved.starters || {};
  target.bench = Array.isArray(saved.bench) ? saved.bench : [];
  target.positions = saved.positions || {};
  target.labels = saved.labels || {};
}

function loadSavedSquadState() {
  const raw = localStorage.getItem(SQUAD_STORAGE_KEY);
  if (!raw) return;
  try {
    const saved = JSON.parse(raw);
    Object.keys(squadState).forEach((key) => restorePlan(squadState[key], saved.squadState?.[key]));
    const controls = saved.controls || {};
    if (controls.teamLeague) {
      teamLeagueSelect.value = controls.teamLeague;
      const clubs = leagueClubMap[controls.teamLeague] || availableClubs;
      teamClubSelect.innerHTML = optionList(clubs, "클럽 선택");
    }
    if (controls.teamClub) teamClubSelect.value = controls.teamClub;
    if (controls.formation && FORMATIONS[controls.formation]) formationSelect.value = controls.formation;
    if (controls.teamRegion) teamRegionSelect.value = controls.teamRegion;
    if (controls.teamNationality) teamNationalitySelect.value = controls.teamNationality;
    if (controls.teamCandidateLeague) teamCandidateLeagueSelect.value = controls.teamCandidateLeague;
    selectedSlotId = saved.selectedSlotId || "";
  } catch {
    localStorage.removeItem(SQUAD_STORAGE_KEY);
  }
}

function addStarter(playerId) {
  const player = currentPlayers.find((item) => String(item.player_id) === String(playerId))
    || slotCandidatePlayers.find((item) => String(item.player_id) === String(playerId));
  if (!player || !selectedSlotId) return;
  const plan = currentPlan();
  if (isPlayerAssigned(player.player_id) && !isPlayerInSelectedSlot(player.player_id)) return;
  plan.starters[selectedSlotId] = player;
  plan.bench = plan.bench.filter((item) => String(item.player_id) !== String(player.player_id));

  const followingSlot = nextEmptySlot(selectedSlotId);
  if (followingSlot) {
    selectSlot(followingSlot);
  } else {
    renderTeamBoard();
    renderPlayers(currentPlayers);
  }
}

function addBench(playerId) {
  const player = currentPlayers.find((item) => String(item.player_id) === String(playerId));
  if (!player) return;
  if (isPlayerAssigned(player.player_id)) return;
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
    search: primarySearchTerm(searchInput.value),
    position: positionSelect.value,
    preset: presetSelect.value,
    region: regionSelect.value,
    nationality: nationalitySelect.value,
    league: leagueSelect.value,
    club: clubSelect.value,
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
  leagueSelect.innerHTML = optionList(meta.filters.leagues, "전체", leagueLabel);
  clubSelect.innerHTML = optionList(availableClubs, "전체");
  renderClubFilter();
  teamRegionSelect.innerHTML = optionList(meta.filters.regions, "전체");
  teamNationalitySelect.innerHTML = optionList(meta.filters.nationalities, "전체");
  teamCandidateLeagueSelect.innerHTML = optionList(meta.filters.leagues, "전체", leagueLabel);
  renderFormationOptions();
  renderTeamControls();
  loadSavedSquadState();
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
      const assigned = isPlayerAssigned(player.player_id);
      const inCurrentSlot = isPlayerInSelectedSlot(player.player_id);
      const starterDisabled = selectedSlotId && !assigned ? "" : "disabled";
      const benchDisabled = assigned ? "disabled" : "";
      const starterLabel = inCurrentSlot ? "선택됨" : assigned ? "배정됨" : "주전";
      const benchLabel = assigned ? "배정됨" : "예비";
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
              <button type="button" data-action="starter" data-player-id="${player.player_id}" ${starterDisabled}>${starterLabel}</button>
              <button type="button" data-action="bench" data-player-id="${player.player_id}" ${benchDisabled}>${benchLabel}</button>
            </div>
          </td>
        </tr>
      `;
    })
    .join("");
  activateImageFallbacks(playerRows);
  renderSlotCandidates();

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
searchInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") loadPlayers();
});
[positionSelect, presetSelect, regionSelect, nationalitySelect, leagueSelect, clubSelect].forEach((select) => {
  select.addEventListener("change", () => {
    if (select === positionSelect) renderPositionCategories(availablePositions);
    if (select === leagueSelect) renderClubFilter();
    loadPlayers();
  });
});
teamLeagueSelect.addEventListener("change", () => {
  const selectedLeague = teamLeagueSelect.value;
  const clubs = selectedLeague ? leagueClubMap[selectedLeague] || [] : availableClubs;
  teamClubSelect.innerHTML = optionList(clubs, "클럽 선택");
  teamClubSelect.value = "";
  resetCurrentSquad();
  renderTeamBoard();
  renderPlayers(currentPlayers);
});
teamClubSelect.addEventListener("change", autoFillTeamSquad);
[teamRegionSelect, teamNationalitySelect, teamCandidateLeagueSelect].forEach((select) => {
  select.addEventListener("change", () => {
    renderSlotCandidates();
    renderTeamAnalysis();
  });
});
formationSelect.addEventListener("change", () => {
  if (teamClubSelect.value) {
    autoFillTeamSquad();
  } else {
    resetCurrentSquad();
    renderTeamBoard();
    renderPlayers(currentPlayers);
  }
});
slotSelect.addEventListener("change", () => {
  selectSlot(slotSelect.value);
});
slotCandidateSearch?.addEventListener("input", renderSlotCandidates);
resetSquadButton.addEventListener("click", () => {
  resetCurrentSquad();
  renderTeamBoard();
  renderPlayers(currentPlayers);
});
saveSquadButton?.addEventListener("click", saveSquadState);
document.querySelectorAll(".quick-questions button").forEach((button) => {
  button.addEventListener("click", () => askQuestion(button.dataset.question));
});
chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  askQuestion(chatInput.value.trim());
});

loadMeta().then(loadPlayers);
