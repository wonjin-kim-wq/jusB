const API_BASE = "/api/notes";

const form = document.getElementById("note-form");
const titleInput = document.getElementById("note-title");
const contentInput = document.getElementById("note-content");
const idInput = document.getElementById("note-id");
const submitBtn = document.getElementById("submit-btn");
const cancelBtn = document.getElementById("cancel-btn");
const noteList = document.getElementById("note-list");
const noteCount = document.getElementById("note-count");
const emptyMessage = document.getElementById("empty-message");
const statusMessage = document.getElementById("status-message");

function showError(message) {
  statusMessage.textContent = message;
  statusMessage.hidden = false;
  setTimeout(() => {
    statusMessage.hidden = true;
  }, 4000);
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function resetForm() {
  idInput.value = "";
  titleInput.value = "";
  contentInput.value = "";
  submitBtn.textContent = "추가하기";
  cancelBtn.hidden = true;
}

async function fetchNotes() {
  try {
    const res = await fetch(API_BASE);
    const data = await res.json();
    renderNotes(data.items || []);
  } catch (err) {
    showError("메모 목록을 불러오지 못했어요.");
  }
}

function renderNotes(notes) {
  noteList.innerHTML = "";
  noteCount.textContent = `${notes.length}개`;
  emptyMessage.hidden = notes.length > 0;

  notes.forEach((note) => {
    const li = document.createElement("li");
    li.className = "note-item";
    li.innerHTML = `
      <h3 class="note-item-title">${escapeHtml(note.title)}</h3>
      <p class="note-item-content">${escapeHtml(note.content)}</p>
      <div class="note-item-meta">수정됨: ${escapeHtml(note.updated_at)}</div>
      <div class="note-item-actions">
        <button class="btn-edit" data-id="${note.id}">수정</button>
        <button class="btn-delete" data-id="${note.id}">삭제</button>
      </div>
    `;
    li.querySelector(".btn-edit").addEventListener("click", () => startEdit(note));
    li.querySelector(".btn-delete").addEventListener("click", () => deleteNote(note.id));
    noteList.appendChild(li);
  });
}

function startEdit(note) {
  idInput.value = note.id;
  titleInput.value = note.title;
  contentInput.value = note.content;
  submitBtn.textContent = "수정 완료";
  cancelBtn.hidden = false;
  titleInput.focus();
}

cancelBtn.addEventListener("click", resetForm);

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const title = titleInput.value.trim();
  const content = contentInput.value.trim();
  const id = idInput.value;

  if (!title) {
    showError("제목을 입력해 주세요.");
    return;
  }

  try {
    let res;
    if (id) {
      res = await fetch(`${API_BASE}/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, content }),
      });
    } else {
      res = await fetch(API_BASE, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, content }),
      });
    }

    if (!res.ok) {
      const err = await res.json();
      showError(err.error?.message || "요청을 처리하지 못했어요.");
      return;
    }

    resetForm();
    fetchNotes();
  } catch (err) {
    showError("서버와 통신하지 못했어요.");
  }
});

async function deleteNote(id) {
  if (!confirm("이 메모를 삭제할까요?")) return;
  try {
    const res = await fetch(`${API_BASE}/${id}`, { method: "DELETE" });
    if (!res.ok) {
      const err = await res.json();
      showError(err.error?.message || "삭제하지 못했어요.");
      return;
    }
    fetchNotes();
  } catch (err) {
    showError("서버와 통신하지 못했어요.");
  }
}

fetchNotes();
