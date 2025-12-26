let puzzleData = null;
let selected = [];
let completed = [];

fetch("/api/puzzle")
  .then(res => res.json())
  .then(data => {
    puzzleData = data;
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

  fetch("/api/check", {
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
      showCompletedGroup(selected, categoryName, "groupFound");
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