/* ════════════════════════════════════════════
   AssessMe — Main JS
   ════════════════════════════════════════════ */

document.addEventListener("DOMContentLoaded", () => {

  /* ──────────────────────────────────────────
     1. Auto-dismiss alerts after 5 s
  ────────────────────────────────────────── */
  document.querySelectorAll(".alert").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity .5s";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 500);
    }, 5000);
  });


  /* ──────────────────────────────────────────
     2. Mobile hamburger nav
  ────────────────────────────────────────── */
  const hamburger = document.getElementById("hamburger");
  const mobileNav = document.getElementById("mobile-nav");
  if (hamburger && mobileNav) {
    hamburger.addEventListener("click", () => {
      const open = hamburger.classList.toggle("open");
      mobileNav.classList.toggle("open", open);
      hamburger.setAttribute("aria-expanded", open);
    });
  }


  /* ──────────────────────────────────────────
     3. Modal helpers
  ────────────────────────────────────────── */
  function openModal(id) {
    const overlay = document.getElementById(id);
    if (!overlay) return;
    overlay.classList.add("open");
    overlay.removeAttribute("aria-hidden");
    // trap focus on first focusable element
    const first = overlay.querySelector("button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])");
    if (first) first.focus();
  }
  function closeModal(id) {
    const overlay = document.getElementById(id);
    if (!overlay) return;
    overlay.classList.remove("open");
    overlay.setAttribute("aria-hidden", "true");
  }

  // Open via data-modal-open
  document.querySelectorAll("[data-modal-open]").forEach((btn) => {
    btn.addEventListener("click", () => openModal(btn.dataset.modalOpen));
  });
  // Close via data-modal-close or .modal-close button
  document.querySelectorAll("[data-modal-close], .modal-close").forEach((btn) => {
    btn.addEventListener("click", () => {
      const overlay = btn.closest(".modal-overlay");
      if (overlay) closeModal(overlay.id);
    });
  });
  // Close on backdrop click
  document.querySelectorAll(".modal-overlay").forEach((overlay) => {
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) closeModal(overlay.id);
    });
  });
  // Close on Escape
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      document.querySelectorAll(".modal-overlay.open").forEach((o) => closeModal(o.id));
    }
  });
  // Expose globally so inline onclick can use it
  window.openModal  = openModal;
  window.closeModal = closeModal;


  /* ──────────────────────────────────────────
     4. Auth — single-page tabs (login / register)
        Works when both panels exist on one page.
  ────────────────────────────────────────── */
  const authTabs   = document.querySelectorAll(".auth-tab[data-target]");
  const authPanels = document.querySelectorAll(".auth-panel");
  if (authTabs.length && authPanels.length) {
    authTabs.forEach((tab) => {
      tab.addEventListener("click", (e) => {
        e.preventDefault();
        authTabs.forEach(t  => { t.classList.remove("active"); t.setAttribute("aria-selected","false"); });
        authPanels.forEach(p => p.classList.add("hidden"));
        tab.classList.add("active");
        tab.setAttribute("aria-selected","true");
        const panel = document.getElementById(tab.dataset.target);
        if (panel) panel.classList.remove("hidden");
      });
    });
  }


  /* ──────────────────────────────────────────
     5. Password visibility toggle
  ────────────────────────────────────────── */
  document.querySelectorAll(".pwd-toggle").forEach((btn) => {
    btn.addEventListener("click", () => {
      const inp = document.getElementById(btn.dataset.target);
      if (!inp) return;
      const show = inp.type === "password";
      inp.type = show ? "text" : "password";
      btn.setAttribute("aria-label", show ? "Hide password" : "Show password");
      btn.querySelector(".pwd-icon").textContent = show ? "🙈" : "👁";
    });
  });


  /* ──────────────────────────────────────────
     6. Password strength meter
  ────────────────────────────────────────── */
  const pwdInput = document.getElementById("password");
  const strengthEl = document.getElementById("pwd-strength");
  if (pwdInput && strengthEl) {
    pwdInput.addEventListener("input", () => {
      const v = pwdInput.value;
      let score = 0;
      if (v.length >= 8)                  score++;
      if (/[A-Z]/.test(v))                score++;
      if (/[0-9]/.test(v))                score++;
      if (/[^A-Za-z0-9]/.test(v))         score++;
      const levels = ["", "pwd-s-weak", "pwd-s-fair", "pwd-s-good", "pwd-s-strong"];
      const labels = ["", "Weak", "Fair", "Good", "Strong"];
      strengthEl.className = "pwd-strength " + (levels[score] || "");
      const txt = strengthEl.querySelector(".pwd-strength-text");
      if (txt) txt.textContent = labels[score] || "";
    });
  }


  /* ──────────────────────────────────────────
     7. Inline form validation
  ────────────────────────────────────────── */
  document.querySelectorAll("form.validated").forEach((form) => {
    form.addEventListener("submit", (e) => {
      let valid = true;
      form.querySelectorAll("[required]").forEach((field) => {
        const err = field.parentElement.querySelector(".form-error");
        if (!field.value.trim()) {
          field.classList.add("is-invalid");
          if (err) err.textContent = "⚠ This field is required.";
          valid = false;
        } else {
          field.classList.remove("is-invalid");
          field.classList.add("is-valid");
          if (err) err.textContent = "";
        }
      });
      // Password confirmation check
      const pwd  = form.querySelector("#password");
      const pwd2 = form.querySelector("#confirm_password");
      if (pwd && pwd2 && pwd.value !== pwd2.value) {
        pwd2.classList.add("is-invalid");
        const err2 = pwd2.parentElement.querySelector(".form-error");
        if (err2) err2.textContent = "⚠ Passwords do not match.";
        valid = false;
      }
      if (!valid) e.preventDefault();
    });

    // Live field feedback
    form.querySelectorAll(".form-control").forEach((field) => {
      field.addEventListener("blur", () => {
        const err = field.parentElement.querySelector(".form-error");
        if (field.required && !field.value.trim()) {
          field.classList.add("is-invalid");
          field.classList.remove("is-valid");
          if (err) err.textContent = "⚠ This field is required.";
        } else if (field.value.trim()) {
          field.classList.remove("is-invalid");
          field.classList.add("is-valid");
          if (err) err.textContent = "";
        }
      });
    });
  });


  /* ──────────────────────────────────────────
     8. Option-item selection (radio/checkbox visual)
  ────────────────────────────────────────── */
  document.querySelectorAll(".option-item").forEach((item) => {
    item.addEventListener("click", () => {
      const input = item.querySelector("input");
      if (!input) return;
      if (input.type === "radio") {
        document.querySelectorAll(`input[name="${input.name}"]`).forEach(r => {
          r.closest(".option-item")?.classList.remove("selected");
        });
        input.checked = true;
      } else {
        input.checked = !input.checked;
      }
      item.classList.toggle("selected", input.checked);
    });
    // Keyboard support
    item.setAttribute("tabindex", "0");
    item.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); item.click(); }
    });
  });


  /* ──────────────────────────────────────────
     9. Rating buttons (1-5 scale)
  ────────────────────────────────────────── */
  document.querySelectorAll(".rating-group").forEach((group) => {
    const hidden = group.querySelector("input[type='hidden']");
    group.querySelectorAll(".rating-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        group.querySelectorAll(".rating-btn").forEach(b => b.classList.remove("selected"));
        btn.classList.add("selected");
        if (hidden) hidden.value = btn.dataset.value;
        // trigger answer-map update
        group.dispatchEvent(new CustomEvent("answered", { bubbles: true }));
      });
    });
  });


  /* ──────────────────────────────────────────
     10. Yes/No buttons
  ────────────────────────────────────────── */
  document.querySelectorAll(".yesno-group").forEach((group) => {
    const hidden = group.querySelector("input[type='hidden']");
    group.querySelectorAll(".yesno-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        group.querySelectorAll(".yesno-btn").forEach(b => b.classList.remove("selected"));
        btn.classList.add("selected");
        if (hidden) hidden.value = btn.dataset.value;
        group.dispatchEvent(new CustomEvent("answered", { bubbles: true }));
      });
    });
  });


  /* ──────────────────────────────────────────
     11. Frequency buttons
  ────────────────────────────────────────── */
  document.querySelectorAll(".freq-group").forEach((group) => {
    const hidden = group.querySelector("input[type='hidden']");
    group.querySelectorAll(".freq-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        group.querySelectorAll(".freq-btn").forEach(b => b.classList.remove("selected"));
        btn.classList.add("selected");
        if (hidden) hidden.value = btn.dataset.value;
        group.dispatchEvent(new CustomEvent("answered", { bubbles: true }));
      });
    });
  });


  /* ──────────────────────────────────────────
     12. Assessment card single-select
  ────────────────────────────────────────── */
  document.querySelectorAll(".assessment-card").forEach((card) => {
    card.addEventListener("click", () => {
      document.querySelectorAll(".assessment-card").forEach(c => {
        c.classList.remove("selected");
        c.setAttribute("aria-pressed", "false");
      });
      card.classList.add("selected");
      card.setAttribute("aria-pressed", "true");
      const hidden = document.getElementById("selected-assessment");
      if (hidden) hidden.value = card.dataset.value || "";
    });
    card.setAttribute("tabindex", "0");
    card.setAttribute("role", "button");
    card.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); card.click(); }
    });
  });


  /* ──────────────────────────────────────────
     13. Questionnaire navigation with answer
         persistence, keyboard nav, answer map,
         unsaved-changes warning
  ────────────────────────────────────────── */
  const questionCards = document.querySelectorAll(".question-card[data-qnum]");
  if (questionCards.length) {
    let current = 1;
    const total = questionCards.length;
    // Restore saved answers from sessionStorage
    const storedAnswers = JSON.parse(sessionStorage.getItem("quizAnswers") || "{}");

    function getCard(n) {
      return document.querySelector(`.question-card[data-qnum="${n}"]`);
    }

    function markAnswered(qnum) {
      const dot = document.querySelector(`.answer-dot[data-qnum="${qnum}"]`);
      if (dot) dot.classList.add("answered");
      updateUnansweredCount();
    }

    function updateUnansweredCount() {
      const total_q = questionCards.length;
      const answered = document.querySelectorAll(".answer-dot.answered").length;
      const el = document.getElementById("answered-count");
      if (el) el.textContent = answered;
      const rem = document.getElementById("remaining-count");
      if (rem) rem.textContent = total_q - answered;
    }

    function updateProgress(n) {
      const pct = Math.round((n / total) * 100);
      const bar = document.getElementById("q-progress");
      const pctEl = document.getElementById("q-pct");
      const curEl = document.getElementById("q-current");
      if (bar)   bar.style.width   = pct + "%";
      if (pctEl) pctEl.textContent = pct + "%";
      if (curEl) curEl.textContent = n;
    }

    function showQuestion(n) {
      questionCards.forEach(c => c.classList.add("hidden"));
      const card = getCard(n);
      if (card) {
        card.classList.remove("hidden");
        card.focus();
      }
      // Update answer map active dot
      document.querySelectorAll(".answer-dot").forEach(d => d.classList.remove("current"));
      const dot = document.querySelector(`.answer-dot[data-qnum="${n}"]`);
      if (dot) dot.classList.add("current");

      // Update nav buttons
      const prev = document.getElementById("btn-prev");
      const next = document.getElementById("btn-next");
      if (prev) prev.disabled = (n === 1);
      if (next) {
        if (n === total) {
          next.textContent = "Review Answers";
          next.dataset.last = "true";
        } else {
          next.textContent = "Next →";
          delete next.dataset.last;
        }
      }
      updateProgress(n);
    }

    function changeQ(dir) {
      const next = current + dir;
      if (next < 1 || next > total) return;
      current = next;
      showQuestion(current);
    }

    // Answer map dot click
    document.querySelectorAll(".answer-dot[data-qnum]").forEach((dot) => {
      dot.addEventListener("click", () => {
        current = parseInt(dot.dataset.qnum, 10);
        showQuestion(current);
      });
    });

    // Restore saved answers into DOM
    function restoreAnswer(qnum, value) {
      const card = getCard(qnum);
      if (!card) return;
      // Radio/checkbox option items
      card.querySelectorAll(".option-item input").forEach(inp => {
        if (inp.value === value) {
          inp.checked = true;
          inp.closest(".option-item")?.classList.add("selected");
        }
      });
      // Rating buttons
      card.querySelectorAll(".rating-btn").forEach(btn => {
        if (btn.dataset.value === value) btn.classList.add("selected");
      });
      // Yes/No
      card.querySelectorAll(".yesno-btn").forEach(btn => {
        if (btn.dataset.value === value) btn.classList.add("selected");
      });
      // Freq
      card.querySelectorAll(".freq-btn").forEach(btn => {
        if (btn.dataset.value === value) btn.classList.add("selected");
      });
      // Hidden inputs
      card.querySelectorAll("input[type='hidden']").forEach(inp => {
        if (inp.name === `q${qnum}`) inp.value = value;
      });
      markAnswered(qnum);
    }

    Object.entries(storedAnswers).forEach(([k, v]) => {
      const n = parseInt(k.replace("q",""), 10);
      restoreAnswer(n, v);
    });

    // Capture answers and persist to sessionStorage
    function captureAnswer(qnum, value) {
      storedAnswers[`q${qnum}`] = value;
      sessionStorage.setItem("quizAnswers", JSON.stringify(storedAnswers));
      markAnswered(qnum);
    }

    // Listen for any answer selection inside a question card
    questionCards.forEach((card) => {
      const qnum = parseInt(card.dataset.qnum, 10);
      // option items
      card.querySelectorAll(".option-item input").forEach(inp => {
        inp.addEventListener("change", () => {
          if (inp.checked) captureAnswer(qnum, inp.value);
        });
      });
      // rating, yesno, freq via custom event
      card.addEventListener("answered", (e) => {
        const hidden = card.querySelector(`input[name="q${qnum}"]`);
        if (hidden && hidden.value) captureAnswer(qnum, hidden.value);
      });
    });

    // Expose for inline onclick
    window.changeQ = changeQ;

    // Next button
    const btnNext = document.getElementById("btn-next");
    if (btnNext) {
      btnNext.addEventListener("click", () => {
        if (btnNext.dataset.last) {
          document.getElementById("quiz-form")?.submit();
        } else {
          changeQ(1);
        }
      });
    }
    const btnPrev = document.getElementById("btn-prev");
    if (btnPrev) btnPrev.addEventListener("click", () => changeQ(-1));

    // Keyboard navigation: left/right arrow keys
    document.addEventListener("keydown", (e) => {
      if (document.activeElement?.closest(".form-control")) return; // don't hijack text input
      if (e.key === "ArrowRight") changeQ(1);
      if (e.key === "ArrowLeft")  changeQ(-1);
    });

    // Unsaved-changes warning
    let quizDirty = false;
    document.querySelectorAll(".option-item input, .rating-btn, .yesno-btn, .freq-btn").forEach(el => {
      el.addEventListener("click", () => { quizDirty = true; });
    });
    window.addEventListener("beforeunload", (e) => {
      if (quizDirty) {
        e.preventDefault();
        e.returnValue = "You have unsaved answers. Are you sure you want to leave?";
      }
    });
    // Clear dirty flag on deliberate submit
    document.getElementById("quiz-form")?.addEventListener("submit", () => { quizDirty = false; });

    // Init
    showQuestion(1);
    updateUnansweredCount();
  }


  /* ──────────────────────────────────────────
     14. Score ring animation (SVG donut)
  ────────────────────────────────────────── */
  document.querySelectorAll(".score-ring-fill").forEach((fill) => {
    const pct  = parseFloat(fill.dataset.pct || 0);
    const r    = 70;
    const circ = 2 * Math.PI * r;
    fill.style.strokeDasharray  = circ;
    fill.style.strokeDashoffset = circ;
    setTimeout(() => {
      fill.style.strokeDashoffset = circ - (circ * pct / 100);
    }, 300);
  });


  /* ──────────────────────────────────────────
     15. Score bar row animations
  ────────────────────────────────────────── */
  document.querySelectorAll(".score-row-fill").forEach((bar) => {
    bar.style.width = "0";
    setTimeout(() => { bar.style.width = (bar.dataset.pct || "0") + "%"; }, 400);
  });


  /* ──────────────────────────────────────────
     16. Processing step animation + redirect
  ────────────────────────────────────────── */
  const pSteps = document.querySelectorAll(".p-step");
  if (pSteps.length) {
    let i = 0;
    const advance = () => {
      if (i < pSteps.length) {
        if (i > 0) pSteps[i-1].classList.replace("active", "done");
        pSteps[i].classList.add("active");
        i++;
        setTimeout(advance, 1100);
      } else {
        pSteps[pSteps.length - 1].classList.replace("active", "done");
        sessionStorage.removeItem("quizAnswers"); // clear persisted answers on submit
        const redir = document.getElementById("processing-redirect");
        if (redir) {
          setTimeout(() => { window.location.href = redir.dataset.url; }, 800);
        }
      }
    };
    setTimeout(advance, 600);

    // Error state: show after 15 s if redirect hasn't happened
    setTimeout(() => {
      const errorEl = document.getElementById("processing-error");
      if (errorEl) errorEl.classList.remove("hidden");
    }, 15000);
  }


  /* ──────────────────────────────────────────
     17. History page: client-side filter
  ────────────────────────────────────────── */
  const historySearch = document.getElementById("history-search");
  const historyRows   = document.querySelectorAll(".history-item[data-name]");
  const historyType   = document.getElementById("filter-type");
  const historyStatus = document.getElementById("filter-status");

  function applyHistoryFilters() {
    const q      = (historySearch?.value || "").toLowerCase();
    const type   = (historyType?.value   || "all").toLowerCase();
    const status = (historyStatus?.value || "all").toLowerCase();
    historyRows.forEach(row => {
      const name = (row.dataset.name   || "").toLowerCase();
      const t    = (row.dataset.type   || "").toLowerCase();
      const s    = (row.dataset.status || "").toLowerCase();
      const matchQ      = !q      || name.includes(q);
      const matchType   = type   === "all" || t === type;
      const matchStatus = status === "all" || s === status;
      row.style.display = (matchQ && matchType && matchStatus) ? "" : "none";
    });
    // Show empty state if nothing visible
    const emptyState = document.getElementById("history-empty");
    if (emptyState) {
      const visible = [...historyRows].filter(r => r.style.display !== "none");
      emptyState.classList.toggle("hidden", visible.length > 0);
    }
  }

  if (historySearch) historySearch.addEventListener("input",  applyHistoryFilters);
  if (historyType)   historyType.addEventListener("change",   applyHistoryFilters);
  if (historyStatus) historyStatus.addEventListener("change", applyHistoryFilters);


  /* ──────────────────────────────────────────
     18. Recommendations filter tabs
  ────────────────────────────────────────── */
  document.querySelectorAll(".rec-filter-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".rec-filter-btn").forEach(b => b.classList.replace("btn-primary", "btn-secondary"));
      btn.classList.replace("btn-secondary", "btn-primary");
      const filter = btn.dataset.filter.toLowerCase();
      document.querySelectorAll(".rec-card[data-filter]").forEach(card => {
        const match = filter === "all" || card.dataset.filter.toLowerCase() === filter;
        card.style.display = match ? "" : "none";
      });
    });
  });


  /* ──────────────────────────────────────────
     19. FAQ accordion
  ────────────────────────────────────────── */
  document.querySelectorAll(".faq-question").forEach((btn) => {
    btn.addEventListener("click", () => {
      const expanded = btn.getAttribute("aria-expanded") === "true";
      // Close all
      document.querySelectorAll(".faq-question").forEach(b => {
        b.setAttribute("aria-expanded", "false");
        const ans = document.getElementById(b.dataset.answer);
        if (ans) ans.classList.remove("open");
      });
      // Open clicked (unless it was already open)
      if (!expanded) {
        btn.setAttribute("aria-expanded", "true");
        const ans = document.getElementById(btn.dataset.answer);
        if (ans) ans.classList.add("open");
      }
    });
  });


  /* ──────────────────────────────────────────
     20. Step indicator: mark from data attribute
  ────────────────────────────────────────── */
  const stepIndicator = document.getElementById("step-indicator");
  if (stepIndicator) {
    const activeIdx = parseInt(stepIndicator.dataset.active || "0", 10);
    stepIndicator.querySelectorAll(".step").forEach((s, i) => {
      if (i < activeIdx) {
        s.classList.add("completed");
        const circle = s.querySelector(".step-circle");
        if (circle) circle.textContent = "✓";
      } else if (i === activeIdx) {
        s.classList.add("active");
      }
    });
  }

});
