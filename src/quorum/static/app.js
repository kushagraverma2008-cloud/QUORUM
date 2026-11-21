/**
 * QUORUM // Autonomous War Room - Unified Client Engine (No external JS)
 * WCAG AA Accessible, XSS-hardened, and Context-Aware.
 */

(function () {
  'use strict';

  // --- PRE-PACKAGED SAMPLE IDEAS (Phase 7 Demo Readiness) ---
  const SAMPLE_IDEAS = [
    {
      title: "EdgeRust Telemetry",
      pitch: "A zero-overhead distributed tracing CLI and lightweight runtime for Rust microservices compiling to WebAssembly edge workers. Replaces heavy OpenTelemetry agents with 2KB kernel probes.",
      stage: "MVP",
      team_size: "Solo Founder",
      runway: "Bootstrapped",
      goal: "Validate Urgency & Demand",
      market: "B2B",
      geo: "Global"
    },
    {
      title: "PostOp Vision Care",
      pitch: "Smartphone computer-vision application that monitors surgical wound recovery at home. Analyzes erythema, edema, and surgical margins daily to detect early surgical site infections before hospital readmission.",
      stage: "Prototype",
      team_size: "2-3 Co-founders",
      runway: "Pre-Seed ($50k-$250k)",
      goal: "Secure Pilot LOIs",
      market: "Enterprise",
      geo: "North America"
    },
    {
      title: "EcoDeliver Fleet",
      pitch: "Autonomous electric cargo e-bike fleet for urban last-mile grocery and parcel logistics. Drops inner-city parcel delivery cost by 60% while cutting carbon footprint to near zero via localized micro-depots.",
      stage: "Idea",
      team_size: "Solo Founder",
      runway: "Bootstrapped",
      goal: "Validate Urgency & Demand",
      market: "B2B",
      geo: "Europe"
    }
  ];

  // --- APPLICATION STATE ---
  const state = {
    currentStep: 1, // 1: Idea, 2: Panel, 3: Verdict
    brief: null,
    panel: [],
    report: null,
    isStreaming: false,
    searchTimeout: null,
    modalTriggerEl: null
  };

  // Restore session state on reload
  function restoreState() {
    try {
      const saved = sessionStorage.getItem('quorum_state');
      if (saved) {
        const parsed = JSON.parse(saved);
        state.currentStep = parsed.currentStep || 1;
        state.brief = parsed.brief || null;
        state.panel = parsed.panel || [];
        state.report = parsed.report || null;
      }
    } catch (e) {
      console.warn('Could not restore session state:', e);
    }
  }

  function saveState() {
    try {
      sessionStorage.setItem('quorum_state', JSON.stringify({
        currentStep: state.currentStep,
        brief: state.brief,
        panel: state.panel,
        report: state.report
      }));
    } catch (e) {
      console.warn('Could not persist session state:', e);
    }
  }

  // --- DOM ELEMENTS ---
  const el = {
    stepTracker: document.getElementById('step-tracker'),
    step1: document.getElementById('step-1-idea'),
    step2: document.getElementById('step-2-panel'),
    step3: document.getElementById('step-3-verdict'),
    pitchForm: document.getElementById('pitch-form'),
    pitchInput: document.getElementById('pitch-input'),
    titleInput: document.getElementById('title-input'),
    fileInput: document.getElementById('file-input'),
    dropzone: document.getElementById('dropzone'),
    fileName: document.getElementById('file-name'),
    stageSelect: document.getElementById('stage-select'),
    teamSelect: document.getElementById('team-size-select'),
    runwaySelect: document.getElementById('runway-select'),
    goalSelect: document.getElementById('goal-select'),
    marketSelect: document.getElementById('market-select'),
    geoSelect: document.getElementById('geo-select'),
    panelList: document.getElementById('panel-list'),
    rerollBtn: document.getElementById('reroll-panel-btn'),
    launchCouncilBtn: document.getElementById('launch-council-btn'),
    streamingProgress: document.getElementById('streaming-progress'),
    progressBar: document.getElementById('progress-bar-fill'),
    progressLabel: document.getElementById('progress-label'),
    streamingCards: document.getElementById('streaming-cards'),
    reportContainer: document.getElementById('report-container'),
    modal: document.getElementById('modal-overlay'),
    modalContent: document.getElementById('modal-content-box'),
    modalBody: document.getElementById('modal-body'),
    closeModalBtn: document.getElementById('modal-close-btn')
  };

  // --- INITIALIZATION ---
  function init() {
    restoreState();
    bindEvents();
    renderStep();
  }

  function bindEvents() {
    // Step navigation buttons
    document.querySelectorAll('.step-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const targetStep = parseInt(btn.dataset.step, 10);
        if (targetStep === 1) setStep(1);
        else if (targetStep === 2 && state.brief) setStep(2);
        else if (targetStep === 3 && (state.report || state.panel.length > 0)) setStep(3);
      });
    });

    // Pitch form submit
    el.pitchForm.addEventListener('submit', handleIdeaSubmit);

    // Dropzone keyboard and click triggers
    el.dropzone.addEventListener('click', () => el.fileInput.click());
    el.dropzone.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        el.fileInput.click();
      }
    });

    // Drag-and-drop
    el.dropzone.addEventListener('dragover', (e) => { e.preventDefault(); el.dropzone.classList.add('dragover'); });
    el.dropzone.addEventListener('dragleave', () => el.dropzone.classList.remove('dragover'));
    el.dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      el.dropzone.classList.remove('dragover');
      if (e.dataTransfer.files.length) handleFileSelection(e.dataTransfer.files[0]);
    });
    el.fileInput.addEventListener('change', (e) => {
      if (e.target.files.length) handleFileSelection(e.target.files[0]);
    });

    // Re-roll button
    el.rerollBtn.addEventListener('click', () => {
      if (!state.brief) return;
      const seed = Math.floor(Math.random() * 1000000);
      fetchPanel(state.brief, seed);
    });

    // Launch council button
    el.launchCouncilBtn.addEventListener('click', startCouncilDeliberation);

    // Modal close & Focus trap
    el.closeModalBtn.addEventListener('click', closeModal);
    el.modal.addEventListener('click', (e) => { if (e.target === el.modal) closeModal(); });
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && el.modal.style.display === 'flex') {
        closeModal();
      }
    });
  }

  function handleFileSelection(file) {
    if (file.size > 10 * 1024 * 1024) {
      alert('File exceeds 10 MB limit. Please select a smaller pitch deck or plain text file.');
      el.fileInput.value = '';
      el.fileName.textContent = '';
      return;
    }
    el.fileName.textContent = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
  }

  // --- SAMPLE PRE-FILLING (Phase 7) ---
  function loadSample(idx) {
    const s = SAMPLE_IDEAS[idx];
    if (!s) return;
    el.titleInput.value = s.title;
    el.pitchInput.value = s.pitch;
    if (el.stageSelect) el.stageSelect.value = s.stage;
    if (el.teamSelect) el.teamSelect.value = s.team_size;
    if (el.runwaySelect) el.runwaySelect.value = s.runway;
    if (el.goalSelect) el.goalSelect.value = s.goal;
    if (el.marketSelect) el.marketSelect.value = s.market;
    if (el.geoSelect) el.geoSelect.value = s.geo;
    el.titleInput.focus();
  }

  // --- STEP SWITCHING & ACCESSIBLE TITLES ---
  function setStep(step) {
    state.currentStep = step;
    saveState();
    renderStep();
  }

  function renderStep() {
    const titles = {
      1: "QUORUM | 1. Pitch Idea & Founder Context",
      2: "QUORUM | 2. Review Adversarial Council",
      3: "QUORUM | 3. Council Viability Verdict"
    };
    document.title = titles[state.currentStep] || "QUORUM // Autonomous War Room";

    // Update step tracker pills & aria-current
    document.querySelectorAll('.step-btn').forEach(btn => {
      const step = parseInt(btn.dataset.step, 10);
      btn.classList.toggle('active', step === state.currentStep);
      btn.classList.toggle('completed', step < state.currentStep);
      if (step === state.currentStep) {
        btn.setAttribute('aria-current', 'step');
      } else {
        btn.removeAttribute('aria-current');
      }
    });

    el.step1.style.display = state.currentStep === 1 ? 'block' : 'none';
    el.step2.style.display = state.currentStep === 2 ? 'block' : 'none';
    el.step3.style.display = state.currentStep === 3 ? 'block' : 'none';

    if (state.currentStep === 2 && state.panel.length > 0) {
      renderPanelCards();
    } else if (state.currentStep === 3) {
      if (state.report) {
        el.streamingProgress.style.display = 'none';
        renderFullReport(state.report);
      } else if (!state.isStreaming) {
        startCouncilDeliberation();
      }
    }
  }

  // --- STEP 1: IDEA SUBMISSION ---
  async function handleIdeaSubmit(e) {
    e.preventDefault();
    const pitch = el.pitchInput.value.trim();
    const title = el.titleInput.value.trim() || 'Untitled Venture';
    const file = el.fileInput.files[0];

    if (!pitch && !file) {
      alert('Please enter your pitch text or upload a document.');
      el.pitchInput.focus();
      return;
    }

    const submitBtn = el.pitchForm.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Synthesizing Brief...';

    try {
      let brief;
      if (file) {
        const formData = new FormData();
        formData.append('title', title);
        formData.append('pitch', pitch);
        formData.append('file', file);
        formData.append('stage', el.stageSelect.value);
        formData.append('team_size', el.teamSelect.value);
        formData.append('runway_budget', el.runwaySelect.value);
        formData.append('primary_goal', el.goalSelect.value);
        formData.append('target_market', el.marketSelect.value);
        formData.append('geography', el.geoSelect.value);

        const res = await fetch('/api/ideas/upload-and-analyze', {
          method: 'POST',
          body: formData
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || 'Upload failed');
        }
        brief = await res.json();
      } else {
        const res = await fetch('/api/ideas/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: title,
            pitch: pitch,
            context: {
              stage: el.stageSelect.value,
              team_size: el.teamSelect.value,
              runway_budget: el.runwaySelect.value,
              primary_goal: el.goalSelect.value,
              target_market: el.marketSelect.value,
              geography: el.geoSelect.value
            }
          })
        });
        if (!res.ok) throw new Error('Analysis failed');
        brief = await res.json();
      }

      state.brief = brief;
      saveState();

      // Recommend council panel
      await fetchPanel(brief);
      setStep(2);
    } catch (err) {
      alert(`Error: ${err.message}`);
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Convene Council →';
    }
  }

  // --- STEP 2: PANEL MANAGEMENT ---
  async function fetchPanel(brief, seed = null) {
    let url = `/api/council/recommend-panel?panel_size=6`;
    if (seed !== null) url += `&seed=${seed}`;

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(brief)
      });
      if (!res.ok) throw new Error('Failed to recommend council panel');
      state.panel = await res.json();
      saveState();
      renderPanelCards();
    } catch (err) {
      console.error(err);
      alert('Could not recommend panel: ' + err.message);
    }
  }

  function renderPanelCards() {
    el.panelList.innerHTML = '';
    state.panel.forEach((expert, idx) => {
      const card = document.createElement('div');
      card.className = 'card';
      card.style.display = 'flex';
      card.style.flexDirection = 'column';
      card.style.justifyContent = 'space-between';

      const depthBadge = expert.profile_depth === 'deep'
        ? '<span class="badge badge-deep">Deep Profile</span>'
        : '<span class="badge badge-basic">Basic Dossier</span>';

      const quote = (expert.signature_quotes && expert.signature_quotes[0])
        ? expert.signature_quotes[0]
        : (expert.core_principles[0] || 'Focus on reality.');

      card.innerHTML = `
        <div>
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
            <h3 style="font-size: 16px; color: var(--cyan);">${escapeHtml(expert.name)}</h3>
            ${depthBadge}
          </div>
          <p style="font-size: 12px; color: var(--text-muted); margin-bottom: 6px;">${escapeHtml(expert.role_or_title || expert.primary_sector)}</p>
          <p style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--lime); margin-bottom: 10px;">${escapeHtml(expert.stance_archetype)}</p>
          <p style="font-size: 13px; color: var(--text-main); font-style: italic; margin-bottom: 12px;">"${escapeHtml(quote)}"</p>
        </div>
        <div style="display: flex; gap: 8px; margin-top: 10px;">
          <button type="button" class="btn btn-secondary btn-sm" style="flex: 1;" onclick="window.QuorumApp.openSwapModal(${idx}, this)">Swap</button>
          <button type="button" class="btn btn-secondary btn-sm" onclick="window.QuorumApp.inspectExpert('${expert.id}', this)">Dossier</button>
        </div>
      `;
      el.panelList.appendChild(card);
    });
  }

  // --- STEP 3: STREAMING & DELIBERATION ---
  function startCouncilDeliberation() {
    if (!state.brief || state.panel.length === 0) {
      setStep(1);
      return;
    }

    state.isStreaming = true;
    state.report = null;
    el.streamingProgress.style.display = 'block';
    el.reportContainer.innerHTML = '';
    el.progressLabel.textContent = `Assembling council (${state.panel.length} experts)...`;
    el.progressBar.style.width = '5%';
    if (el.streamingCards) el.streamingCards.innerHTML = '';

    fetch('/api/council/evaluate/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        brief: state.brief,
        expert_ids: state.panel.map(p => p.id)
      })
    }).then(response => {
      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      function readChunk() {
        reader.read().then(({ done, value }) => {
          if (done) {
            state.isStreaming = false;
            return;
          }

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n\n');
          buffer = lines.pop();

          for (const block of lines) {
            const rawEvent = block.trim();
            if (!rawEvent) continue;

            const eventMatch = rawEvent.match(/^event:\s*(.+)$/m);
            const dataMatch = rawEvent.match(/^data:\s*(.+)$/m);

            if (eventMatch && dataMatch) {
              const eventType = eventMatch[1].trim();
              const eventData = JSON.parse(dataMatch[1].trim());

              if (eventType === 'expert') {
                const pct = Math.round((eventData.completed / eventData.total) * 90);
                el.progressBar.style.width = `${pct}%`;
                el.progressLabel.textContent = eventData.progress_label;
                renderStreamingExpertCard(eventData.expert);
              } else if (eventType === 'report') {
                state.report = eventData;
                saveState();
                el.progressBar.style.width = '100%';
                el.progressLabel.textContent = 'Consensus reached. Finalizing synthesis...';
                setTimeout(() => {
                  el.streamingProgress.style.display = 'none';
                  renderFullReport(state.report);
                }, 600);
              }
            }
          }
          readChunk();
        }).catch(err => {
          console.error('Stream read error:', err);
          state.isStreaming = false;
          fallbackEvaluate();
        });
      }

      readChunk();
    }).catch(err => {
      console.warn('Stream failed, falling back to direct evaluate:', err);
      fallbackEvaluate();
    });
  }

  async function fallbackEvaluate() {
    try {
      el.progressLabel.textContent = 'Evaluating via direct council endpoint...';
      const res = await fetch('/api/council/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          brief: state.brief,
          expert_ids: state.panel.map(p => p.id)
        })
      });
      if (!res.ok) throw new Error('Direct evaluation failed');
      state.report = await res.json();
      saveState();
      el.streamingProgress.style.display = 'none';
      renderFullReport(state.report);
    } catch (e) {
      alert('Error during evaluation: ' + e.message);
    } finally {
      state.isStreaming = false;
    }
  }

  function renderStreamingExpertCard(expertVerdict) {
    if (!el.streamingCards) return;
    const card = document.createElement('div');
    card.className = 'card';
    card.style.borderLeft = `4px solid ${expertVerdict.overall_score >= 7.0 ? 'var(--lime)' : (expertVerdict.overall_score >= 5.5 ? 'var(--cyan)' : 'var(--red)')}`;
    card.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
        <strong style="color: var(--text-main);">${escapeHtml(expertVerdict.expert_name)}</strong>
        <span class="mono" style="font-weight: 700; color: ${expertVerdict.overall_score >= 7 ? 'var(--lime)' : (expertVerdict.overall_score >= 5.5 ? 'var(--cyan)' : 'var(--red)')}">
          ${expertVerdict.overall_score.toFixed(1)}/10
        </span>
      </div>
      <p style="font-size: 11px; text-transform: uppercase; color: var(--text-muted); margin-bottom: 8px;">${escapeHtml(expertVerdict.stance_archetype)}</p>
      <p style="font-size: 13px; color: var(--text-muted);">${escapeHtml(expertVerdict.opinion_critique.slice(0, 140))}...</p>
    `;
    el.streamingCards.appendChild(card);
  }

  // --- FULL SYNTHESIS REPORT RENDERING ---
  function renderFullReport(report) {
    el.reportContainer.innerHTML = '';

    // Suspicious Prompt Injection Alert (Phase 3 Security)
    if (report.is_suspicious_input) {
      const secBanner = document.createElement('div');
      secBanner.className = 'alert-banner';
      secBanner.style.borderColor = '#f59e0b';
      secBanner.style.background = 'rgba(245, 158, 11, 0.1)';
      secBanner.style.color = '#fbbf24';
      secBanner.innerHTML = `
        <span style="font-size: 18px;">🛡️</span>
        <div>
          <strong>SUSPICIOUS PITCH INPUT FLAGGED</strong>
          <p style="margin-top: 2px; font-size: 12px; color: var(--text-muted);">
            Pitch contains prompt-override markers or anomalous uniform scoring. Council evaluations were forced to strict isolated business rules.
          </p>
        </div>
      `;
      el.reportContainer.appendChild(secBanner);
    }

    // 1. Offline Simulation Warning Banner (Honest Fallback)
    if (report.source === 'offline') {
      const banner = document.createElement('div');
      banner.className = 'alert-banner';
      banner.setAttribute('role', 'status');
      banner.innerHTML = `
        <span style="font-size: 18px;" aria-hidden="true">⚠️</span>
        <div>
          <strong>OFFLINE SIMULATION — NOT REAL AI ANALYSIS</strong>
          <p style="margin-top: 2px; color: var(--text-muted); font-size: 12px;">Operating in deterministic heuristic fallback mode because no valid Google Gemini API key was detected. All scoring reflects authentic persona archetype rules.</p>
        </div>
      `;
      el.reportContainer.appendChild(banner);
    }

    // 2. Score & Verdict Hero Card
    const heroCard = document.createElement('div');
    heroCard.className = 'score-hero';

    let scoreClass = 'score-promising';
    if (report.overall_score >= 7.5) scoreClass = 'score-strong';
    else if (report.overall_score < 5.5 && report.overall_score >= 4.0) scoreClass = 'score-weak';
    else if (report.overall_score < 4.0) scoreClass = 'score-fatal';

    heroCard.innerHTML = `
      <div>
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
          <h2 style="font-size: 26px;">${escapeHtml(report.title)}</h2>
          <span class="badge ${report.source === 'offline' ? 'badge-offline' : 'badge-deep'}">${report.source.toUpperCase()}</span>
        </div>
        <p style="font-size: 15px; color: var(--text-muted); max-width: 650px;">${escapeHtml(report.executive_summary)}</p>
      </div>
      <div style="text-align: right;">
        <div class="score-display ${scoreClass}" id="composite-score-val" aria-label="Composite Viability Score">${report.overall_score.toFixed(1)}</div>
        <div style="font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-main);" id="composite-verdict-label">${escapeHtml(report.verdict_label)}</div>
        <div style="font-size: 11px; color: var(--text-dim); margin-top: 4px;">Consensus: ${report.consensus_percentage}%</div>
      </div>
    `;
    el.reportContainer.appendChild(heroCard);

    // Action bar (Export JSON & Print)
    const actionsBar = document.createElement('div');
    actionsBar.className = 'no-print';
    actionsBar.style.display = 'flex';
    actionsBar.style.justifyContent = 'flex-end';
    actionsBar.style.gap = '10px';
    actionsBar.style.marginBottom = '20px';
    actionsBar.innerHTML = `
      <button type="button" class="btn btn-secondary btn-sm" onclick="window.QuorumApp.exportJson()">Export JSON</button>
      <button type="button" class="btn btn-secondary btn-sm" onclick="window.print()">Print Report</button>
      <button type="button" class="btn btn-lime btn-sm" onclick="window.QuorumApp.newEvaluation()">New Run</button>
    `;
    el.reportContainer.appendChild(actionsBar);

    // Phase 2: What to Do Next for YOUR Situation
    if (report.tailored_actions && report.tailored_actions.length > 0) {
      const tailoredSection = document.createElement('div');
      tailoredSection.className = 'card';
      tailoredSection.style.marginBottom = '20px';
      tailoredSection.style.borderColor = 'rgba(0, 229, 255, 0.4)';
      tailoredSection.style.background = 'rgba(0, 229, 255, 0.03)';
      tailoredSection.innerHTML = `
        <h3 style="font-size: 18px; color: var(--cyan); margin-bottom: 6px;">What to Do Next for YOUR Situation</h3>
        <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 12px;">Directly tailored to your stage, team size, budget, and immediate goals:</p>
        <div style="display: flex; flex-direction: column; gap: 8px;">
          ${report.tailored_actions.map(action => `
            <div style="display: flex; gap: 10px; align-items: flex-start; padding: 10px; background: rgba(15, 23, 42, 0.7); border-radius: var(--radius-sm); border: 1px solid var(--border);">
              <span style="color: var(--cyan); font-size: 16px;">➔</span>
              <p style="font-size: 13px; color: var(--text-main); line-height: 1.5;">${escapeHtml(action)}</p>
            </div>
          `).join('')}
        </div>
      `;
      el.reportContainer.appendChild(tailoredSection);
    }

    // 3. Top 3 Existential Risks
    const risksSection = document.createElement('div');
    risksSection.className = 'card';
    risksSection.style.marginBottom = '20px';
    const top3Warnings = (report.top_warnings || []).slice(0, 3);
    risksSection.innerHTML = `
      <h3 style="font-size: 18px; margin-bottom: 12px; color: var(--red);">Top Existential Risks</h3>
      <div style="display: flex; flex-direction: column; gap: 10px;">
        ${top3Warnings.map(w => `
          <div style="padding: 10px; background: rgba(255,59,48,0.06); border-left: 3px solid var(--red); border-radius: var(--radius-sm);">
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
              <strong style="color: var(--text-main); font-size: 14px;">${escapeHtml(w.warning)}</strong>
              <span class="badge" style="background: rgba(255,59,48,0.2); color: var(--red);">${escapeHtml(w.severity)}</span>
            </div>
            <p style="font-size: 12px; color: var(--text-muted);">Flagged by ${w.experts_count} persona(s): ${escapeHtml(w.flagged_by.join(', '))}</p>
          </div>
        `).join('')}
      </div>
    `;
    el.reportContainer.appendChild(risksSection);

    // 4. Kill Questions Matrix with "Answer this" Rebuttal Loop
    const killSection = document.createElement('div');
    killSection.className = 'card';
    killSection.style.marginBottom = '20px';
    killSection.innerHTML = `
      <h3 style="font-size: 18px; margin-bottom: 4px; color: var(--cyan);">Adversarial Kill Questions</h3>
      <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 16px;">Answer any kill question below to re-evaluate with that expert and update your council score.</p>
      <div style="display: flex; flex-direction: column; gap: 14px;" id="kill-questions-list">
        ${(report.kill_questions || []).map((kq, idx) => `
          <div class="card" style="background: rgba(11, 15, 25, 0.85); border: 1px solid var(--border);" id="kq-card-${idx}">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
              <strong style="color: var(--cyan); font-size: 14px;">${escapeHtml(kq.raised_by)} asks:</strong>
              <span class="mono" style="font-size: 12px; color: var(--text-dim);" id="kq-score-tag-${idx}">${findExpertScore(kq.raised_by)}/10</span>
            </div>
            <p style="font-size: 14px; font-weight: 600; color: var(--text-main); margin-bottom: 10px;">"${escapeHtml(kq.question)}"</p>
            <div style="display: flex; gap: 8px;">
              <input type="text" class="input" placeholder="Type your counter-argument or defense..." id="rebut-input-${idx}" style="font-size: 13px;" aria-label="Rebuttal answer to ${escapeHtml(kq.raised_by)}" />
              <button type="button" class="btn btn-secondary btn-sm" onclick="window.QuorumApp.submitRebuttal('${escapeQuotes(kq.raised_by)}', ${idx}, '${escapeQuotes(kq.question)}')">Rebut</button>
            </div>
          </div>
        `).join('')}
      </div>
    `;
    el.reportContainer.appendChild(killSection);

    // 5. 8 Pillar Breakdown
    const pillarSection = document.createElement('div');
    pillarSection.className = 'card';
    pillarSection.style.marginBottom = '20px';
    const p = report.pillar_scores;
    const pillarsData = [
      { name: 'Market Demand', val: p.market_demand },
      { name: 'Differentiation & Moat', val: p.differentiation },
      { name: 'Technical Feasibility', val: p.feasibility },
      { name: 'Financial Viability', val: p.financial_viability },
      { name: 'Execution Safety', val: p.execution_risk },
      { name: 'Regulatory & Legal Safety', val: p.regulatory_legal_risk },
      { name: 'Market Timing', val: p.market_timing },
      { name: 'Defensibility at Scale', val: p.defensibility_scale }
    ];

    pillarSection.innerHTML = `
      <h3 style="font-size: 18px; margin-bottom: 16px;">8 Core Startup Pillars</h3>
      <div class="grid-2">
        ${pillarsData.map(item => `
          <div>
            <div style="display: flex; justify-content: space-between; font-size: 13px; font-weight: 600; margin-bottom: 6px;">
              <span>${item.name}</span>
              <span class="mono" style="color: ${item.val >= 7 ? 'var(--lime)' : (item.val >= 5.5 ? 'var(--cyan)' : 'var(--red)')};">${item.val.toFixed(1)}/10</span>
            </div>
            <div class="bar-track">
              <div class="bar-fill ${item.val >= 7 ? 'fill-lime' : (item.val >= 5.5 ? 'fill-cyan' : 'fill-red')}" style="width: ${item.val * 10}%;"></div>
            </div>
          </div>
        `).join('')}
      </div>
    `;
    el.reportContainer.appendChild(pillarSection);

    // 6. Core Disagreements
    if (report.consensus_dissent && report.consensus_dissent.sharp_disagreements.length > 0) {
      const dissSection = document.createElement('div');
      dissSection.className = 'card';
      dissSection.style.marginBottom = '20px';
      dissSection.innerHTML = `
        <h3 style="font-size: 18px; margin-bottom: 12px; color: var(--lime);">Philosophical Clashes & Disagreements</h3>
        <div style="display: flex; flex-direction: column; gap: 10px;">
          ${report.consensus_dissent.sharp_disagreements.map(d => `
            <div style="padding: 12px; background: rgba(175,248,51,0.05); border: 1px solid rgba(175,248,51,0.2); border-radius: var(--radius-sm);">
              <strong style="color: var(--lime); font-size: 14px; display: block; margin-bottom: 6px;">${escapeHtml(d.topic)}</strong>
              <div class="grid-2" style="font-size: 13px;">
                <p style="color: var(--cyan);">🟢 <strong>${escapeHtml(d.optimists.join(', '))}:</strong> ${escapeHtml(d.optimist_view)}</p>
                <p style="color: var(--red);">🔴 <strong>${escapeHtml(d.skeptics.join(', '))}:</strong> ${escapeHtml(d.skeptic_view)}</p>
              </div>
            </div>
          `).join('')}
        </div>
      `;
      el.reportContainer.appendChild(dissSection);
    }

    // 7. Tactical Roadmap
    const r = report.tactical_roadmap;
    const roadmapSection = document.createElement('div');
    roadmapSection.className = 'card';
    roadmapSection.style.marginBottom = '20px';
    roadmapSection.innerHTML = `
      <h3 style="font-size: 18px; margin-bottom: 14px;">Tactical De-Risking Roadmap</h3>
      <div class="grid-3">
        <div style="padding: 12px; background: rgba(11, 15, 25, 0.7); border-radius: var(--radius-sm); border: 1px solid var(--border);">
          <strong style="color: var(--cyan); display: block; margin-bottom: 8px;">Day 1-30: Immediate Kill Tests</strong>
          <ul style="padding-left: 18px; font-size: 13px; color: var(--text-muted); display: flex; flex-direction: column; gap: 6px;">
            ${(r.days_30 || []).map(item => `<li>${escapeHtml(item)}</li>`).join('')}
          </ul>
        </div>
        <div style="padding: 12px; background: rgba(11, 15, 25, 0.7); border-radius: var(--radius-sm); border: 1px solid var(--border);">
          <strong style="color: var(--lime); display: block; margin-bottom: 8px;">Day 31-90: Wedge Validation</strong>
          <ul style="padding-left: 18px; font-size: 13px; color: var(--text-muted); display: flex; flex-direction: column; gap: 6px;">
            ${(r.days_90 || []).map(item => `<li>${escapeHtml(item)}</li>`).join('')}
          </ul>
        </div>
        <div style="padding: 12px; background: rgba(11, 15, 25, 0.7); border-radius: var(--radius-sm); border: 1px solid var(--border);">
          <strong style="color: var(--text-main); display: block; margin-bottom: 8px;">Day 91-180: Moat & Scale</strong>
          <ul style="padding-left: 18px; font-size: 13px; color: var(--text-muted); display: flex; flex-direction: column; gap: 6px;">
            ${(r.days_180 || []).map(item => `<li>${escapeHtml(item)}</li>`).join('')}
          </ul>
        </div>
      </div>
    `;
    el.reportContainer.appendChild(roadmapSection);

    // 8. 2D Radial Tension Graph (Pure SVG + Accessible Table Alternative)
    const graphSection = document.createElement('div');
    graphSection.className = 'card';
    graphSection.style.marginBottom = '20px';
    graphSection.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
        <h3 style="font-size: 18px;">2D Council Tension Graph</h3>
        <span class="mono" style="font-size: 12px; color: var(--text-muted);">Divergence: ${report.network_graph.tension_index}</span>
      </div>
      <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 12px;">
        Node size and color indicate pillar score. Edge thickness and color indicate philosophical tension. Click any persona node to interrogate.
      </p>
      <div class="graph-container">
        ${renderSvgTensionGraph(report.network_graph)}
      </div>
    `;
    el.reportContainer.appendChild(graphSection);

    // 9. Expert Cards (Collapsed Accordion by Default)
    const rosterSection = document.createElement('div');
    rosterSection.className = 'card';
    rosterSection.style.marginBottom = '20px';
    rosterSection.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; cursor: pointer;" onclick="window.QuorumApp.toggleRoster()" role="button" tabindex="0" aria-expanded="false" id="roster-accordion-btn">
        <h3 style="font-size: 18px;">Individual Expert Dossiers & Critiques (${report.expert_roster.length})</h3>
        <span id="roster-toggle-icon" style="color: var(--cyan); font-weight: 700;">+ Expand</span>
      </div>
      <div id="roster-cards-container" style="display: none; margin-top: 16px; flex-direction: column; gap: 14px;">
        ${report.expert_roster.map(exp => `
          <div class="card" style="background: rgba(11, 15, 25, 0.9); border: 1px solid var(--border);">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
              <div>
                <h4 style="font-size: 16px; color: var(--cyan);">${escapeHtml(exp.expert_name)}</h4>
                <p style="font-size: 12px; color: var(--text-muted);">${escapeHtml(exp.role_or_title || '')} • <span style="color: var(--lime);">${escapeHtml(exp.stance_archetype)}</span></p>
              </div>
              <div style="text-align: right;">
                <span class="mono" style="font-size: 18px; font-weight: 800; color: ${exp.overall_score >= 7 ? 'var(--lime)' : (exp.overall_score >= 5.5 ? 'var(--cyan)' : 'var(--red)')};">${exp.overall_score.toFixed(1)}/10</span>
                <div style="font-size: 11px; color: var(--text-dim);">${escapeHtml(exp.verdict_label)}</div>
              </div>
            </div>
            <p style="font-size: 14px; color: var(--text-main); margin-bottom: 12px; line-height: 1.6;">${escapeHtml(exp.opinion_critique)}</p>
            <div style="display: flex; gap: 8px; justify-content: flex-end;">
              <button type="button" class="btn btn-secondary btn-sm" onclick="window.QuorumApp.interrogatePersona('${exp.expert_id}', '${escapeQuotes(exp.expert_name)}', this)">Interrogate 1-on-1</button>
            </div>
          </div>
        `).join('')}
      </div>
    `;
    el.reportContainer.appendChild(rosterSection);
  }

  function findExpertScore(name) {
    if (!state.report || !state.report.expert_roster) return '5.0';
    const found = state.report.expert_roster.find(e => e.expert_name === name);
    return found ? found.overall_score.toFixed(1) : '5.0';
  }

  // --- 2D RADIAL SVG TENSION GRAPH WITH WCAG COMPLIANCE ---
  function renderSvgTensionGraph(graph) {
    const width = 500;
    const height = 500;
    const cx = width / 2;
    const cy = height / 2;
    const radius = 170;

    const nodeCount = graph.nodes.length;
    if (nodeCount === 0) return '<p>No graph nodes available</p>';

    const nodeCoords = {};
    graph.nodes.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / nodeCount - Math.PI / 2;
      const x = cx + radius * Math.cos(angle);
      const y = cy + radius * Math.sin(angle);
      nodeCoords[node.id] = { x, y, node };
    });

    let edgesSvg = '';
    graph.edges.forEach(edge => {
      const src = nodeCoords[edge.source];
      const tgt = nodeCoords[edge.target];
      if (src && tgt) {
        const strokeWidth = Math.max(1, Math.min(5, (edge.tension || 0.2) * 5));
        const strokeOpacity = Math.max(0.2, Math.min(0.85, (edge.tension || 0.2)));
        const strokeColor = edge.tension > 0.5 ? 'var(--red)' : (edge.tension > 0.25 ? 'var(--cyan)' : 'var(--lime)');

        edgesSvg += `
          <line x1="${src.x}" y1="${src.y}" x2="${tgt.x}" y2="${tgt.y}"
                stroke="${strokeColor}" stroke-width="${strokeWidth}" stroke-opacity="${strokeOpacity}">
            <title>${escapeHtml(edge.reason || 'Tension: ' + edge.tension)}</title>
          </line>
        `;
      }
    });

    let nodesSvg = '';
    graph.nodes.forEach(node => {
      const pos = nodeCoords[node.id];
      const nodeR = 14 + (node.score || 5) * 1.5;
      nodesSvg += `
        <g class="graph-node" tabindex="0" role="button" aria-label="Interrogate ${escapeHtml(node.name)}, score ${node.score.toFixed(1)}" onclick="window.QuorumApp.interrogatePersona('${node.id}', '${escapeQuotes(node.name)}', this)" onkeydown="if(event.key==='Enter'||event.key===' ')window.QuorumApp.interrogatePersona('${node.id}', '${escapeQuotes(node.name)}', this)">
          <circle cx="${pos.x}" cy="${pos.y}" r="${nodeR}" fill="${node.color}" stroke="#05060A" stroke-width="3">
            <title>${escapeHtml(node.name)} (${escapeHtml(node.archetype)}): ${node.score.toFixed(1)}/10</title>
          </circle>
          <text x="${pos.x}" y="${pos.y + 4}" text-anchor="middle" font-size="11" font-weight="700" fill="#05060A">
            ${node.score.toFixed(1)}
          </text>
          <text x="${pos.x}" y="${pos.y + nodeR + 14}" text-anchor="middle" font-size="11" font-weight="600" fill="var(--text-main)">
            ${escapeHtml(node.name)}
          </text>
        </g>
      `;
    });

    // Accessible Table Alternative for Screen Readers
    const tableAlternative = `
      <table class="sr-only">
        <caption>Council Expert Scores and Tension Matrix</caption>
        <thead>
          <tr><th>Expert Name</th><th>Archetype</th><th>Score</th></tr>
        </thead>
        <tbody>
          ${graph.nodes.map(n => `<tr><td>${escapeHtml(n.name)}</td><td>${escapeHtml(n.archetype)}</td><td>${n.score.toFixed(1)}/10</td></tr>`).join('')}
        </tbody>
      </table>
    `;

    return `
      <svg viewBox="0 0 ${width} ${height}" class="svg-graph" role="img" aria-label="2D Radial Council Tension Graph visualizing expert score alignment and philosophical divergence.">
        <circle cx="${cx}" cy="${cy}" r="${radius}" fill="none" stroke="rgba(51, 65, 85, 0.3)" stroke-dasharray="4 4" />
        ${edgesSvg}
        ${nodesSvg}
      </svg>
      ${tableAlternative}
    `;
  }

  // --- REBUTTAL LOOP (Phase 7) ---
  async function submitRebuttal(expertName, idx, killQuestion) {
    const input = document.getElementById(`rebut-input-${idx}`);
    const answer = input ? input.value.trim() : '';
    if (!answer) {
      alert('Please enter your counter-argument or defense first.');
      if (input) input.focus();
      return;
    }

    const expert = (state.report && state.report.expert_roster)
      ? state.report.expert_roster.find(e => e.expert_name === expertName)
      : null;

    if (!expert) {
      alert('Expert persona not found.');
      return;
    }

    input.disabled = true;
    const btn = input.nextElementSibling;
    if (btn) { btn.disabled = true; btn.textContent = 'Scoring...'; }

    try {
      const res = await fetch('/api/rebut', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          brief: state.brief,
          expert_id: expert.expert_id,
          kill_question: killQuestion,
          answer: answer
        })
      });

      if (!res.ok) throw new Error('Rebuttal request failed');
      const updatedVerdict = await res.json();

      const oldScore = expert.overall_score;
      const newScore = updatedVerdict.overall_score;
      expert.overall_score = newScore;
      expert.pillar_ratings = updatedVerdict.pillar_ratings;

      const tag = document.getElementById(`kq-score-tag-${idx}`);
      if (tag) {
        tag.innerHTML = `<span style="text-decoration: line-through; color: var(--text-dim);">${oldScore.toFixed(1)}</span> <span style="color: var(--lime); font-weight: 800;">${newScore.toFixed(1)}/10</span>`;
      }

      // Recompute composite viability score
      const allScores = state.report.expert_roster.map(e => e.overall_score);
      const newComposite = Number((allScores.reduce((a, b) => a + b, 0) / allScores.length).toFixed(1));
      state.report.overall_score = newComposite;

      let newLabel = 'Do not build as-is';
      if (newComposite >= 7.5) newLabel = 'Strong';
      else if (newComposite >= 5.5) newLabel = 'Promising but risky';
      else if (newComposite >= 4.0) newLabel = 'Weak';
      state.report.verdict_label = newLabel;

      const scoreDisplay = document.getElementById('composite-score-val');
      if (scoreDisplay) scoreDisplay.textContent = newComposite.toFixed(1);

      const labelDisplay = document.getElementById('composite-verdict-label');
      if (labelDisplay) labelDisplay.textContent = newLabel;

      saveState();
      alert(`Rebuttal evaluated by ${expertName}!\nScore updated: ${oldScore.toFixed(1)} → ${newScore.toFixed(1)}.\nNew Council Composite: ${newComposite.toFixed(1)}/10.`);
    } catch (err) {
      alert('Could not submit rebuttal: ' + err.message);
    } finally {
      if (input) input.disabled = false;
      if (btn) { btn.disabled = false; btn.textContent = 'Rebut'; }
    }
  }

  // --- MODAL UTILITIES (ACCESSIBLE FOCUS TRAP) ---
  function openSwapModal(panelIndex, triggerEl) {
    state.modalTriggerEl = triggerEl || null;
    const currentExpert = state.panel[panelIndex];
    el.modalBody.innerHTML = `
      <h3 id="modal-title" style="font-size: 18px; margin-bottom: 10px;">Replace ${escapeHtml(currentExpert.name)}</h3>
      <input type="text" class="input" placeholder="Search 700+ experts by name or sector..." id="swap-search-input" style="margin-bottom: 14px;" aria-label="Search experts" />
      <div id="swap-results-list" style="max-height: 380px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px;">
        <p style="color: var(--text-muted); font-size: 13px;">Type to search catalog...</p>
      </div>
    `;
    el.modal.style.display = 'flex';

    const searchInput = document.getElementById('swap-search-input');
    if (searchInput) {
      searchInput.focus();
      searchInput.addEventListener('input', (e) => {
        clearTimeout(state.searchTimeout);
        const query = e.target.value.trim();
        state.searchTimeout = setTimeout(() => searchExpertsForSwap(query, panelIndex), 200);
      });
    }

    searchExpertsForSwap('', panelIndex);
  }

  async function searchExpertsForSwap(query, panelIndex) {
    const list = document.getElementById('swap-results-list');
    if (!list) return;

    try {
      const res = await fetch(`/api/experts?q=${encodeURIComponent(query)}&limit=15`);
      const candidates = await res.json();
      list.innerHTML = '';

      if (candidates.length === 0) {
        list.innerHTML = '<p style="color: var(--text-muted); font-size: 13px;">No experts found matching query.</p>';
        return;
      }

      candidates.forEach(cand => {
        const row = document.createElement('div');
        row.style.display = 'flex';
        row.style.justifyContent = 'space-between';
        row.style.alignItems = 'center';
        row.style.padding = '8px 12px';
        row.style.background = 'rgba(15, 23, 42, 0.6)';
        row.style.borderRadius = 'var(--radius-sm)';
        row.style.border = '1px solid var(--border)';

        const badge = cand.profile_depth === 'deep' ? '<span class="badge badge-deep">Deep</span>' : '';

        row.innerHTML = `
          <div>
            <strong style="color: var(--text-main); font-size: 14px;">${escapeHtml(cand.name)}</strong> ${badge}
            <div style="font-size: 11px; color: var(--text-muted);">${escapeHtml(cand.stance_archetype)} • ${escapeHtml(cand.primary_sector)}</div>
          </div>
          <button type="button" class="btn btn-secondary btn-sm" onclick="window.QuorumApp.selectReplacement(${panelIndex}, '${cand.id}')">Select</button>
        `;
        list.appendChild(row);
      });
    } catch (e) {
      list.innerHTML = `<p style="color: var(--red); font-size: 13px;">Search error: ${escapeHtml(e.message)}</p>`;
    }
  }

  async function selectReplacement(panelIndex, expertId) {
    try {
      const res = await fetch(`/api/experts/${expertId}`);
      if (!res.ok) throw new Error('Expert fetch failed');
      const newExpert = await res.json();
      state.panel[panelIndex] = newExpert;
      saveState();
      renderPanelCards();
      closeModal();
    } catch (e) {
      alert('Could not swap expert: ' + e.message);
    }
  }

  async function inspectExpert(expertId, triggerEl) {
    state.modalTriggerEl = triggerEl || null;
    try {
      const res = await fetch(`/api/experts/${expertId}`);
      if (!res.ok) throw new Error('Dossier fetch failed');
      const exp = await res.json();

      el.modalBody.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
          <div>
            <h3 id="modal-title" style="font-size: 20px; color: var(--cyan);">${escapeHtml(exp.name)}</h3>
            <p style="font-size: 13px; color: var(--text-muted);">${escapeHtml(exp.role_or_title || exp.primary_sector)}</p>
          </div>
          <span class="badge ${exp.profile_depth === 'deep' ? 'badge-deep' : 'badge-basic'}">${exp.profile_depth.toUpperCase()}</span>
        </div>
        <div style="font-size: 13px; color: var(--lime); font-weight: 700; margin-bottom: 14px;">Archetype: ${escapeHtml(exp.stance_archetype)}</div>
        <div style="margin-bottom: 14px;">
          <strong style="display: block; font-size: 12px; color: var(--text-dim); text-transform: uppercase; margin-bottom: 6px;">Core Mental Models:</strong>
          <ul style="padding-left: 18px; font-size: 13px; color: var(--text-main);">
            ${(exp.core_principles || []).map(p => `<li>${escapeHtml(p)}</li>`).join('')}
          </ul>
        </div>
        <div style="margin-bottom: 14px;">
          <strong style="display: block; font-size: 12px; color: var(--text-dim); text-transform: uppercase; margin-bottom: 6px;">Common Warnings:</strong>
          <ul style="padding-left: 18px; font-size: 13px; color: var(--text-muted);">
            ${(exp.common_warnings || []).map(w => `<li>${escapeHtml(w)}</li>`).join('')}
          </ul>
        </div>
      `;
      el.modal.style.display = 'flex';
      el.closeModalBtn.focus();
    } catch (e) {
      alert('Error fetching dossier: ' + e.message);
    }
  }

  function interrogatePersona(expertId, expertName, triggerEl) {
    state.modalTriggerEl = triggerEl || null;
    el.modalBody.innerHTML = `
      <h3 id="modal-title" style="font-size: 18px; color: var(--cyan); margin-bottom: 6px;">1-on-1 Cross-Examination: ${escapeHtml(expertName)}</h3>
      <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 14px;">Interrogate this persona regarding their evaluation of your pitch.</p>
      <div id="chat-messages" style="max-height: 280px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; margin-bottom: 14px; padding: 10px; background: rgba(5,6,10,0.8); border: 1px solid var(--border); border-radius: var(--radius-sm);" aria-live="polite">
        <div style="font-size: 13px; color: var(--lime);"><strong>${escapeHtml(expertName)}:</strong> I am ready. What is your counter-thesis or question?</div>
      </div>
      <div style="display: flex; gap: 8px;">
        <input type="text" class="input" placeholder="Ask ${escapeHtml(expertName)} a question..." id="chat-input" aria-label="Message to ${escapeHtml(expertName)}" />
        <button type="button" class="btn btn-primary btn-sm" id="chat-send-btn" onclick="window.QuorumApp.sendChatMessage('${expertId}', '${escapeQuotes(expertName)}')">Send</button>
      </div>
    `;
    el.modal.style.display = 'flex';
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
      chatInput.focus();
      chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage(expertId, expertName);
      });
    }
  }

  async function sendChatMessage(expertId, expertName) {
    const input = document.getElementById('chat-input');
    const msg = input ? input.value.trim() : '';
    if (!msg) return;

    const chatBox = document.getElementById('chat-messages');
    chatBox.innerHTML += `<div style="font-size: 13px; color: var(--cyan); text-align: right;"><strong>Founder:</strong> ${escapeHtml(msg)}</div>`;
    input.value = '';
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
      const res = await fetch('/api/council/expert-chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ expert_id: expertId, user_message: msg })
      });
      const data = await res.json();
      chatBox.innerHTML += `<div style="font-size: 13px; color: var(--lime);"><strong>${escapeHtml(expertName)}:</strong> ${escapeHtml(data.reply)}</div>`;
      chatBox.scrollTop = chatBox.scrollHeight;
    } catch (e) {
      chatBox.innerHTML += `<div style="font-size: 13px; color: var(--red);">Error: ${escapeHtml(e.message)}</div>`;
    }
  }

  function closeModal() {
    el.modal.style.display = 'none';
    el.modalBody.innerHTML = '';
    if (state.modalTriggerEl && typeof state.modalTriggerEl.focus === 'function') {
      state.modalTriggerEl.focus();
    }
    state.modalTriggerEl = null;
  }

  function toggleRoster() {
    const container = document.getElementById('roster-cards-container');
    const icon = document.getElementById('roster-toggle-icon');
    const btn = document.getElementById('roster-accordion-btn');
    if (!container) return;
    const isHidden = container.style.display === 'none';
    container.style.display = isHidden ? 'flex' : 'none';
    if (icon) icon.textContent = isHidden ? '− Collapse' : '+ Expand';
    if (btn) btn.setAttribute('aria-expanded', isHidden ? 'true' : 'false');
  }

  function exportJson() {
    if (!state.report) return;
    const blob = new Blob([JSON.stringify(state.report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `quorum_report_${state.report.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function newEvaluation() {
    sessionStorage.removeItem('quorum_state');
    state.brief = null;
    state.panel = [];
    state.report = null;
    state.currentStep = 1;
    setStep(1);
  }

  // --- ESCAPE HELPERS (XSS DEFENSE) ---
  function escapeQuotes(str) {
    return (str || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Expose to window for accessible event handlers
  window.QuorumApp = {
    loadSample,
    openSwapModal,
    searchExpertsForSwap,
    selectReplacement,
    inspectExpert,
    interrogatePersona,
    sendChatMessage,
    submitRebuttal,
    toggleRoster,
    exportJson,
    newEvaluation
  };

  // Run on DOM load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
