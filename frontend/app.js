const API_BASE = window.location.origin.includes("localhost") || window.location.origin.includes("127.0.0.1")
  ? window.location.origin
  : "";

const state = {
  resumes: [],
  analytics: null,
  charts: {},
  user: null,
  authMode: "login",
  page: 1,
  pageSize: 5,
  selectedResumeId: null,
};

const els = {
  form: document.getElementById("upload-form"),
  fileInput: document.getElementById("resume-file"),
  dropArea: document.getElementById("drop-area"),
  classifyBtn: document.getElementById("classify-btn"),
  preview: document.getElementById("file-preview"),
  requiredSkills: document.getElementById("required-skills"),
  analysisCard: document.getElementById("analysis-card"),
  table: document.getElementById("candidate-table"),
  search: document.getElementById("search-input"),
  statusFilter: document.getElementById("status-filter"),
  sortSelect: document.getElementById("sort-select"),
  prevPage: document.getElementById("prev-page"),
  nextPage: document.getElementById("next-page"),
  pageSummary: document.getElementById("page-summary"),
  guidanceContent: document.getElementById("guidance-content"),
  detailTitle: document.getElementById("detail-title"),
  detailContent: document.getElementById("detail-content"),
  noteForm: document.getElementById("note-form"),
  noteInput: document.getElementById("note-input"),
  darkToggle: document.getElementById("dark-toggle"),
  toastContainer: document.getElementById("toast-container"),
  jobForm: document.getElementById("job-form"),
  jobTitle: document.getElementById("job-title"),
  jobDescription: document.getElementById("job-description"),
  jobList: document.getElementById("job-list"),
  authCard: document.getElementById("auth-card"),
  authForm: document.getElementById("auth-form"),
  authName: document.getElementById("auth-name"),
  authEmail: document.getElementById("auth-email"),
  authPassword: document.getElementById("auth-password"),
  authRole: document.getElementById("auth-role"),
  authSubmit: document.getElementById("auth-submit"),
  authMode: document.getElementById("auth-mode"),
  authTitle: document.getElementById("auth-title"),
  authCopy: document.getElementById("auth-copy"),
  sessionCard: document.getElementById("session-card"),
  sessionUser: document.getElementById("session-user"),
  sessionRole: document.getElementById("session-role"),
  logoutBtn: document.getElementById("logout-btn"),
};

function api(path, options = {}) {
  return fetch(`${API_BASE}${path}`, { credentials: "include", ...options }).then(async (res) => {
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || "Request failed");
    return data;
  });
}

function toast(message, type = "success") {
  const item = document.createElement("div");
  item.className = `toast ${type}`;
  item.textContent = message;
  els.toastContainer.appendChild(item);
  setTimeout(() => item.remove(), 3500);
}

function setLoading(isLoading) {
  els.classifyBtn.disabled = isLoading || !els.fileInput.files.length;
  els.classifyBtn.textContent = isLoading ? "Analyzing..." : "Run Analysis";
}

function updateFileState(file) {
  const count = els.fileInput.files.length;
  if (!file) {
    els.preview.textContent = "No file selected";
    els.classifyBtn.disabled = true;
    return;
  }
  const valid = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
  els.preview.textContent = valid ? (count > 1 ? `${count} PDF resumes selected` : file.name) : "Please choose a PDF file";
  els.classifyBtn.disabled = !valid;
}

els.fileInput.addEventListener("change", () => updateFileState(els.fileInput.files[0]));
els.dropArea.addEventListener("click", () => els.fileInput.click());
els.dropArea.addEventListener("keydown", (event) => {
  if (event.key === "Enter" || event.key === " ") els.fileInput.click();
});
els.dropArea.addEventListener("dragover", (event) => {
  event.preventDefault();
  els.dropArea.classList.add("drag-over");
});
els.dropArea.addEventListener("dragleave", () => els.dropArea.classList.remove("drag-over"));
els.dropArea.addEventListener("drop", (event) => {
  event.preventDefault();
  els.dropArea.classList.remove("drag-over");
  if (event.dataTransfer.files.length) {
    els.fileInput.files = event.dataTransfer.files;
    updateFileState(els.fileInput.files[0]);
  }
});

