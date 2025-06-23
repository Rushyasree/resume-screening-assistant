const form = document.getElementById("upload-form");
const fileInput = document.getElementById("resume-file");
const dropArea = document.getElementById("drop-area");
const classifyBtn = document.getElementById("classify-btn");
const loading = document.getElementById("loading");
const result = document.getElementById("result");
const groupedResumes = document.getElementById("grouped-resumes");
const searchInput = document.getElementById("search-input");
const dateFilter = document.getElementById("date-filter");
const exportBtn = document.getElementById("export-btn");
const darkToggle = document.getElementById("dark-toggle");
const sortSelect = document.getElementById("sort-select");
const clearBtn = document.getElementById("clear-btn");
const toastContainer = document.createElement("div");
toastContainer.id = "toast-container";
document.body.appendChild(toastContainer);

let history = JSON.parse(localStorage.getItem("resumeHistory")) || [];

// 🌓 Dark Mode
if (localStorage.getItem("darkMode") === "true") {
  document.body.classList.add("dark");
  darkToggle.checked = true;
}
darkToggle?.addEventListener("change", () => {
  document.body.classList.toggle("dark");
  localStorage.setItem("darkMode", darkToggle.checked);
});

// 📎 File Preview
fileInput.addEventListener("change", () => {
  classifyBtn.disabled = !fileInput.files.length || fileInput.files[0].type !== "application/pdf";
  showPreview(fileInput.files[0]);
});

dropArea.addEventListener("click", () => fileInput.click());
dropArea.addEventListener("dragover", e => {
  e.preventDefault();
  dropArea.style.background = "#e0f7fa";
});
dropArea.addEventListener("dragleave", () => {
  dropArea.style.background = "#f9f9f9";
});
dropArea.addEventListener("drop", e => {
  e.preventDefault();
  const files = e.dataTransfer.files;
  if (files.length && files[0].type === "application/pdf") {
    fileInput.files = files;
    classifyBtn.disabled = false;
    showPreview(files[0]);
  }
  dropArea.style.background = "#f9f9f9";
});

function showPreview(file) {
  const preview = document.getElementById("file-preview") || document.createElement("div");
  preview.id = "file-preview";
  preview.textContent = `📄 Selected: ${file.name}`;
  dropArea.insertAdjacentElement("afterend", preview);
}

// 🔥 Toast
function showToast(message, success = true) {
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.style.background = success ? "#28a745" : "#dc3545";
  toast.innerText = message;
  toastContainer.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

// 🎯 Classification
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const file = fileInput.files[0];
  if (!file || file.type !== "application/pdf") return;

  loading.classList.remove("hidden");
  result.innerText = "";
  const formData = new FormData();
  formData.append("resume", file);

  try {
    const res = await fetch("/classify", {
      method: "POST",
      body: formData,
    });

    const data = await res.json();
    if (!res.ok || !data.category) throw new Error(data.error || "Unknown classification error");

    const record = {
      filename: file.name,
      category: data.category,
      timestamp: new Date().toISOString(),
    };
    history.push(record);
    localStorage.setItem("resumeHistory", JSON.stringify(history));

    showToast("✅ Resume classified successfully");
    updateUI(history);
  } catch (err) {
    showToast(`❌ ${err.message}`, false);
  } finally {
    loading.classList.add("hidden");
    form.reset();
    classifyBtn.disabled = true;
    const preview = document.getElementById("file-preview");
    if (preview) preview.remove();
  }
});

// 🔁 UI Update
function updateUI(data) {
  const grouped = data.reduce((acc, item) => {
    acc[item.category] = acc[item.category] || [];
    acc[item.category].push(item);
    return acc;
  }, {});

  groupedResumes.innerHTML = "";
  for (const category in grouped) {
    const group = document.createElement("div");
    group.className = "category-group";

    const heading = document.createElement("h3");
    heading.innerText = `${category} (${grouped[category].length})`;
    group.appendChild(heading);

    const list = document.createElement("ul");
    grouped[category].forEach((item) => {
      const li = document.createElement("li");
      const date = new Date(item.timestamp).toLocaleString();
      const filename = document.createElement("span");
      filename.textContent = `${item.filename} — ${date}`;
      const downloadBtn = document.createElement("a");
      downloadBtn.href = `/data/${item.filename}`;
      downloadBtn.innerText = "⬇";
      downloadBtn.title = "Download";
      downloadBtn.style.marginLeft = "0.5rem";
      downloadBtn.target = "_blank";
      li.appendChild(filename);
      li.appendChild(downloadBtn);
      list.appendChild(li);
    });

    group.appendChild(list);
    groupedResumes.appendChild(group);
  }
}

// 🔽 Sorting
sortSelect?.addEventListener("change", () => {
  const option = sortSelect.value;
  let sorted = [...history];
  if (option === "date-asc") sorted.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
  else if (option === "date-desc") sorted.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
  else if (option === "name-asc") sorted.sort((a, b) => a.filename.localeCompare(b.filename));
  else if (option === "name-desc") sorted.sort((a, b) => b.filename.localeCompare(a.filename));
  updateUI(sorted);
});

// 🔍 Search
searchInput.addEventListener("input", () => {
  const query = searchInput.value.toLowerCase();
  const filtered = history.filter((item) => item.filename.toLowerCase().includes(query));
  updateUI(filtered);
});

// 📅 Filter by Date
dateFilter.addEventListener("change", () => {
  const selected = dateFilter.value;
  const filtered = history.filter((item) => item.timestamp.startsWith(selected));
  updateUI(filtered);
});

// ⬇ Export CSV
exportBtn.addEventListener("click", () => {
  if (!history.length) return;
  const csv = "Filename,Category,Timestamp\n" + history.map(h => `${h.filename},${h.category},${h.timestamp}`).join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "classification_history.csv";
  a.click();
});

// 🧹 Clear History
clearBtn?.addEventListener("click", () => {
  if (!confirm("Clear all history?")) return;
  history = [];
  localStorage.removeItem("resumeHistory");
  updateUI(history);
  showToast("🧹 History cleared");
});

// 🔄 Initial Render
updateUI(history);
