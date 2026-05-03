// static/script_ai.js – SLOW, VISIBLE AI
let selectedDie = null;
let possibleMoves = [];
let highlightedSources = new Set();
let selectedSource = null;
let possibleTargets = new Map();
let gameOver = false;
let rollAnimationInterval = null;
let isRolling = false;
let pendingSource = null;
let isAIPlaying = false;

const AI_PLAYER = -1;

async function loadState() {
  const response = await fetch("/api/state");
  const data = await response.json();
  renderInfo(data);
  renderBoard(data.board);
  updateDiceUI(data.remaining_dice);
  resetSelection();
  gameOver = data.game_over;
  if (gameOver) {
    document.getElementById("roll-btn").disabled = true;
  } else {
    aiMoveIfNeeded();
  }
}

// ========== VERY SLOW AI TURN ==========
async function aiMoveIfNeeded() {
  if (gameOver || isAIPlaying) return;

  const currentPlayerText = document.getElementById("current-player").innerText;
  const isAITurn = currentPlayerText.includes("Player 2") && AI_PLAYER === -1;
  if (!isAITurn) return;

  isAIPlaying = true;
  const rollBtn = document.getElementById("roll-btn");
  rollBtn.disabled = true;

  // Show a status message
  const aiStatus = document.createElement("div");
  aiStatus.id = "ai-status";
  aiStatus.textContent = "AI is rolling dice...";
  aiStatus.style.position = "fixed";
  aiStatus.style.bottom = "120px";
  aiStatus.style.right = "30px";
  aiStatus.style.backgroundColor = "#222";
  aiStatus.style.color = "white";
  aiStatus.style.padding = "10px 20px";
  aiStatus.style.borderRadius = "8px";
  aiStatus.style.zIndex = "2000";
  document.body.appendChild(aiStatus);

  // 1. Roll dice for AI with slower animation
  await animateAIDiceRollSlow();

  // 2. Wait 2.5 seconds so human can read the dice
  aiStatus.textContent = "AI rolled. Waiting...";
  await delay(2500);

  // 3. Show thinking message
  aiStatus.textContent = "AI is thinking...";
  await delay(1000);

  // 4. Ask AI to move
  const moveRes = await fetch("/api/ai_move", { method: "POST" });
  const moveData = await moveRes.json();
  if (!moveRes.ok) {
    console.error("AI move failed:", moveData.error);
    aiStatus.remove();
    rollBtn.disabled = false;
    isAIPlaying = false;
    return;
  }

  // 5. Update board instantly
  aiStatus.textContent = "AI moved!";
  renderInfo(moveData);
  renderBoard(moveData.board);
  updateDiceUI(moveData.remaining_dice);
  resetSelection();

  // 6. Wait 1 second before handing back
  await delay(1000);

  aiStatus.remove();

  if (moveData.game_over) {
    gameOver = true;
    rollBtn.disabled = true;
  } else {
    rollBtn.disabled = false;
  }

  isAIPlaying = false;
}

async function animateAIDiceRollSlow() {
  const dice1 = document.getElementById("dice1");
  const dice2 = document.getElementById("dice2");
  dice1.style.display = "inline-block";
  dice2.style.display = "inline-block";

  let frames = 0;
  const maxFrames = 20;   // more frames = slower animation
  const interval = setInterval(() => {
    const rand1 = Math.floor(Math.random() * 6) + 1;
    const rand2 = Math.floor(Math.random() * 6) + 1;
    dice1.src = `/static/dice/dice${rand1}.png`;
    dice2.src = `/static/dice/dice${rand2}.png`;
    frames++;
    if (frames >= maxFrames) {
      clearInterval(interval);
      finishAIDiceRoll();
    }
  }, 70);   // slower interval (70ms instead of 50)
}

async function finishAIDiceRoll() {
  const response = await fetch("/api/roll");
  const data = await response.json();
  const dice1 = document.getElementById("dice1");
  const dice2 = document.getElementById("dice2");
  if (data.dice[0]) dice1.src = `/static/dice/dice${data.dice[0]}.png`;
  if (data.dice[1]) dice2.src = `/static/dice/dice${data.dice[1]}.png`;
  updateDiceUI(data.remaining_dice);
}

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
// ===========================================