if (localStorage.getItem("darkMode") === "true") {
  document.body.classList.add("dark");
  els.darkToggle.checked = true;
}
els.darkToggle.addEventListener("change", () => {
  document.body.classList.toggle("dark", els.darkToggle.checked);
  localStorage.setItem("darkMode", els.darkToggle.checked);
  renderCharts();
});

els.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = els.fileInput.files[0];
  if (!file) return;

  const formData = new FormData();
  const files = Array.from(els.fileInput.files);
  const isBatch = files.length > 1;
  files.forEach((item) => formData.append(isBatch ? "resumes" : "resume", item));
  parseSkills(els.requiredSkills.value).forEach((skill) => formData.append("required_skills", skill));

  try {
    setLoading(true);
    const data = await api(isBatch ? "/api/resumes/batch" : "/api/resumes", { method: "POST", body: formData });
    if (isBatch) {
      const okCount = (data.items || []).filter((item) => item.ok).length;
      toast(`Batch processed: ${okCount}/${files.length} resumes`);
    } else {
      renderAnalysis(file.name, data.classification, data.score);
      toast("Resume analyzed successfully");
    }
    els.form.reset();
    updateFileState(null);
    await refreshAll();
  } catch (error) {
    toast(error.message, "error");
  } finally {
    setLoading(false);
  }
});

els.jobForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const payload = {
      title: els.jobTitle.value.trim() || "Untitled Role",
      description: els.jobDescription.value.trim(),
    };
    const data = await api("/api/job-descriptions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    els.requiredSkills.value = data.required_skills.join(", ");
    toast("Job skills extracted");
    els.jobForm.reset();
    await loadJobs();
  } catch (error) {
    toast(error.message, "error");
  }
});

els.search.addEventListener("input", () => {
  state.page = 1;
  renderTable();
});
els.statusFilter.addEventListener("change", () => {
  state.page = 1;
  renderTable();
});
els.sortSelect.addEventListener("change", renderTable);
els.prevPage.addEventListener("click", () => {
  state.page = Math.max(1, state.page - 1);
  renderTable();
});
els.nextPage.addEventListener("click", () => {
  state.page += 1;
  renderTable();
});

els.authMode.addEventListener("click", () => {
  state.authMode = state.authMode === "login" ? "register" : "login";
  renderAuth();
});

els.authForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    if (state.authMode === "register") {
      await api("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: els.authName.value.trim(),
          email: els.authEmail.value.trim(),
          password: els.authPassword.value,
          role: els.authRole.value,
        }),
      });
      toast("Registration complete. Logging you in...");
    }
    const data = await api("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: els.authEmail.value.trim(),
        password: els.authPassword.value,
      }),
    });
    state.user = data.user;
    els.authForm.reset();
    renderAuth();
    await refreshAll();
    await loadJobs();
  } catch (error) {
    toast(error.message, "error");
  }
});

els.logoutBtn.addEventListener("click", async () => {
  await api("/api/auth/logout", { method: "POST" });
  state.user = null;
  state.resumes = [];
  state.analytics = null;
  state.page = 1;
  renderAuth();
  renderMetrics();
  renderTable();
  renderSkills();
  toast("Logged out");
});

