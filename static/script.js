let selectedDie = null;
let possibleMoves = [];          // {type, source, target}
let highlightedSources = new Set();
let selectedSource = null;
let possibleTargets = new Map(); // source -> array of target indices (or null for bear off)

async function loadState() {
  const response = await fetch("/api/state");
  const data = await response.json();
  renderInfo(data);
  renderBoard(data.board);
  updateDiceUI(data.remaining_dice);
  resetSelection();
}

function renderInfo(data) {
  const currentPlayerText =
    data.current_player === 1 ? "Player 1 (+)" : "Player 2 (-)";
  document.getElementById("current-player").textContent =
    `Current player: ${currentPlayerText}`;
  document.getElementById("borne-off").textContent =
    `Borne off: P1=${data.borne_off["1"]}, P2=${data.borne_off["-1"]}`;
}

function renderBoard(board) {
  const boardDiv = document.getElementById("board");
  boardDiv.innerHTML = "";

  const horizontalLine = document.createElement("div");
  horizontalLine.className = "board-horizontal-line";
  boardDiv.appendChild(horizontalLine);

  const middleBar = document.createElement("div");
  middleBar.className = "middle-bar";
  boardDiv.appendChild(middleBar);

  const leftHalf = document.createElement("div");
  leftHalf.className = "half left";
  const rightHalf = document.createElement("div");
  rightHalf.className = "half right";

  const leftTop = document.createElement("div");
  leftTop.className = "row top";
  const leftBottom = document.createElement("div");
  leftBottom.className = "row bottom";
  const rightTop = document.createElement("div");
  rightTop.className = "row top";
  const rightBottom = document.createElement("div");
  rightBottom.className = "row bottom";

  // points 13..18 (index 12..17)
  for (let i = 12; i <= 17; i++) {
    leftTop.appendChild(createPoint(board[i], i + 1, "top", i % 2 === 0 ? "dark" : "light"));
  }
  // points 19..24 (index 18..23)
  for (let i = 18; i <= 23; i++) {
    rightTop.appendChild(createPoint(board[i], i + 1, "top", i % 2 === 0 ? "light" : "dark"));
  }
  // points 12..7 (index 11 down to 6)
  for (let i = 11; i >= 6; i--) {
    leftBottom.appendChild(createPoint(board[i], i + 1, "bottom", i % 2 === 0 ? "light" : "dark"));
  }
  // points 6..1 (index 5 down to 0)
  for (let i = 5; i >= 0; i--) {
    rightBottom.appendChild(createPoint(board[i], i + 1, "bottom", i % 2 === 0 ? "dark" : "light"));
  }

  leftHalf.appendChild(leftTop);
  leftHalf.appendChild(leftBottom);
  rightHalf.appendChild(rightTop);
  rightHalf.appendChild(rightBottom);

  boardDiv.appendChild(leftHalf);
  boardDiv.appendChild(rightHalf);

  // reattach board click events
  attachBoardEvents();
}

function createPoint(value, label, rowType, colorType) {
  const pointDiv = document.createElement("div");
  pointDiv.className = `point ${colorType}`;
  pointDiv.dataset.point = label;

  const wrapper = document.createElement("div");
  wrapper.className = rowType;

  const triangle = document.createElement("div");
  triangle.className = "triangle";

  const labelDiv = document.createElement("div");
  labelDiv.className = "point-label";
  labelDiv.textContent = label;

  const checkersDiv = document.createElement("div");
  checkersDiv.className = "checkers";

  wrapper.appendChild(labelDiv);
  wrapper.appendChild(triangle);
  wrapper.appendChild(checkersDiv);
  pointDiv.appendChild(wrapper);

  const count = Math.abs(value);
  const color = value > 0 ? "white" : "black";
  const MAX_VISIBLE = 6;

  // how many to show as individual checkers
  const visibleCount = Math.min(count, MAX_VISIBLE);
  const remaining = count - visibleCount;

  for (let i = 0; i < visibleCount; i++) {
    const checker = document.createElement("div");
    checker.className = `checker ${color}`;
    // reduce overlap to keep them inside triangle
    const step = rowType === "top" ? 32 : 32;
    if (rowType === "top") {
      checker.style.top = `${i * step}px`;
    } else {
      checker.style.bottom = `${i * step}px`;
    }
    checkersDiv.appendChild(checker);
  }

  if (remaining > 0) {
    const badge = document.createElement("div");
    badge.className = `checker-badge ${color}`;
    badge.textContent = `+${remaining}`;
    // position the badge below/above the visible stack
    if (rowType === "top") {
      badge.style.top = `${visibleCount * 32}px`;
    } else {
      badge.style.bottom = `${visibleCount * 32}px`;
    }
    checkersDiv.appendChild(badge);
  }

  return pointDiv;
}

