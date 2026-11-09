function initMatching() {
  function updateMaxOptionsWarning(table) {
    const max = Number.parseInt(table.dataset.maxResponsePerOption, 10);
    const warning = document.getElementById(`${table.dataset.answerName}-max-options-warning`);
    if (!warning || Number.isNaN(max)) return;
    const counts = new Map();
    table.querySelectorAll('input[type="radio"]:checked').forEach((radio) => {
        counts.set(radio.value, (counts.get(radio.value) || 0) + 1);
      });
    warning.hidden = Array.from(counts.values()).every((count) => count <= max);
  }

  document.querySelectorAll(".pl-matching-radio-matrix-container[data-max-response-per-option]")
    .forEach(updateMaxOptionsWarning);

  document.addEventListener("change", (event) => {
    const table = event.target.closest(".pl-matching-radio-matrix-container");
    if (table) updateMaxOptionsWarning(table);
  });

  document.addEventListener("click", (event) => {
    const button = event.target.closest(".pl-matching-reset-btn");
    if (!button) return;

    const ratio_matrix_name = button.attributes["radio-matrix-name"].value;

    const container = document.getElementById(ratio_matrix_name);
    if (!container) return;

    container.querySelectorAll('input[type="radio"]:checked').forEach((radio) => {
    radio.checked = false;
    radio.dispatchEvent(new Event("change", { bubbles: true }));
    });
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initMatching);
} else {
  initMatching();
}
