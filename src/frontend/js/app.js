const state = {
  books: [],
  selectedBookId: null,
  selectedIds: new Set(),
  selectedBookDetail: null,
  activeJobId: null,
  activeBookId: null,
  ws: null,
};

const elements = {
  bookPathInput: document.getElementById("book-path-input"),
  addBookBtn: document.getElementById("add-book-btn"),
  refreshBtn: document.getElementById("refresh-btn"),
  runSelectedBtn: document.getElementById("run-selected-btn"),
  scheduleSelectedBtn: document.getElementById("schedule-selected-btn"),
  bookList: document.getElementById("book-list"),
  bookEmptyState: document.getElementById("book-empty-state"),
  globalMessage: document.getElementById("global-message"),
  detailTitle: document.getElementById("detail-title"),
  detailStatus: document.getElementById("detail-status"),
  detailMeta: document.getElementById("detail-meta"),
  previewFront: document.getElementById("preview-front"),
  previewBack: document.getElementById("preview-back"),
  settingsForm: document.getElementById("settings-form"),
  settingLanguage: document.getElementById("setting-language"),
  settingOptimize: document.getElementById("setting-optimize"),
  settingErrorPolicy: document.getElementById("setting-error-policy"),
  settingFrontCover: document.getElementById("setting-front-cover"),
  settingBackCover: document.getElementById("setting-back-cover"),
  settingResume: document.getElementById("setting-resume"),
  runBookBtn: document.getElementById("run-book-btn"),
  scheduleBookBtn: document.getElementById("schedule-book-btn"),
  progressSection: document.getElementById("progress-section"),
  progressJobId: document.getElementById("progress-job-id"),
  progressBar: document.getElementById("progress-bar"),
  progressText: document.getElementById("progress-text"),
  downloadLinks: document.getElementById("download-links"),
};

function setMessage(text, isError = false) {
  elements.globalMessage.textContent = text || "";
  elements.globalMessage.style.color = isError ? "#b63b45" : "";
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || `HTTP ${response.status}`);
  }
  if (response.status === 204) {
    return null;
  }
  return response.json();
}

function toBadgeClass(status) {
  if (["pending", "running", "done", "failed", "cancelled"].includes(status)) {
    return status;
  }
  return "pending";
}

function safeInt(value) {
  if (value === "" || value == null) {
    return null;
  }
  const parsed = Number.parseInt(value, 10);
  return Number.isNaN(parsed) ? null : parsed;
}

function next2amIso() {
  const now = new Date();
  const target = new Date(now);
  target.setHours(2, 0, 0, 0);
  if (target <= now) {
    target.setDate(target.getDate() + 1);
  }
  return target.toISOString();
}

function closeSocket() {
  if (state.ws) {
    state.ws.close();
    state.ws = null;
  }
}

function renderDownloads(bookId, status) {
  elements.downloadLinks.innerHTML = "";
  if (status !== "done") {
    return;
  }

  ["book.pdf", "book.txt", "report.json"].forEach((fileName) => {
    const link = document.createElement("a");
    link.href = `/api/output/${bookId}/${fileName}`;
    link.textContent = fileName;
    link.target = "_blank";
    link.rel = "noopener";
    elements.downloadLinks.appendChild(link);
  });
}

function updateProgressUI(payload) {
  elements.progressSection.hidden = false;
  elements.progressJobId.textContent = payload.job_id || "";
  elements.progressBar.style.width = `${payload.percent || 0}%`;
  elements.progressText.textContent = `${(payload.status || "").toUpperCase()} | ${
    payload.step_name || "-"
  } | ${payload.percent || 0}%`;
}

function openJobSocket(jobId, bookId) {
  closeSocket();

  const protocol = location.protocol === "https:" ? "wss" : "ws";
  const wsUrl = `${protocol}://${location.host}/ws/jobs/${jobId}`;
  const ws = new WebSocket(wsUrl);
  state.ws = ws;
  state.activeJobId = jobId;
  state.activeBookId = bookId;
  elements.progressSection.hidden = false;
  elements.progressJobId.textContent = jobId;

  ws.onmessage = async (event) => {
    const payload = JSON.parse(event.data);
    if (payload.type === "progress") {
      updateProgressUI(payload);
    }

    if (payload.type === "completion") {
      updateProgressUI({
        job_id: payload.job_id,
        status: payload.status,
        step_name: "complete",
        percent: payload.status === "done" ? 100 : 0,
      });
      renderDownloads(bookId, payload.status);
      await loadBooks(bookId);
      closeSocket();
    }
  };

  ws.onerror = () => {
    setMessage("WebSocket disconnected unexpectedly.", true);
  };
}

