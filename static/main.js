let puzzleData = null;
let puzzleName = null;
let selected = [];
let completed = [];
const GROUP_COLORS = ["green", "red", "blue", "purple"];

// Use puzzle name from URL if present, otherwise fetch a random one
const urlParams = new URLSearchParams(window.location.search);
const requestedPuzzle = urlParams.get("puzzle");
const fetchUrl = requestedPuzzle
  ? `/api/puzzle?name=${encodeURIComponent(requestedPuzzle)}`
  : "/api/puzzle";

fetch(fetchUrl)
  .then(res => res.json())
  .then(data => {
    puzzleData = data;
    puzzleName = data.name;
    // Pin the puzzle in the URL so refreshes keep the same puzzle
    if (!requestedPuzzle && puzzleName) {
      const url = new URL(window.location);
      url.searchParams.set("puzzle", puzzleName);
      history.replaceState(null, "", url);
    }
    renderGrid();
  });

function renderGrid() {
  const grid = document.getElementById("grid");
  grid.innerHTML = "";

  puzzleData.words.forEach(word => {
    const div = document.createElement("div");
    div.className = "word";
    div.textContent = word;
    div.onclick = () => toggleSelect(div, word);
    grid.appendChild(div);
  });
}

function toggleSelect(el, word) {
  if (selected.includes(word)) {
    selected = selected.filter(w => w !== word);
    el.classList.remove("selected");
  } else if (selected.length < 4) {
    selected.push(word);
    el.classList.add("selected");
  }
}

document.getElementById("submitBtn").onclick = () => {
  if (selected.length !== 4) {
    alert("Pick 4 words!");
    return;
  }

  fetch(`/api/check?name=${encodeURIComponent(puzzleName)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ group: selected })
  })
  .then(res => res.json())
  .then(resp => {
    document.getElementById("result").textContent =
      resp.correct ? "✅ Correct!" : "❌ Try again";

    if(resp.correct){
      // Example category name; you could let the backend return a real one
      let categoryName = resp.category || "Category";
      // remove words from overall grid
      removeFromGrid(selected);
      // show in completed UI
      const difficultyIndex = puzzleData.categories.indexOf(categoryName);
      showCompletedGroup(selected, categoryName, `groupFound ${GROUP_COLORS[difficultyIndex]}`);
      // mark as completed and show celebration if all found
      completed.push(categoryName);
      const totalSets = puzzleData && puzzleData.sets ? puzzleData.sets.length : 4;
      if (completed.length >= totalSets) {
        showCelebration();
      }
    }

    clearSelection();
  });
};

function clearSelection() {
  selected = [];
  document.querySelectorAll(".word.selected").forEach(el => el.classList.remove("selected"));
}

function showCompletedGroup(group, categoryName, colorClass){
  const container = document.getElementById("completedGroups");

  const groupDiv = document.createElement("div");
  groupDiv.className = "completedGroup " + colorClass;

  const title = document.createElement("div");
  title.className = "groupTitle";
  title.textContent = categoryName;

  const listDiv = document.createElement("div");
  listDiv.className = "groupWords";

  group.forEach(w => {
    const wEl = document.createElement("div");
    wEl.className = "groupWord";
    wEl.textContent = w;
    listDiv.appendChild(wEl);
  });

  groupDiv.appendChild(title);
  groupDiv.appendChild(listDiv);

  container.appendChild(groupDiv);
}

function removeFromGrid(wordsToRemove) {
  // Remove from the puzzle data array
  puzzleData.words = puzzleData.words.filter(
    w => !wordsToRemove.includes(w)
  );

  // Re-draw the grid
  renderGrid();
}

// --- Create Puzzle Modal ---

const modal = document.getElementById("createPuzzleModal");
const categoryFormsDiv = document.getElementById("categoryForms");
const createError = document.getElementById("createError");
const puzzleNameInput = document.getElementById("puzzleName");
const createSubmitBtn = document.getElementById("createSubmitBtn");

function generatePuzzleName() {
  const hex = Math.random().toString(16).slice(2, 6);
  return `puzzle-${hex}`;
}

function buildCategoryForms() {
  categoryFormsDiv.innerHTML = "";
  for (let i = 0; i < 4; i++) {
    const section = document.createElement("div");
    section.className = "category-section";
    section.innerHTML = `
      <label>Category ${i + 1} Name</label>
      <input type="text" class="cat-name" data-index="${i}" placeholder="e.g. Fruits">
      <div class="cat-words">
        <input type="text" class="cat-word" data-cat="${i}" placeholder="Word 1">
        <input type="text" class="cat-word" data-cat="${i}" placeholder="Word 2">
        <input type="text" class="cat-word" data-cat="${i}" placeholder="Word 3">
        <input type="text" class="cat-word" data-cat="${i}" placeholder="Word 4">
      </div>
    `;
    categoryFormsDiv.appendChild(section);
  }
}

function validateModalForm() {
  const catNames = document.querySelectorAll(".cat-name");
  const catWords = document.querySelectorAll(".cat-word");
  let allFilled = true;
  catNames.forEach(input => { if (!input.value.trim()) allFilled = false; });
  catWords.forEach(input => { if (!input.value.trim()) allFilled = false; });
  createSubmitBtn.disabled = !allFilled;
}

document.getElementById("createPuzzleBtn").onclick = () => {
  puzzleNameInput.value = generatePuzzleName();
  createError.textContent = "";
  createSubmitBtn.disabled = true;
  buildCategoryForms();
  modal.style.display = "flex";

  // Live validation on input
  categoryFormsDiv.addEventListener("input", validateModalForm);
};

document.getElementById("createCancelBtn").onclick = () => {
  modal.style.display = "none";
};

// Close modal on overlay click (not content)
modal.onclick = (e) => {
  if (e.target === modal) modal.style.display = "none";
};

createSubmitBtn.onclick = () => {
  createError.textContent = "";

  const name = puzzleNameInput.value.trim();
  const categories = [];
  for (let i = 0; i < 4; i++) {
    const catName = document.querySelector(`.cat-name[data-index="${i}"]`).value.trim();
    const wordInputs = document.querySelectorAll(`.cat-word[data-cat="${i}"]`);
    const words = Array.from(wordInputs).map(el => el.value.trim());
    categories.push({ name: catName, words });
  }

  // Client-side duplicate word check
  const allWords = categories.flatMap(c => c.words.map(w => w.toUpperCase()));
  if (new Set(allWords).size !== allWords.length) {
    createError.textContent = "Duplicate words found. Each word must be unique.";
    return;
  }

  const payload = { categories };
  if (name) payload.name = name;

  fetch("/api/puzzle", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
  .then(res => res.json().then(data => ({ status: res.status, data })))
  .then(({ status, data }) => {
    if (status === 201) {
      modal.style.display = "none";
      alert(`Puzzle "${data.name}" created successfully!`);
    } else {
      createError.textContent = data.error || "Failed to create puzzle.";
    }
  });
};

// show a big celebratory message when all groups are found
function showCelebration(){
  // prevent duplicates
  if (document.getElementById('celebrationOverlay')) return;
  const overlay = document.createElement('div');
  overlay.id = 'celebrationOverlay';
  overlay.className = 'celebration';
  overlay.innerHTML = `
    <div class="celebrationContent">
      <h1>Máquina!!</h1>
    </div>
  `;
  // optionally allow click to dismiss
  overlay.onclick = () => overlay.remove();
  document.body.appendChild(overlay);
  // scroll to top to ensure it's visible
  window.scrollTo({ top: 0, behavior: 'smooth' });
}