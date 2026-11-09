function initMatching() {
  function updateMaxOptionsWarning(container) {
    const max = Number.parseInt(container.dataset.maxResponsePerOption, 10);
    const warning = document.getElementById(`${container.dataset.answerName}-max-options-warning`);
    if (!warning || Number.isNaN(max)) return;

    const counts = new Map();
    container.querySelectorAll("select").forEach((select) => {
      const value = select.value;
      if (value === "-1") return;
      counts.set(value, (counts.get(value) || 0) + 1);
    });
    warning.hidden = Array.from(counts.values()).every((count) => count <= max);
  }

  document.querySelectorAll(".pl-matching-container[data-max-response-per-option]")
    .forEach(updateMaxOptionsWarning);

  document.addEventListener("change", (event) => {
    const container = event.target.closest(".pl-matching-container");
    if (container) updateMaxOptionsWarning(container);
  });

  document.addEventListener("click", (event) => {
    const button = event.target.closest(".pl-matching-reset-btn");
    if (!button) return;

    const name = button.attributes["data-answers-name"].value;

    const container = document.getElementById(`${name}-container`);
    if (!container) return;
    
    container.querySelectorAll("select").forEach((select) => {
      select.selectedIndex = 0;
      select.dispatchEvent(new Event("change", { bubbles: true }));
    });
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initMatching);
} else {
  initMatching();
}