function renderBookList() {
  const { books, selectedBookId, selectedIds } = state;
  elements.bookList.innerHTML = "";
  elements.bookEmptyState.style.display = books.length ? "none" : "block";

  books.forEach((book) => {
    const item = document.createElement("li");
    item.className = "book-item";
    if (book.id === selectedBookId) {
      item.classList.add("active");
    }

    const rowTop = document.createElement("div");
    rowTop.className = "book-item-row";

    const main = document.createElement("div");
    main.className = "book-item-main";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = selectedIds.has(book.id);
    checkbox.addEventListener("click", (event) => {
      event.stopPropagation();
      if (checkbox.checked) {
        selectedIds.add(book.id);
      } else {
        selectedIds.delete(book.id);
      }
    });

    const title = document.createElement("span");
    title.className = "book-title";
    title.textContent = book.title;
    main.appendChild(checkbox);
    main.appendChild(title);

    const status = document.createElement("span");
    status.className = `status-badge ${toBadgeClass(book.status)}`;
    status.textContent = book.status;

    rowTop.appendChild(main);
    rowTop.appendChild(status);

    const meta = document.createElement("p");
    meta.className = "meta";
    meta.textContent = `${book.id} | stage: ${book.current_stage}`;

    item.appendChild(rowTop);
    item.appendChild(meta);

    item.addEventListener("click", () => selectBook(book.id));
    elements.bookList.appendChild(item);
  });
}

function fillChips(container, values) {
  container.innerHTML = "";
  if (!values || values.length === 0) {
    const empty = document.createElement("span");
    empty.className = "meta";
    empty.textContent = "No data";
    container.appendChild(empty);
    return;
  }

  values.forEach((value) => {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = value;
    container.appendChild(chip);
  });
}

function applyBookToSettings(book) {
  elements.settingLanguage.value = book.ocr_language || "kor+eng";
  elements.settingOptimize.value = book.optimize_mode || "basic";
  elements.settingErrorPolicy.value = book.error_policy || "skip";
  elements.settingFrontCover.value = book.front_cover ?? "";
  elements.settingBackCover.value = book.back_cover ?? "";
}

function renderDetail(book, preview = { front: [], back: [] }) {
  state.selectedBookDetail = book;
  elements.detailTitle.textContent = book.title;
  elements.detailStatus.className = `status-badge ${toBadgeClass(book.status)}`;
  elements.detailStatus.textContent = book.status;
  elements.detailMeta.textContent = `${book.id} | stage: ${book.current_stage} | source: ${book.source_path}`;
  applyBookToSettings(book);
  fillChips(elements.previewFront, preview.front);
  fillChips(elements.previewBack, preview.back);
  renderDownloads(book.id, book.status);
}

async function loadBooks(preferBookId = null) {
  try {
    state.books = await fetchJson("/api/books");
    if (preferBookId) {
      state.selectedBookId = preferBookId;
    } else if (
      state.selectedBookId &&
      !state.books.some((book) => book.id === state.selectedBookId)
    ) {
      state.selectedBookId = null;
    }
    renderBookList();
    if (state.selectedBookId) {
      await selectBook(state.selectedBookId);
    }
  } catch (error) {
    setMessage(error.message, true);
  }
}

async function selectBook(bookId) {
  try {
    state.selectedBookId = bookId;
    renderBookList();
    const book = await fetchJson(`/api/books/${bookId}`);
    const preview = await fetchJson(`/api/books/${bookId}/preview`).catch(() => ({
      front: [],
      back: [],
    }));
    renderDetail(book, preview);
  } catch (error) {
    setMessage(error.message, true);
  }
}