function renderInfo(data) {
  const currentPlayerText = data.current_player === 1 ? "Player 1 (+)" : "Player 2 (-)";
  document.getElementById("current-player").textContent =
    data.game_over 
      ? (data.winner === 1 ? "Player 1 (White) wins!" : "Player 2 (Black) wins!")
      : `Current player: ${currentPlayerText}`;
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

  for (let i = 12; i <= 17; i++) {
    leftTop.appendChild(createPoint(board[i], i + 1, "top", i % 2 === 0 ? "dark" : "light"));
  }
  for (let i = 18; i <= 23; i++) {
    rightTop.appendChild(createPoint(board[i], i + 1, "top", i % 2 === 0 ? "light" : "dark"));
  }
  for (let i = 11; i >= 6; i--) {
    leftBottom.appendChild(createPoint(board[i], i + 1, "bottom", i % 2 === 0 ? "light" : "dark"));
  }
  for (let i = 5; i >= 0; i--) {
    rightBottom.appendChild(createPoint(board[i], i + 1, "bottom", i % 2 === 0 ? "dark" : "light"));
  }

  leftHalf.appendChild(leftTop);
  leftHalf.appendChild(leftBottom);
  rightHalf.appendChild(rightTop);
  rightHalf.appendChild(rightBottom);

  boardDiv.appendChild(leftHalf);
  boardDiv.appendChild(rightHalf);

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
  const visibleCount = Math.min(count, MAX_VISIBLE);
  const remaining = count - visibleCount;

  for (let i = 0; i < visibleCount; i++) {
    const checker = document.createElement("div");
    checker.className = `checker ${color}`;
    checkersDiv.appendChild(checker);
  }

  if (remaining > 0) {
    const badge = document.createElement("div");
    badge.className = `checker-badge ${color}`;
    badge.textContent = `+${remaining}`;
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
  dice1.classList.remove("dice-highlight");
  dice2.classList.remove("dice-highlight");
  if (!remainingDice || remainingDice.length === 0) return;

  dice1.src = `/static/dice/dice${remainingDice[0]}.png`;
  dice1.style.display = "inline-block";
  dice1.dataset.value = remainingDice[0];
  if (remainingDice[1]) {
    dice2.src = `/static/dice/dice${remainingDice[1]}.png`;
    dice2.style.display = "inline-block";
    dice2.dataset.value = remainingDice[1];
  } else {
    dice2.style.display = "none";
  }
}

async function rollDice() {
  if (isRolling || gameOver || isAIPlaying) return;

  const rollBtn = document.getElementById("roll-btn");
  const dice1 = document.getElementById("dice1");
  const dice2 = document.getElementById("dice2");

  rollBtn.disabled = true;
  isRolling = true;

  let frames = 0;
  const maxFrames = 12;

  rollAnimationInterval = setInterval(() => {
    const rand1 = Math.floor(Math.random() * 6) + 1;
    const rand2 = Math.floor(Math.random() * 6) + 1;
    dice1.src = `/static/dice/dice${rand1}.png`;
    dice2.src = `/static/dice/dice${rand2}.png`;
    dice1.style.display = "inline-block";
    dice2.style.display = "inline-block";

    frames++;
    if (frames >= maxFrames) {
      clearInterval(rollAnimationInterval);
      finishRoll();
    }
  }, 50);
}

async function finishRoll() {
  const response = await fetch("/api/roll");
  const data = await response.json();

  const dice1 = document.getElementById("dice1");
  const dice2 = document.getElementById("dice2");
  if (data.dice[0]) dice1.src = `/static/dice/dice${data.dice[0]}.png`;
  if (data.dice[1]) dice2.src = `/static/dice/dice${data.dice[1]}.png`;

  updateDiceUI(data.remaining_dice);
  await loadState();

  document.getElementById("roll-btn").disabled = false;
  isRolling = false;
}

async function onDieClick(event) {
  if (gameOver || isAIPlaying) return;
  const dieImg = event.currentTarget;
  const dieValue = parseInt(dieImg.dataset.value);
  if (isNaN(dieValue)) return;

  if (pendingSource !== null && selectedSource !== null) {
    selectedDie = dieValue;
    const resp = await fetch(`/api/legal_moves_for_die?die=${dieValue}`);
    const data = await resp.json();
    let moves = data.moves;
    moves = moves.filter(m => m.source === pendingSource);
    if (moves.length === 0) {
      alert("This die cannot move the selected checker");
      resetSelection();
      return;
    }
    possibleMoves = moves;
    highlightedSources.clear();
    possibleTargets.clear();
    highlightedSources.add(pendingSource);
    possibleTargets.set(pendingSource, []);
    for (let move of possibleMoves) {
      possibleTargets.get(pendingSource).push(move.target);
    }
    applyHighlights();
    pendingSource = null;
    document.querySelectorAll(".dice").forEach(d => d.classList.remove("dice-highlight"));
    return;
  }

  selectedDie = dieValue;
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

async function onPointClick(event) {
  if (gameOver || isAIPlaying) return;
  const pointDiv = event.currentTarget;
  const pointNumber = parseInt(pointDiv.dataset.point) - 1;

  if (selectedDie !== null) {
    if (selectedSource === null) {
      if (highlightedSources.has(pointNumber)) {
        selectedSource = pointNumber;
        applyHighlights();
      } else {
        resetSelection();
      }
    } else {
      const targets = possibleTargets.get(selectedSource) || [];
      if (targets.includes(pointNumber)) {
        const move = possibleMoves.find(m => m.source === selectedSource && m.target === pointNumber);
        if (move) executeMove(selectedDie, move);
        else resetSelection();
      } else {
        resetSelection();
      }
    }
    return;
  }

  const resp = await fetch(`/api/legal_dice_for_source?source=${pointNumber}`);
  const data = await resp.json();
  if (data.legal_dice && data.legal_dice.length > 0) {
    resetSelection();
    pendingSource = pointNumber;
    selectedSource = pointNumber;
    applyHighlights();
    highlightLegalDice(data.legal_dice);
  } else {
    resetSelection();
  }
}

function highlightLegalDice(diceValues) {
  const dice1 = document.getElementById("dice1");
  const dice2 = document.getElementById("dice2");
  [dice1, dice2].forEach(dice => {
    dice.classList.remove("dice-highlight");
    const val = parseInt(dice.dataset.value);
    if (diceValues.includes(val) && dice.style.display !== "none") {
      dice.classList.add("dice-highlight");
    }
  });
}

function applyHighlights() {
  document.querySelectorAll(".point").forEach(p => {
    p.classList.remove("possible-source", "possible-target", "selected-source");
  });
  document.getElementById("bear-off-hint").style.display = "none";

  for (let src of highlightedSources) {
    const elem = document.querySelector(`.point[data-point="${src+1}"]`);
    if (elem) elem.classList.add("possible-source");
  }
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

function resetSelection() {
  selectedDie = null;
  selectedSource = null;
  pendingSource = null;
  possibleMoves = [];
  highlightedSources.clear();
  possibleTargets.clear();
  document.querySelectorAll(".point").forEach(p => {
    p.classList.remove("possible-source", "possible-target", "selected-source");
  });
  document.getElementById("bear-off-hint").style.display = "none";
  document.querySelectorAll(".dice").forEach(d => d.classList.remove("dice-highlight"));
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
  renderInfo(data);
  renderBoard(data.board);
  updateDiceUI(data.remaining_dice);
  resetSelection();
  if (data.game_over) {
    gameOver = true;
    document.getElementById("roll-btn").disabled = true;
  } else {
    aiMoveIfNeeded();
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("roll-btn").addEventListener("click", rollDice);
  document.getElementById("cancel-selection").addEventListener("click", () => resetSelection());
  document.getElementById("dice1").addEventListener("click", onDieClick);
  document.getElementById("dice2").addEventListener("click", onDieClick);
  document.getElementById("bear-off-hint").addEventListener("click", () => {
    if (selectedSource !== null && !gameOver && !isAIPlaying) {
      const move = possibleMoves.find(m => m.source === selectedSource && m.target === null);
      if (move) executeMove(selectedDie, move);
      else resetSelection();
    }
  });
  loadState();
});