function attachBoardEvents() {
  document.querySelectorAll(".point").forEach(point => {
    point.removeEventListener("click", onPointClick);
    point.addEventListener("click", onPointClick);
  });
}

function updateDiceUI(remainingDice) {
  const dice1 = document.getElementById("dice1");
  const dice2 = document.getElementById("dice2");
  dice1.style.display = "none";
  dice2.style.display = "none";
  if (!remainingDice || remainingDice.length === 0) return;

  dice1.src = `/static/dice/dice${remainingDice[0]}.png`;
  dice1.style.display = "inline-block";
  dice1.dataset.value = remainingDice[0];
  if (remainingDice[1]) {
    dice2.src = `/static/dice/dice${remainingDice[1]}.png`;
    dice2.style.display = "inline-block";
    dice2.dataset.value = remainingDice[1];
  }
}

async function rollDice() {
  resetSelection();
  const response = await fetch("/api/roll");
  const data = await response.json();
  updateDiceUI(data.remaining_dice);
  await loadState(); // refresh board and info
}

async function onDieClick(event) {
  const dieImg = event.currentTarget;
  const dieValue = parseInt(dieImg.dataset.value);
  if (isNaN(dieValue)) return;
  selectedDie = dieValue;
  // fetch legal moves for this die
  const resp = await fetch(`/api/legal_moves_for_die?die=${dieValue}`);
  const data = await resp.json();
  possibleMoves = data.moves;
  highlightedSources.clear();
  possibleTargets.clear();

  for (const move of possibleMoves) {
    highlightedSources.add(move.source);
    if (!possibleTargets.has(move.source)) possibleTargets.set(move.source, []);
    possibleTargets.get(move.source).push(move.target);
  }
  applyHighlights();
}

function applyHighlights() {
  // clear previous highlights
  document.querySelectorAll(".point").forEach(p => {
    p.classList.remove("possible-source", "possible-target", "selected-source");
  });
  document.getElementById("bear-off-hint").style.display = "none";

  for (let src of highlightedSources) {
    const elem = document.querySelector(`.point[data-point="${src+1}"]`);
    if (elem) elem.classList.add("possible-source");
  }
  // if a source is selected, show its targets
  if (selectedSource !== null) {
    const srcElem = document.querySelector(`.point[data-point="${selectedSource+1}"]`);
    if (srcElem) srcElem.classList.add("selected-source");
    const targets = possibleTargets.get(selectedSource) || [];
    for (let t of targets) {
      if (t === null) {
        document.getElementById("bear-off-hint").style.display = "block";
      } else {
        const tElem = document.querySelector(`.point[data-point="${t+1}"]`);
        if (tElem) tElem.classList.add("possible-target");
      }
    }
  }
}

function onPointClick(event) {
  const pointDiv = event.currentTarget;
  const pointNumber = parseInt(pointDiv.dataset.point) - 1; // 0‑based

  if (selectedSource === null) {
    // choose source
    if (highlightedSources.has(pointNumber)) {
      selectedSource = pointNumber;
      applyHighlights();
    } else {
      resetSelection();
    }
  } else {
    // choose target
    const targets = possibleTargets.get(selectedSource) || [];
    if (targets.includes(pointNumber)) {
      // find the move
      const move = possibleMoves.find(m => m.source === selectedSource && m.target === pointNumber);
      if (move) executeMove(selectedDie, move);
      else resetSelection();
    } else {
      resetSelection();
    }
  }
}

function resetSelection() {
  selectedSource = null;
  selectedDie = null;
  possibleMoves = [];
  highlightedSources.clear();
  possibleTargets.clear();
  document.querySelectorAll(".point").forEach(p => {
    p.classList.remove("possible-source", "possible-target", "selected-source");
  });
  document.getElementById("bear-off-hint").style.display = "none";
}

async function executeMove(die, move) {
  const response = await fetch("/api/apply_die_move", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ die: die, move: move })
  });
  const data = await response.json();
  if (!response.ok) {
    alert(data.error || "Move failed");
    resetSelection();
    return;
  }
  // update UI
  renderInfo(data);
  renderBoard(data.board);
  updateDiceUI(data.remaining_dice);
  resetSelection();
  // if no dice left, allow new roll; otherwise the dice remain clickable
}

// bear off click
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("roll-btn").addEventListener("click", rollDice);
  document.getElementById("cancel-selection").addEventListener("click", () => resetSelection());
  document.getElementById("dice1").addEventListener("click", onDieClick);
  document.getElementById("dice2").addEventListener("click", onDieClick);
  document.getElementById("bear-off-hint").addEventListener("click", () => {
    if (selectedSource !== null) {
      const move = possibleMoves.find(m => m.source === selectedSource && m.target === null);
      if (move) executeMove(selectedDie, move);
      else resetSelection();
    }
  });
  loadState();
});