async function addBook() {
  const path = elements.bookPathInput.value.trim();
  if (!path) {
    setMessage("Please enter a directory path.", true);
    return;
  }

  try {
    const book = await fetchJson("/api/books", {
      method: "POST",
      body: JSON.stringify({ path }),
    });
    elements.bookPathInput.value = "";
    setMessage(`Added: ${book.title}`);
    await loadBooks(book.id);
  } catch (error) {
    setMessage(error.message, true);
  }
}

function settingsPayload() {
  return {
    ocr_language: elements.settingLanguage.value,
    optimize_mode: elements.settingOptimize.value,
    error_policy: elements.settingErrorPolicy.value,
    front_cover: safeInt(elements.settingFrontCover.value),
    back_cover: safeInt(elements.settingBackCover.value),
  };
}

async function saveSettings() {
  if (!state.selectedBookId) {
    setMessage("Select a book first.", true);
    return null;
  }

  try {
    const updated = await fetchJson(`/api/books/${state.selectedBookId}`, {
      method: "PATCH",
      body: JSON.stringify(settingsPayload()),
    });
    setMessage("Settings saved.");
    await loadBooks(updated.id);
    return updated;
  } catch (error) {
    setMessage(error.message, true);
    return null;
  }
}

async function createJob(bookId, { runNow, scheduledAt, resume = false }) {
  const payload = {
    book_id: bookId,
    run_now: runNow,
    scheduled_at: scheduledAt || null,
    resume,
  };
  const created = await fetchJson("/api/jobs", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  if (created.started) {
    openJobSocket(created.job.id, bookId);
  } else {
    elements.progressSection.hidden = false;
    elements.progressJobId.textContent = created.job.id;
    elements.progressBar.style.width = "0%";
    elements.progressText.textContent = "QUEUED";
  }
  return created;
}

async function runCurrentBookNow() {
  if (!state.selectedBookId) {
    setMessage("Select a book first.", true);
    return;
  }
  const updated = await saveSettings();
  if (!updated) {
    return;
  }
  try {
    const resume = elements.settingResume.checked;
    await createJob(updated.id, { runNow: true, scheduledAt: null, resume });
    setMessage("Job started.");
  } catch (error) {
    setMessage(error.message, true);
  }
}

async function scheduleCurrentBook() {
  if (!state.selectedBookId) {
    setMessage("Select a book first.", true);
    return;
  }
  const updated = await saveSettings();
  if (!updated) {
    return;
  }
  try {
    await createJob(updated.id, {
      runNow: false,
      scheduledAt: next2amIso(),
      resume: elements.settingResume.checked,
    });
    setMessage("Job scheduled for next 2AM.");
  } catch (error) {
    setMessage(error.message, true);
  }
}

async function runSelectedNow() {
  if (state.selectedIds.size === 0) {
    setMessage("Select at least one book.", true);
    return;
  }
  try {
    for (const id of state.selectedIds) {
      await createJob(id, { runNow: true, scheduledAt: null, resume: false });
    }
    setMessage(`Started ${state.selectedIds.size} jobs.`);
  } catch (error) {
    setMessage(error.message, true);
  }
}

async function scheduleSelected() {
  if (state.selectedIds.size === 0) {
    setMessage("Select at least one book.", true);
    return;
  }
  const scheduledAt = next2amIso();
  try {
    for (const id of state.selectedIds) {
      await createJob(id, { runNow: false, scheduledAt, resume: false });
    }
    setMessage(`Scheduled ${state.selectedIds.size} jobs.`);
  } catch (error) {
    setMessage(error.message, true);
  }
}

function bindEvents() {
  elements.addBookBtn.addEventListener("click", addBook);
  elements.refreshBtn.addEventListener("click", () => loadBooks(state.selectedBookId));
  elements.runSelectedBtn.addEventListener("click", runSelectedNow);
  elements.scheduleSelectedBtn.addEventListener("click", scheduleSelected);
  elements.settingsForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    await saveSettings();
  });
  elements.runBookBtn.addEventListener("click", runCurrentBookNow);
  elements.scheduleBookBtn.addEventListener("click", scheduleCurrentBook);
}

async function init() {
  bindEvents();
  await loadBooks();
}

init();

