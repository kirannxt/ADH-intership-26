/* ── Assessment App — Main JS ── */

document.addEventListener("DOMContentLoaded", () => {

  /* Auto-dismiss alerts */
  document.querySelectorAll(".alert").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity .5s";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 500);
    }, 4500);
  });

  /* Auth tabs (login / register toggle) */
  const authTabs = document.querySelectorAll(".auth-tab");
  const authPanels = document.querySelectorAll(".auth-panel");
  authTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      authTabs.forEach(t => t.classList.remove("active"));
      authPanels.forEach(p => p.classList.add("hidden"));
      tab.classList.add("active");
      const target = document.getElementById(tab.dataset.target);
      if (target) target.classList.remove("hidden");
    });
  });

  /* Option-item selection (radio/checkbox visual) */
  document.querySelectorAll(".option-item").forEach((item) => {
    item.addEventListener("click", () => {
      const input = item.querySelector("input");
      if (!input) return;
      if (input.type === "radio") {
        const name = input.name;
        document.querySelectorAll(`input[name="${name}"]`).forEach(r => {
          r.closest(".option-item")?.classList.remove("selected");
        });
      }
      input.checked = !input.checked || input.type === "radio";
      item.classList.toggle("selected", input.checked);
    });
  });

  /* Assessment card single-select */
  document.querySelectorAll(".assessment-card").forEach((card) => {
    card.addEventListener("click", () => {
      document.querySelectorAll(".assessment-card").forEach(c => c.classList.remove("selected"));
      card.classList.add("selected");
      const hidden = document.getElementById("selected-assessment");
      if (hidden) hidden.value = card.dataset.value || "";
    });
  });

  /* Animate score rings on load */
  document.querySelectorAll(".score-ring-fill").forEach((fill) => {
    const pct = parseFloat(fill.dataset.pct || 0);
    const r   = 70;
    const circ = 2 * Math.PI * r;
    fill.style.strokeDasharray  = circ;
    fill.style.strokeDashoffset = circ;
    setTimeout(() => {
      fill.style.strokeDashoffset = circ - (circ * pct / 100);
    }, 200);
  });

  /* Animate score bar rows */
  document.querySelectorAll(".score-row-fill").forEach((bar) => {
    const pct = bar.dataset.pct || "0";
    bar.style.width = "0";
    setTimeout(() => { bar.style.width = pct + "%"; }, 300);
  });

  /* Processing screen step animation */
  const pSteps = document.querySelectorAll(".p-step");
  if (pSteps.length) {
    let i = 0;
    const advance = () => {
      if (i < pSteps.length) {
        if (i > 0) pSteps[i-1].classList.replace("active","done");
        pSteps[i].classList.add("active");
        i++;
        setTimeout(advance, 1100);
      } else {
        pSteps[pSteps.length-1].classList.replace("active","done");
        // Redirect after processing
        const redir = document.getElementById("processing-redirect");
        if (redir) setTimeout(() => { window.location.href = redir.dataset.url; }, 800);
      }
    };
    setTimeout(advance, 400);
  }

  /* Password toggle */
  document.querySelectorAll(".pwd-toggle").forEach((btn) => {
    btn.addEventListener("click", () => {
      const inp = document.getElementById(btn.dataset.target);
      if (!inp) return;
      inp.type = inp.type === "password" ? "text" : "password";
      btn.textContent = inp.type === "password" ? "👁" : "🙈";
    });
  });

  /* Progress bar: highlight active step in step-indicator */
  const currentStep = document.getElementById("current-step");
  if (currentStep) {
    const idx = parseInt(currentStep.value, 10);
    document.querySelectorAll(".step").forEach((s, i) => {
      if (i < idx)  { s.classList.add("completed"); s.querySelector(".step-circle").textContent = "✓"; }
      if (i === idx){ s.classList.add("active"); }
    });
  }

});