els.noteForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!state.selectedResumeId) return;
  try {
    await api(`/api/resumes/${state.selectedResumeId}/notes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ note: els.noteInput.value.trim() }),
    });
    els.noteInput.value = "";
    await loadCandidateDetail(state.selectedResumeId);
    toast("Note saved");
  } catch (error) {
    toast(error.message, "error");
  }
});

function parseSkills(value) {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

function renderAnalysis(filename, classification, score) {
  const skills = (classification.skills || []).slice(0, 12).map((skill) => `<span class="chip">${escapeHtml(skill)}</span>`).join("");
  const missing = (score.missing_skills || []).slice(0, 8).map((skill) => `<span class="chip warning">${escapeHtml(skill)}</span>`).join("");

  els.analysisCard.innerHTML = `
    <div class="section-head">
      <div>
        <p class="eyebrow">Latest Candidate Analysis</p>
        <h2>${escapeHtml(filename)}</h2>
      </div>
      <span class="status ${statusClass(score.status)}">${escapeHtml(score.status)}</span>
    </div>
    <div class="analysis-grid">
      <div><span>Category</span><strong>${escapeHtml(classification.category)}</strong></div>
      <div><span>Confidence</span><strong>${Math.round(classification.confidence * 100)}%</strong></div>
      <div><span>Experience</span><strong>${escapeHtml(classification.experience_level)}</strong></div>
      <div><span>Candidate Score</span><strong>${score.overall_score}%</strong></div>
    </div>
    <p class="explanation">${escapeHtml(classification.reason)}</p>
    <p class="explanation">${escapeHtml(score.explanation)}</p>
    <h3>Matched Skills</h3>
    <div class="chip-row">${skills || "<span class='muted'>No skills extracted</span>"}</div>
    ${missing ? `<h3>Skill Gaps</h3><div class="chip-row">${missing}</div>` : ""}
  `;
}

async function refreshAll() {
  const resumeData = await api("/api/resumes");
  state.resumes = resumeData.items || [];
  if (["admin", "recruiter"].includes(state.user?.role)) {
    state.analytics = await api("/api/analytics");
  } else {
    state.analytics = { total_resumes: state.resumes.length, average_score: 0, by_category: {}, status_counts: {}, skill_frequency: {}, upload_trend: {}, score_buckets: {} };
  }
  renderMetrics();
  renderTable();
  renderCharts();
  renderSkills();
}

async function loadJobs() {
  const data = await api("/api/job-descriptions");
  els.jobList.innerHTML = (data.items || []).map((job) => `
    <button class="job-pill" type="button" data-skills="${escapeHtml((job.required_skills || []).join(", "))}">
      <strong>${escapeHtml(job.title)}</strong>
      <span>${(job.required_skills || []).length} skills</span>
    </button>
  `).join("") || "<p class='muted'>No job descriptions saved yet.</p>";

  els.jobList.querySelectorAll(".job-pill").forEach((button) => {
    button.addEventListener("click", () => {
      els.requiredSkills.value = button.dataset.skills;
      toast("Target skills loaded");
    });
  });
}

function renderMetrics() {
  const data = state.analytics || {};
  const byCategory = data.by_category || {};
  const topCategory = Object.entries(byCategory).sort((a, b) => b[1] - a[1])[0]?.[0] || "-";
  document.getElementById("metric-total").textContent = data.total_resumes || 0;
  document.getElementById("metric-score").textContent = `${data.average_score || 0}%`;
  document.getElementById("metric-shortlist").textContent = (data.status_counts || {}).Shortlist || 0;
  document.getElementById("metric-category").textContent = topCategory;
}

function renderTable() {
  const query = els.search.value.toLowerCase();
  const status = els.statusFilter.value;
  const rows = state.resumes.filter((item) => {
    const matchesQuery = item.original_filename.toLowerCase().includes(query) || (item.category || "").toLowerCase().includes(query);
    const matchesStatus = !status || item.status === status;
    return matchesQuery && matchesStatus;
  });
  sortRows(rows);

  const totalPages = Math.max(1, Math.ceil(rows.length / state.pageSize));
  state.page = Math.min(state.page, totalPages);
  const start = (state.page - 1) * state.pageSize;
  const pageRows = rows.slice(start, start + state.pageSize);

  els.table.innerHTML = pageRows.map((item) => `
    <tr>
      <td>${escapeHtml(item.original_filename)}</td>
      <td>${escapeHtml(item.category || "Pending")}</td>
      <td><strong>${item.job_match_score ?? item.overall_score ?? 0}%</strong></td>
      <td><span class="status ${statusClass(item.status)}">${escapeHtml(item.status || "Review")}</span></td>
      <td>${(item.skills || []).slice(0, 4).map((skill) => `<span class="mini-chip">${escapeHtml(skill)}</span>`).join("")}</td>
      <td>
        <div class="action-stack">
          ${["admin", "recruiter"].includes(state.user?.role) ? `<select data-status-id="${item.id}" title="Update status">
            ${["Shortlist", "Review", "Hold", "Reject"].map((status) => `<option ${status === item.status ? "selected" : ""}>${status}</option>`).join("")}
          </select>` : ""}
          <button class="secondary-button" data-guidance-id="${item.id}" type="button">Guidance</button>
          ${["admin", "recruiter"].includes(state.user?.role) ? `<button class="secondary-button" data-detail-id="${item.id}" type="button">Detail</button>
          <a class="link-button" href="/api/resumes/${item.id}/report.pdf">PDF</a>
          <a class="link-button" href="/api/resumes/${item.id}/download">Resume</a>` : ""}
        </div>
      </td>
    </tr>
  `).join("") || `<tr><td colspan="6" class="muted">No candidates found.</td></tr>`;

  els.table.querySelectorAll("[data-status-id]").forEach((select) => {
    select.addEventListener("change", async () => {
      try {
        await api(`/api/resumes/${select.dataset.statusId}/status`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status: select.value }),
        });
        toast("Candidate status updated");
        await refreshAll();
      } catch (error) {
        toast(error.message, "error");
      }
    });
  });

  els.table.querySelectorAll("[data-guidance-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        const data = await api(`/api/resumes/${button.dataset.guidanceId}/guidance`);
        renderGuidance(data);
      } catch (error) {
        toast(error.message, "error");
      }
    });
  });

  els.table.querySelectorAll("[data-detail-id]").forEach((button) => {
    button.addEventListener("click", () => loadCandidateDetail(button.dataset.detailId));
  });

  els.pageSummary.textContent = rows.length
    ? `Showing ${start + 1}-${Math.min(start + state.pageSize, rows.length)} of ${rows.length} candidates`
    : "0 candidates";
  els.prevPage.disabled = state.page <= 1;
  els.nextPage.disabled = state.page >= totalPages;
}

async function loadCandidateDetail(resumeId) {
  const data = await api(`/api/resumes/${resumeId}`);
  state.selectedResumeId = resumeId;
  els.detailTitle.textContent = data.original_filename;
  els.noteForm.classList.remove("hidden");
  const list = (items = []) => items.length ? items.map((item) => `<li>${escapeHtml(item)}</li>`).join("") : "<li>No items found.</li>";
  const noteList = (data.notes || []).length
    ? data.notes.map((note) => `<li>${escapeHtml(note.note)} <span class="muted">(${escapeHtml(note.created_at || "")})</span></li>`).join("")
    : "<li>No recruiter notes yet.</li>";
  const historyList = (data.status_history || []).length
    ? data.status_history.map((event) => `<li>${escapeHtml(event.action)} ${escapeHtml(event.metadata?.status || "")}</li>`).join("")
    : "<li>No status history yet.</li>";
  els.detailContent.classList.remove("muted");
  els.detailContent.innerHTML = `
    <div class="detail-grid">
      <section class="detail-box"><h3>Summary</h3><p>${escapeHtml(data.text_excerpt || "No summary available.")}</p></section>
      <section class="detail-box"><h3>Scores</h3><p>Match: ${data.job_match_score ?? data.overall_score ?? 0}%</p><p>Status: ${escapeHtml(data.status || "Review")}</p></section>
      <section class="detail-box"><h3>Skills</h3><ul>${list(data.skills)}</ul></section>
      <section class="detail-box"><h3>Missing Skills</h3><ul>${list(data.missing_skills)}</ul></section>
      <section class="detail-box"><h3>Status History</h3><ul>${historyList}</ul></section>
      <section class="detail-box"><h3>Recruiter Notes</h3><ul>${noteList}</ul></section>
    </div>
  `;
}

function sortRows(rows) {
  const option = els.sortSelect.value;
  rows.sort((a, b) => {
    if (option === "score-desc") return (b.job_match_score ?? b.overall_score ?? 0) - (a.job_match_score ?? a.overall_score ?? 0);
    if (option === "score-asc") return (a.job_match_score ?? a.overall_score ?? 0) - (b.job_match_score ?? b.overall_score ?? 0);
    if (option === "name-asc") return a.original_filename.localeCompare(b.original_filename);
    return new Date(b.created_at || 0) - new Date(a.created_at || 0);
  });
}

function renderGuidance(data) {
  const list = (items = []) => items.length ? items.map((item) => `<li>${escapeHtml(item)}</li>`).join("") : "<li>No items found.</li>";
  els.guidanceContent.classList.remove("muted");
  els.guidanceContent.innerHTML = `
    <div class="guidance-grid">
      <section class="guidance-box"><h3>Target Role</h3><p>${escapeHtml(data.target_role)}</p></section>
      <section class="guidance-box"><h3>Strengths</h3><ul>${list(data.strengths)}</ul></section>
      <section class="guidance-box"><h3>Missing Skills</h3><ul>${list(data.missing_skills)}</ul></section>
      <section class="guidance-box"><h3>Resume Feedback</h3><ul>${list(data.resume_feedback)}</ul></section>
      <section class="guidance-box"><h3>Career Roadmap</h3><ul>${list(data.career_roadmap)}</ul></section>
      <section class="guidance-box"><h3>Certifications</h3><ul>${list(data.certification_recommendations)}</ul></section>
    </div>
  `;
}
function renderSkills() {
  const skills = state.analytics?.skill_frequency || {};
  els.skillFrequency = document.getElementById("skill-frequency");
  els.skillFrequency.innerHTML = Object.entries(skills).map(([skill, count]) => `
    <div class="skill-bar"><span>${escapeHtml(skill)}</span><strong>${count}</strong></div>
  `).join("") || "<p class='muted'>No skill data yet.</p>";
}

function renderCharts() {
  if (!window.Chart || !state.analytics) return;
  const textColor = document.body.classList.contains("dark") ? "#e5e7eb" : "#111827";
  drawChart("category-chart", "bar", state.analytics.by_category || {}, textColor);
  drawChart("status-chart", "doughnut", state.analytics.status_counts || {}, textColor);
  drawChart("upload-chart", "line", state.analytics.upload_trend || {}, textColor);
  drawChart("score-chart", "bar", state.analytics.score_buckets || {}, textColor);
}

function drawChart(id, type, values, textColor) {
  const ctx = document.getElementById(id);
  if (state.charts[id]) state.charts[id].destroy();
  state.charts[id] = new Chart(ctx, {
    type,
    data: {
      labels: Object.keys(values),
      datasets: [{
        data: Object.values(values),
        backgroundColor: type === "line" ? "rgba(37, 99, 235, 0.16)" : ["#2563eb", "#16a34a", "#f59e0b", "#dc2626", "#7c3aed"],
        borderColor: "#2563eb",
        borderWidth: type === "line" ? 2 : 0,
        tension: 0.35,
        fill: type === "line",
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { labels: { color: textColor } } },
      scales: ["bar", "line"].includes(type) ? {
        x: { ticks: { color: textColor }, grid: { display: false } },
        y: { ticks: { color: textColor, precision: 0 }, grid: { color: "rgba(148,163,184,.25)" } },
      } : {},
    },
  });
}

function statusClass(status = "") {
  return status.toLowerCase().replaceAll(" ", "-");
}

function escapeHtml(value = "") {
  return String(value).replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  }[char]));
}

async function loadSession() {
  try {
    const data = await api("/api/auth/me");
    state.user = data.user;
  } catch {
    state.user = null;
  }
  renderAuth();
  if (state.user) {
    await refreshAll();
    await loadJobs();
  } else {
    els.table.innerHTML = `<tr><td colspan="6" class="muted">Login or register to load saved candidates.</td></tr>`;
  }
}

function renderAuth() {
  const isRegister = state.authMode === "register";
  els.authTitle.textContent = state.user ? "Signed in" : (isRegister ? "Create account" : "Login");
  els.authCopy.textContent = state.user ? "Recruiter workspace is ready." : "Use a local account to access recruiter features.";
  els.authSubmit.textContent = isRegister ? "Register" : "Login";
  els.authMode.textContent = isRegister ? "Switch to Login" : "Switch to Register";
  els.authName.classList.toggle("hidden", !isRegister);
  els.authRole.classList.toggle("hidden", !isRegister);
  els.authForm.classList.toggle("hidden", Boolean(state.user));
  els.sessionCard.classList.toggle("hidden", !state.user);
  if (state.user) {
    els.sessionUser.textContent = state.user.name;
    els.sessionRole.textContent = state.user.role;
  }
  renderRoleViews();
}

function renderRoleViews() {
  const role = state.user?.role || "guest";
  document.querySelectorAll("[data-role-view]").forEach((section) => {
    const allowed = section.dataset.roleView.split(/\s+/);
    section.classList.toggle("hidden", !state.user || !allowed.includes(role));
  });
}

loadSession().catch(() => {
  document.getElementById("candidate-table").innerHTML = `<tr><td colspan="6" class="muted">Start the Flask backend to load saved candidates.</td></tr>`;
});

