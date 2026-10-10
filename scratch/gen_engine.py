# -*- coding: utf-8 -*-
"""
JavaScript Deliberation Engine Module for case-room.html
Implements exact state machine, routing animations, seating order,
and UI synchronization as specified in case-room-bugfix phases 1-6
and agent-animation-restore phases 1-5.
"""

ENGINE_CODE = '''
(() => {
  const $ = s => document.querySelector(s);
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* Canonical 7 Specialist Agents (Phase 1) */
  const AGENTS = {
    ob: { name: 'Obstetrics', short: 'Obstetrics', color: '#2E9FE6', book: 'Williams Obstetrics' },
    em: { name: 'Emergency Medicine', short: 'Emergency', color: '#0E9AA7', book: "Tintinalli's Emergency Medicine" },
    ca: { name: 'Cardiology', short: 'Cardiology', color: '#1F7BEA', book: "Braunwald's Heart Disease" },
    su: { name: 'Surgery', short: 'Surgery', color: '#13A06B', book: "Schwartz's Principles of Surgery" },
    gy: { name: 'Gynecology', short: 'Gynecology', color: '#0FA88A', book: 'Williams Gynecology' },
    ne: { name: 'Neurology', short: 'Neurology', color: '#5B3DF5', book: "Adams and Victor's Principles of Neurology" },
    im: { name: 'Internal Medicine', short: 'Internal Med.', color: '#2B2FD9', book: "Harrison's Principles of Internal Medicine" },
  };

  /* Default Table Order (lead at top, clockwise descending score, standby at bottom) */
  const SEAT_ORDER = ['ob', 'em', 'ca', 'su', 'gy', 'ne', 'im'];

  /* Node Status Map */
  const NODE_STATUS = {
    idle: 'Ready',
    thinking: 'Evaluating…',
    speaking: 'Sharing',
    listening: 'Listening',
    agreed: 'Agrees',
    standby: 'Standby'
  };

  /* Single State Source of Truth */
  let currentCaseKey = 'preeclampsia_hellp';
  let activeCase = CASES[currentCaseKey];

  const state = {
    phase: 'idle',         // 'idle' | 'routing' | 'review' | 'crosscheck' | 'consensus' | 'signoff'
    running: false,        // false = paused or idle
    routing: null,         // RoutingResult | null
    filter: null,          // AgentKey | null (ALWAYS null on load / case change)
    tab: 'draft',          // 'draft' | 'discussion' (ALWAYS 'draft' on load / case change)
    eventIndex: 0,
    eventSubState: 'idle', // 'idle' | 'thinking' | 'speaking'
    subStateTime: 0,
    agreedAgents: new Set(),
    agreedPlans: new Set(),
    showAllLabs: false
  };

  /* DOM references */
  const table = $('#table');
  const cv = $('#cv');
  const ctx = cv.getContext('2d');
  let W = 0, H = 0, dpr = 1;
  const pos = {};
  let core = { x: 0, y: 0 };
  const nodes = {};
  const rcol = {};
  const planRows = {};
  const packets = [];
  let speakerAt = null;
  let phaseTimer = 0;
  let pausedElapsed = 0;

  /** Scopes internal SVG IDs so gradients and masks never collide */
  function uniquifyIds(svg, suffix) {
    if (!svg) return '';
    const ids = Array.from(svg.matchAll(/id="([^"]+)"/g)).map(m => m[1]);
    return ids.reduce(
      (s, id) => s.split(`id="${id}"`).join(`id="${id}-${suffix}"`).split(`url(#${id})`).join(`url(#${id}-${suffix})`),
      svg,
    );
  }

  /** Replays a one-shot CSS class cleanly via reflow */
  function triggerOneShot(el, className, durationMs) {
    if (!el) return;
    el.classList.remove(className);
    void el.offsetWidth;
    el.classList.add(className);
    setTimeout(() => {
      el.classList.remove(className);
    }, durationMs);
  }

  /* Derive Labels */
  function routedSummary(r) {
    if (!r) return 'Not routed yet';
    const assignedCount = Object.values(r.status).filter(s => s !== 'standby').length;
    const totalCount = Object.keys(r.status).length;
    const leadKey = Object.keys(r.status).find(k => r.status[k] === 'lead') || r.primary;
    const leadName = AGENTS[leadKey] ? AGENTS[leadKey].name : 'Specialist';
    return `Routed ${r.routedAt || '14:17'} · ${assignedCount} of ${totalCount} assigned · ${leadName} leads`;
  }

  function getLabels() {
    switch (state.phase) {
      case 'idle':
        return { router: 'Not routed yet', stage: 'Not started', badge: null, action: 'Route case' };
      case 'routing':
        return { router: 'Routing the case…', stage: state.running ? 'Routing' : 'Routing (Paused)', badge: 'Live', action: state.running ? 'Pause' : 'Resume' };
      case 'review':
        return { router: routedSummary(state.routing), stage: state.running ? 'Independent review' : 'Independent review (Paused)', badge: 'Live', action: state.running ? 'Pause' : 'Resume' };
      case 'crosscheck':
        return { router: routedSummary(state.routing), stage: state.running ? 'Cross-check' : 'Cross-check (Paused)', badge: 'Live', action: state.running ? 'Pause' : 'Resume' };
      case 'consensus':
        return { router: routedSummary(state.routing), stage: state.running ? 'Consensus' : 'Consensus (Paused)', badge: 'Live', action: state.running ? 'Pause' : 'Resume' };
      case 'signoff':
        return { router: routedSummary(state.routing), stage: 'Ready to sign', badge: 'Awaiting signature', action: 'Replay' };
    }
  }

  /* Sync Header, Badges, and Primary Control */
  function syncUI() {
    const labels = getLabels();

    // Router header
    $('#r-sum').textContent = labels.router;

    // Stage text
    $('#stage-t').textContent = labels.stage;

    // Stage Segments (4 segments: Review, Crosscheck, Consensus, Ready to sign)
    const segs = document.querySelectorAll('.stage .segs i');
    segs.forEach((seg, idx) => {
      let on = false;
      if (state.phase === 'review' && idx === 0) on = true;
      else if (state.phase === 'crosscheck' && idx <= 1) on = true;
      else if (state.phase === 'consensus' && idx <= 2) on = true;
      else if (state.phase === 'signoff') on = true;
      seg.classList.toggle('on', on);
    });

    // Dossier Badges
    const badgeStatus = $('#dossier-status');
    if (labels.badge) {
      badgeStatus.hidden = false;
      badgeStatus.textContent = labels.badge;
      badgeStatus.className = 'badge-status' + (labels.badge === 'Awaiting signature' ? ' awaiting' : '');
    } else {
      badgeStatus.hidden = true;
    }

    const badgeSynthetic = $('#dossier-synthetic');
    badgeSynthetic.hidden = !activeCase.synthetic;

    // Primary Control in Specialists Header
    const mainBtn = $('#b-main-control');
    const mainSpan = mainBtn.querySelector('span');
    const replayBtn = $('#b-replay');

    mainSpan.textContent = labels.action;
    mainBtn.setAttribute('aria-label', labels.action);

    if (labels.action === 'Route case' || labels.action === 'Resume') {
      mainBtn.querySelector('svg').innerHTML = '<polygon points="3.5 2.5 13.5 8 3.5 13.5"/>';
    } else if (labels.action === 'Pause') {
      mainBtn.querySelector('svg').innerHTML = '<rect x="3" y="2.5" width="3.4" height="11" rx="1"/><rect x="9.6" y="2.5" width="3.4" height="11" rx="1"/>';
    } else if (labels.action === 'Replay') {
      mainBtn.querySelector('svg').innerHTML = '<path d="M2.5 8a5.5 5.5 0 1 0 1.7-4"/><path d="M2.5 2.5v3h3"/>';
    }

    // Secondary replay button only visible once run is in progress or completed
    replayBtn.hidden = (state.phase === 'idle');

    // Board Copy
    const board = $('#board');
    if (state.phase === 'idle') {
      board.innerHTML = '<b>MedGemma router</b><p>Press Route case to assign specialists.</p>';
    } else if (state.phase === 'routing') {
      board.innerHTML = '<b>MedGemma router</b><p>Scoring relevance for each specialist…</p>';
    } else if (state.phase === 'signoff') {
      const leadK = (state.routing && state.routing.primary) || 'ob';
      const roleText = leadK === 'ob' ? 'on-call obstetrician' : 'attending physician';
      board.innerHTML = `<b>MedGemma router</b><p>Waiting for the ${roleText}.</p>`;
    }

    // Sign button
    const signBtn = $('#b-sign');
    signBtn.disabled = (state.phase !== 'signoff');
    signBtn.title = (state.phase === 'signoff') ? 'Authorize and sign clinical plan' : 'Available when the agents agree';

    // Tabs & Panels
    syncPanels();
  }

  /* Sync Draft and Discussion Panels */
  function syncPanels() {
    const isDraft = (state.tab === 'draft');
    $('#t-draft').setAttribute('aria-selected', String(isDraft));
    $('#t-disc').setAttribute('aria-selected', String(!isDraft));
    $('#p-draft').hidden = !isDraft;
    $('#p-disc').hidden = isDraft;

    // Draft empty state vs content
    const hasDraftContent = (state.phase !== 'idle' && state.phase !== 'routing');
    $('#draft-empty').hidden = hasDraftContent;
    $('#draft-content').hidden = !hasDraftContent;

    // Discussion empty state vs messages
    const discList = $('#disc-list');
    const msgCount = discList.children.length;
    $('#disc-empty').hidden = (msgCount > 0);
    $('#count').textContent = msgCount;

    // Badge styling for unread
    const countBadge = $('#count');
    countBadge.classList.toggle('has-unread', isDraft && msgCount > 0);

    // Discussion Filter Chip
    const filterChip = $('#filter-chip');
    if (state.filter) {
      filterChip.hidden = false;
      const ag = AGENTS[state.filter];
      $('#filter-chip-text').textContent = `${ag ? ag.name : state.filter} only`;
    } else {
      filterChip.hidden = true;
    }
  }

  /* Populate Clinical Dossier */
  function populateSidebar(c) {
    $('#pt-name').textContent = c.name;
    $('#pt-id').textContent = c.mrn;
    $('#pt-demog').textContent = c.demog;

    const acuityEl = $('#pt-acuity');
    acuityEl.className = 'badge-esi ' + (c.acuityClass || 'esi2');
    acuityEl.textContent = c.acuity || `ESI ${c.esi} · Emergent`;

    $('#pt-cc').textContent = c.chief_complaint;
    $('#pt-hpi').textContent = c.hpi;

    // Vitals (3x2 grid, tabular nums, SpO2)
    const vitGrid = $('#vitals-grid');
    vitGrid.innerHTML = c.vitals.map(v => `
      <div class="vital-item ${v.status}">
        <span class="vital-label">${v.label}</span>
        <span class="vital-val">${v.val} <small>${v.unit}</small></span>
      </div>
    `).join('');

    // Render Labs
    renderLabs(c);

    // Imaging Studies (2-line clamp on findings, finding first)
    const imgList = $('#imaging-list');
    imgList.innerHTML = c.imaging.map((img, idx) => `
      <div class="imaging-card" data-idx="${idx}">
        <div class="imaging-info">
          <span class="imaging-title">${img.title}</span>
          <span class="imaging-findings">${img.desc}</span>
        </div>
        <button type="button" class="imaging-btn" aria-label="View study">View</button>
      </div>
    `).join('');

    imgList.querySelectorAll('.imaging-card').forEach(card => {
      card.addEventListener('click', () => {
        const idx = parseInt(card.dataset.idx, 10);
        openImagingModal(c.imaging[idx]);
      });
    });
  }

  /* Render Labs: Abnormal only by default, expand to all */
  function renderLabs(c) {
    const list = $('#labs-list');
    const labs = c.labs || [];
    const abnormalLabs = labs.filter(l => l.status === 'low' || l.status === 'high' || l.status === 'crit' || l.status === 'critical');
    const displayLabs = state.showAllLabs ? labs : (abnormalLabs.length ? abnormalLabs : labs);

    list.innerHTML = displayLabs.map(l => {
      const flagClass = (l.status === 'critical' || l.status === 'crit') ? 'critical' : (l.status === 'low' ? 'low' : (l.status === 'high' ? 'high' : 'norm'));
      const flagText = l.flag || (flagClass === 'critical' ? 'Critical' : (flagClass === 'low' ? 'Low' : (flagClass === 'high' ? 'High' : '')));
      return `
        <div class="lab-row">
          <span class="lab-name">${l.name}</span>
          <div class="lab-right">
            <span class="lab-val">${l.val}</span>
            ${flagText ? `<span class="lab-flag ${flagClass}">${flagText}</span>` : ''}
          </div>
        </div>
      `;
    }).join('');

    const toggleBtn = $('#b-show-all-labs');
    if (labs.length > abnormalLabs.length) {
      toggleBtn.hidden = false;
      toggleBtn.textContent = state.showAllLabs ? `Show abnormal only (${abnormalLabs.length})` : `Show all labs (${labs.length})`;
    } else {
      toggleBtn.hidden = true;
    }
  }

  $('#b-show-all-labs').addEventListener('click', () => {
    state.showAllLabs = !state.showAllLabs;
    renderLabs(activeCase);
  });

  /* Imaging Modal */
  function openImagingModal(img) {
    $('#modal-title').textContent = `${img.title} (${img.mod})`;
    $('#modal-report').innerHTML = img.modalText;
    $('#modal-preview').innerHTML = `
      <div style="text-align:center;color:#94A3B8;display:flex;flex-direction:column;align-items:center;gap:12px;">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width:56px;height:56px;color:var(--indigo)">
          <path d="M4 4h16v16H4z"/><path d="M9 9h6v6H9z"/>
        </svg>
        <span style="font-size:13px;font-family:monospace;letter-spacing:.05em;">HIGH RESOLUTION DIAGNOSTIC SCAN DATA</span>
      </div>
    `;
    $('#imaging-modal').hidden = false;
  }
  $('#modal-close').addEventListener('click', () => { $('#imaging-modal').hidden = true; });
  $('#imaging-modal').addEventListener('click', e => {
    if (e.target === $('#imaging-modal')) $('#imaging-modal').hidden = true;
  });

  /* Render Router Cards */
  function renderRouterCards() {
    const rcols = $('#rcols');
    rcols.innerHTML = '';

    // Sort order: if routing exists, sort high to low by score; otherwise default SEAT_ORDER
    let order = [...SEAT_ORDER];
    if (state.routing && state.routing.scores) {
      order.sort((a, b) => (state.routing.scores[b] || 0) - (state.routing.scores[a] || 0));
    }

    order.forEach(k => {
      const a = AGENTS[k];
      const isRouted = !!state.routing;
      const score = isRouted && state.routing.scores ? state.routing.scores[k] : null;
      const status = isRouted && state.routing.status ? state.routing.status[k] : null;
      const isStandby = (status === 'standby');
      const isLead = (status === 'lead');

      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'rc' + (isStandby ? ' standby' : '');
      btn.style.setProperty('--c', a.color);
      btn.setAttribute('aria-pressed', String(state.filter === k));
      btn.setAttribute('aria-label', `${a.name}: ${score !== null ? score + '% relevance' : 'Not routed'}${isLead ? ', lead' : ''}. Select to filter.`);

      let tagMarkup = '';
      if (isRouted && status) {
        if (isLead) tagMarkup = '<span class="tag lead">Lead</span>';
        else if (isStandby) tagMarkup = '<span class="tag">Standby</span>';
        else tagMarkup = '<span class="tag">Assigned</span>';
      }

      btn.innerHTML = `
        <span class="nm">
          <img src="${AV[k]}" alt="">
          <span>${a.short}</span>
        </span>
        <div class="pc">
          <b class="v">${score !== null ? score : '—'}</b>
          ${tagMarkup}
        </div>
        <span class="rbar"><i style="width:${score !== null ? score : 0}%"></i></span>
      `;

      btn.addEventListener('click', () => {
        setFilter(state.filter === k ? null : k);
      });

      rcols.appendChild(btn);
      rcol[k] = btn;
    });
  }

  /* Animate Scores */
  function animateScores(scores, ms = 1300) {
    if (reduce) {
      for (const [key, el] of Object.entries(rcol)) {
        const v = scores[key] || 0;
        const vEl = el.querySelector('.v');
        const barEl = el.querySelector('.rbar i');
        if (vEl) vEl.textContent = Math.round(v);
        if (barEl) barEl.style.width = v + '%';
      }
      return;
    }

    const t0 = performance.now();
    const ease = k => 1 - Math.pow(1 - k, 3);
    function step(now) {
      const k = Math.min(1, (now - t0) / ms), u = ease(k);
      for (const [key, el] of Object.entries(rcol)) {
        const v = (scores[key] || 0) * u;
        const vEl = el.querySelector('.v');
        const barEl = el.querySelector('.rbar i');
        if (vEl) vEl.textContent = Math.round(v);
        if (barEl) barEl.style.width = v + '%';
      }
      if (k < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  /* Room Nodes Setup with Full Animation Hooks */
  SEAT_ORDER.forEach((k, i) => {
    const a = AGENTS[k];
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'node';
    b.style.setProperty('--c', a.color);
    b.style.setProperty('--d', `${(-i * 0.63).toFixed(2)}s`);
    b.style.setProperty('--bd', `${(i * 0.8 + 0.4).toFixed(2)}s`);
    b.setAttribute('aria-label', `${a.name} AI agent. Filter messages.`);

    const inlineSvg = uniquifyIds(AVSVG[k] || '', `${k}-${i}`);

    b.innerHTML = `
      <span class="av">
        <span class="halo"></span>
        <span class="spin"></span>
        <span class="orbit" aria-hidden="true">
          <i style="--a:0deg"></i>
          <i style="--a:-28deg"></i>
          <i style="--a:-52deg"></i>
        </span>
        <span class="face" aria-hidden="true">${inlineSvg}</span>
        <span class="ok" aria-hidden="true">
          <svg viewBox="0 0 12 12" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2.5 6.3l2.3 2.2 4.7-5" />
          </svg>
        </span>
      </span>
      <span class="nm">${a.name}</span>
      <span class="st">Ready</span>
    `;

    b.addEventListener('click', () => {
      setFilter(state.filter === k ? null : k);
    });

    table.appendChild(b);
    nodes[k] = b;
  });

  /* Node and Seating Layout */
  function layout() {
    const r = table.getBoundingClientRect();
    W = r.width;
    H = r.height;
    dpr = window.devicePixelRatio || 1;
    cv.width = W * dpr;
    cv.height = H * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    const small = W < 640;
    const rx = W * (small ? 0.40 : 0.41);
    const ry = H * (small ? 0.36 : 0.36);
    core = { x: W / 2, y: H / 2 };

    // Update agent name strings for responsive screens
    SEAT_ORDER.forEach(k => {
      const nm = nodes[k].querySelector('.nm');
      if (nm) nm.textContent = small ? AGENTS[k].short : AGENTS[k].name;
    });

    // Seating order: lead at top (-PI/2), clockwise descending scores
    SEAT_ORDER.forEach((k, i) => {
      const a = -Math.PI / 2 + (i * Math.PI * 2) / SEAT_ORDER.length;
      const x = W / 2 + Math.cos(a) * rx;
      const y = H / 2 + Math.sin(a) * ry - (small ? 6 : 10);
      pos[k] = { x, y };
      nodes[k].style.left = x + 'px';
      nodes[k].style.top = y + 'px';
    });
  }
  window.addEventListener('resize', layout);

  /* Gaze Pupils Tracking in SVG User Units (±30 / ±22) */
  function gaze(pt, except) {
    SEAT_ORDER.forEach(k => {
      const n = nodes[k], p = pos[k];
      if (!p || n.classList.contains('standby')) return;
      if (!pt || k === except) {
        n.style.setProperty('--gx', '0px');
        n.style.setProperty('--gy', '0px');
        return;
      }
      const dx = pt.x - p.x, dy = pt.y - p.y;
      const dist = Math.hypot(dx, dy) || 1;
      n.style.setProperty('--gx', ((dx / dist) * 30).toFixed(1) + 'px');
      n.style.setProperty('--gy', ((dy / dist) * 22).toFixed(1) + 'px');
    });
  }

  table.addEventListener('pointermove', e => {
    const r = table.getBoundingClientRect();
    gaze({ x: e.clientX - r.left, y: e.clientY - r.top });
  });
  table.addEventListener('pointerleave', () => gaze(speakerAt));

  /* Draft & Plan Setup */
  function setupDraftPlan(c) {
    $('#dx').textContent = c.dx;
    $('#watch-for').textContent = c.watchFor;
    $('#ddx').textContent = c.ddx.map(d => d.t).join(', ');

    const planEl = $('#plan');
    planEl.innerHTML = '';
    c.plan.forEach(p => {
      const li = document.createElement('li');
      li.className = 'plan-item';
      li.id = 'plan-' + p.id;
      const ownerTags = p.own.map(o => `<span class="own-pill">${AGENTS[o] ? AGENTS[o].short : o}</span>`).join('');
      li.innerHTML = `
        <input type="checkbox" id="chk-${p.id}" disabled>
        <label for="chk-${p.id}">
          <span class="owners">${ownerTags}</span>
          ${p.t}
        </label>
      `;
      planEl.appendChild(li);
      planRows[p.id] = li;
    });
  }

  /* Reset to Initial State */
  function resetToInitialState() {
    state.phase = 'idle';
    state.running = false;
    state.routing = null;
    state.filter = null;
    state.tab = 'draft';
    state.eventIndex = 0;
    state.eventSubState = 'idle';
    state.subStateTime = 0;
    state.agreedAgents.clear();
    state.agreedPlans.clear();
    state.showAllLabs = false;
    packets.length = 0;
    speakerAt = null;

    $('#disc-list').innerHTML = '';
    $('#count').textContent = '0';
    $('#conf').textContent = '0.75';
    $('#agree').textContent = '0';
    $('#meter').style.width = '0%';

    SEAT_ORDER.forEach(k => {
      nodes[k].className = 'node';
      nodes[k].style.setProperty('--gx', '0px');
      nodes[k].style.setProperty('--gy', '0px');
      const isSb = (activeCase.router && activeCase.router.standby && activeCase.router.standby.includes(k));
      if (isSb) nodes[k].classList.add('standby');
      nodes[k].querySelector('.st').textContent = isSb ? NODE_STATUS.standby : NODE_STATUS.idle;
    });

    renderRouterCards();
    syncUI();
  }

  /* Filter Handling */
  function setFilter(k) {
    state.filter = k;
    if (k) {
      state.tab = 'discussion';
    }

    // Toggle selected and dimmed nodes
    SEAT_ORDER.forEach(t => {
      nodes[t].classList.toggle('sel', t === k);
      nodes[t].classList.toggle('dim', k !== null && t !== k);
    });

    // Toggle router tile selection
    Object.entries(rcol).forEach(([kk, b]) => {
      b.setAttribute('aria-pressed', String(kk === k));
    });

    // Filter discussion messages
    document.querySelectorAll('.msg').forEach(m => {
      m.hidden = !!k && m.dataset.who !== k;
    });

    syncUI();
  }

  // Clear filter via button and Escape key
  $('#b-clear-filter').addEventListener('click', () => setFilter(null));
  window.addEventListener('keydown', e => {
    if (e.key === 'Escape') setFilter(null);
  });

  /* Tabs switching */
  $('#t-draft').addEventListener('click', () => {
    state.tab = 'draft';
    syncUI();
  });
  $('#t-disc').addEventListener('click', () => {
    state.tab = 'discussion';
    syncUI();
    const d = $('#disc-list');
    d.scrollTop = d.scrollHeight;
  });

  /* TTS Voice playback */
  async function speakTurn(who, voiceText) {
    const voiceCheckbox = $('#voice');
    if (!voiceText || !voiceCheckbox || !voiceCheckbox.checked) return;

    try {
      const resp = await fetch('/api/tts/speak', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: voiceText,
          voice: who,
          specialty: AGENTS[who] ? AGENTS[who].name : 'Specialist'
        })
      });
      const data = await resp.json();
      if (data.audio_base64 && !data.fallback) {
        const audio = new Audio('data:audio/mp3;base64,' + data.audio_base64);
        await audio.play();
        return;
      }
    } catch (e) {
      // Backend unavailable, fallback to browser speech synthesis
    }

    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const ut = new SpeechSynthesisUtterance(voiceText);
      ut.rate = 1.05;
      window.speechSynthesis.speak(ut);
    }
  }

  /* Deliberation Event Handlers */
  function startEventThinking(idx, now) {
    const events = activeCase.events || [];
    if (idx >= events.length) {
      finishDeliberation();
      return;
    }

    const ev = events[idx];
    const whoAg = AGENTS[ev.who] || { name: ev.who, short: ev.who, book: '' };

    // Update Phase based on progress
    if (idx === 0) state.phase = 'review';
    else if (idx >= 2 && idx < events.length - 2) state.phase = 'crosscheck';
    else if (idx >= events.length - 2 && idx < events.length) state.phase = 'consensus';

    state.eventSubState = 'thinking';
    state.subStateTime = now;

    // Reset speaking on all nodes, preserve agreed
    SEAT_ORDER.forEach(k => {
      nodes[k].classList.remove('speaking', 'thinking');
      if (k === ev.who) {
        nodes[k].classList.add('thinking');
        nodes[k].querySelector('.st').textContent = NODE_STATUS.thinking;
      } else if (state.agreedAgents.has(k)) {
        nodes[k].querySelector('.st').textContent = NODE_STATUS.agreed;
      } else if (!nodes[k].classList.contains('standby')) {
        nodes[k].querySelector('.st').textContent = NODE_STATUS.listening;
      }
    });

    speakerAt = pos[ev.who];
    gaze(speakerAt, ev.who);

    $('#board').innerHTML = `<b>${whoAg.name}</b><p>Evaluating clinical telemetry…</p>`;
    syncUI();
  }

  function startEventSpeaking(idx, now) {
    const events = activeCase.events || [];
    if (idx >= events.length) {
      finishDeliberation();
      return;
    }

    const ev = events[idx];
    const whoAg = AGENTS[ev.who] || { name: ev.who, short: ev.who, book: '' };

    state.eventSubState = 'speaking';
    state.subStateTime = now;

    // Node styling: ev.who transitions from thinking to speaking
    SEAT_ORDER.forEach(k => {
      nodes[k].classList.remove('thinking');
      if (k === ev.who) {
        nodes[k].classList.add('speaking');
        nodes[k].querySelector('.st').textContent = NODE_STATUS.speaking;
      }
    });

    // Append discussion message
    const msg = document.createElement('div');
    msg.className = 'msg';
    msg.dataset.who = ev.who;
    msg.hidden = (state.filter !== null && state.filter !== ev.who);
    msg.innerHTML = `
      <div class="msg-hdr">
        <span class="msg-who">
          <img src="${AV[ev.who]}" alt="">
          ${whoAg.name} <span style="font-weight:400;color:var(--mute)">· AI agent</span>
        </span>
        <span class="msg-cite">${whoAg.book}</span>
      </div>
      <div>${ev.detail}</div>
    `;
    const discList = $('#disc-list');
    discList.appendChild(msg);
    if (state.tab === 'discussion') {
      discList.scrollTop = discList.scrollHeight;
    }

    // Packet animation
    const targetPos = (ev.to && pos[ev.to]) ? pos[ev.to] : core;
    if (pos[ev.who]) {
      packets.push({
        from: pos[ev.who],
        to: targetPos,
        color: AGENTS[ev.who] ? AGENTS[ev.who].color : '#2B2FD9',
        t0: now,
        dur: 900
      });
    }

    // Board update
    $('#board').innerHTML = `<b>${whoAg.name}</b><p>${ev.short}</p>`;

    // Voice verbal line
    speakTurn(ev.who, ev.voice);

    // One-shot hear trigger on recipient
    if (ev.to && ev.to !== 'board' && nodes[ev.to]) {
      triggerOneShot(nodes[ev.to], 'hear', 700);
    }

    // Agreements
    if (ev.agreeWith) {
      ev.agreeWith.forEach(w => {
        state.agreedAgents.add(w);
        if (nodes[w]) {
          triggerOneShot(nodes[w], 'nod', 950);
          nodes[w].classList.add('agreed');
          if (w !== ev.who) nodes[w].querySelector('.st').textContent = NODE_STATUS.agreed;
        }
      });
    }

    if (ev.planAgrees) {
      ev.planAgrees.forEach(pid => state.agreedPlans.add(pid));
    }

    // Update Plan Items
    activeCase.plan.forEach(pl => {
      const isAgreed = state.agreedPlans.has(pl.id);
      const li = planRows[pl.id];
      if (li) {
        li.classList.toggle('agreed', isAgreed);
        const chk = li.querySelector('input');
        if (chk) chk.checked = isAgreed;
      }
    });

    // Update agreement counter & meter
    const totalAgents = SEAT_ORDER.filter(k => !nodes[k].classList.contains('standby')).length;
    const count = Math.min(totalAgents, state.agreedAgents.size);
    $('#agree').textContent = count;

    const progress = (idx + 1) / events.length;
    const currentConf = (0.75 + progress * (activeCase.conf - 0.75)).toFixed(2);
    $('#conf').textContent = currentConf;
    $('#meter').style.width = (progress * 100) + '%';

    syncUI();
  }

  function finishEventSpeaking(idx, now) {
    const events = activeCase.events || [];
    const ev = events[idx];
    if (ev && nodes[ev.who]) {
      nodes[ev.who].classList.remove('speaking');
      if (state.agreedAgents.has(ev.who)) {
        nodes[ev.who].classList.add('agreed');
        nodes[ev.who].querySelector('.st').textContent = NODE_STATUS.agreed;
      } else {
        nodes[ev.who].querySelector('.st').textContent = NODE_STATUS.listening;
      }
    }

    state.eventIndex++;
    if (state.eventIndex < events.length) {
      startEventThinking(state.eventIndex, now);
    } else {
      finishDeliberation();
    }
  }

  function finishDeliberation() {
    state.phase = 'signoff';
    state.running = false;
    state.eventSubState = 'idle';
    speakerAt = null;
    gaze(null);
    syncUI();
  }

  /* Step forward synchronously through events */
  function stepTo(targetIndex) {
    const events = activeCase.events || [];
    while (state.eventIndex < targetIndex && state.eventIndex < events.length) {
      const idx = state.eventIndex;
      const ev = events[idx];
      const whoAg = AGENTS[ev.who] || { name: ev.who, short: ev.who, book: '' };

      // Update Phase
      if (idx === 0) state.phase = 'review';
      else if (idx >= 2 && idx < events.length - 2) state.phase = 'crosscheck';
      else if (idx >= events.length - 2 && idx < events.length) state.phase = 'consensus';

      if (ev.agreeWith) ev.agreeWith.forEach(w => state.agreedAgents.add(w));
      if (ev.planAgrees) ev.planAgrees.forEach(pid => state.agreedPlans.add(pid));

      const msg = document.createElement('div');
      msg.className = 'msg';
      msg.dataset.who = ev.who;
      msg.hidden = (state.filter !== null && state.filter !== ev.who);
      msg.innerHTML = `
        <div class="msg-hdr">
          <span class="msg-who">
            <img src="${AV[ev.who]}" alt="">
            ${whoAg.name} <span style="font-weight:400;color:var(--mute)">· AI agent</span>
          </span>
          <span class="msg-cite">${whoAg.book}</span>
        </div>
        <div>${ev.detail}</div>
      `;
      $('#disc-list').appendChild(msg);

      state.eventIndex++;
    }

    activeCase.plan.forEach(pl => {
      const isAgreed = state.agreedPlans.has(pl.id);
      const li = planRows[pl.id];
      if (li) {
        li.classList.toggle('agreed', isAgreed);
        const chk = li.querySelector('input');
        if (chk) chk.checked = isAgreed;
      }
    });

    SEAT_ORDER.forEach(k => {
      nodes[k].classList.remove('speaking', 'thinking');
      if (state.agreedAgents.has(k)) {
        nodes[k].classList.add('agreed');
        nodes[k].querySelector('.st').textContent = NODE_STATUS.agreed;
      } else if (!nodes[k].classList.contains('standby')) {
        nodes[k].querySelector('.st').textContent = NODE_STATUS.listening;
      }
    });

    const totalAgents = SEAT_ORDER.filter(k => !nodes[k].classList.contains('standby')).length;
    const count = Math.min(totalAgents, state.agreedAgents.size);
    $('#agree').textContent = count;
    const progress = state.eventIndex / events.length;
    const currentConf = (0.75 + progress * (activeCase.conf - 0.75)).toFixed(2);
    $('#conf').textContent = currentConf;
    $('#meter').style.width = (progress * 100) + '%';

    if (state.eventIndex >= events.length) {
      finishDeliberation();
    } else {
      startEventThinking(state.eventIndex, performance.now());
    }
    syncUI();
  }

  /* Tick loop for Canvas and Timeline */
  function tick(now) {
    ctx.clearRect(0, 0, W, H);

    // Spokes to center
    SEAT_ORDER.forEach(k => {
      const p = pos[k];
      if (!p) return;
      const sb = nodes[k].classList.contains('standby');
      ctx.strokeStyle = sb ? 'rgba(201,206,218,.35)' : '#E3E6EE';
      ctx.lineWidth = 1;
      ctx.setLineDash(sb ? [3, 4] : []);
      ctx.beginPath();
      ctx.moveTo(p.x, p.y);
      ctx.lineTo(core.x, core.y);
      ctx.stroke();
    });
    ctx.setLineDash([]);

    // Packets
    for (let i = packets.length - 1; i >= 0; i--) {
      const P = packets[i];
      const u = Math.min(1, (now - P.t0) / P.dur);
      const e = u < 0.5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2;
      const x = P.from.x + (P.to.x - P.from.x) * e;
      const y = P.from.y + (P.to.y - P.from.y) * e;

      ctx.fillStyle = P.color;
      ctx.beginPath();
      ctx.arc(x, y, 4.5, 0, Math.PI * 2);
      ctx.fill();

      if (u >= 1) packets.splice(i, 1);
    }

    // Step progression when running
    if (state.running) {
      if (state.phase === 'routing') {
        if (now - phaseTimer > 2000) {
          state.phase = 'review';
          renderRouterCards();
          animateScores(state.routing.scores, 1300);
          state.eventIndex = 0;
          startEventThinking(0, now);
        }
      } else if (state.eventSubState === 'thinking') {
        const thinkingDur = reduce ? 0 : 1300;
        if (now - state.subStateTime >= thinkingDur) {
          startEventSpeaking(state.eventIndex, now);
        }
      } else if (state.eventSubState === 'speaking') {
        const speakingDur = reduce ? 0 : 1800;
        if (now - state.subStateTime >= speakingDur) {
          finishEventSpeaking(state.eventIndex, now);
        }
      }
    }

    requestAnimationFrame(tick);
  }

  /* Primary Control Flow */
  async function handleMainControl() {
    if (state.phase === 'idle') {
      // Start routing
      state.phase = 'routing';
      state.running = true;
      phaseTimer = performance.now();
      syncUI();

      // Consult backend router with graceful fallback
      let result = activeCase.router;
      try {
        const resp = await fetch('/api/router/route', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            chief_complaint: activeCase.chief_complaint,
            patient_history: activeCase.hpi,
            vitals: activeCase.vitals,
            diagnostic_data: activeCase.labs
          })
        });
        if (resp.ok) {
          const data = await resp.json();
          const mapKey = name => {
            if (!name) return null;
            const n = name.toLowerCase();
            if (n.includes('obstet')) return 'ob';
            if (n.includes('gynec')) return 'gy';
            if (n.includes('emerg')) return 'em';
            if (n.includes('cardio')) return 'ca';
            if (n.includes('neuro')) return 'ne';
            if (n.includes('surg')) return 'su';
            if (n.includes('internal')) return 'im';
            return null;
          };
          const primaryKey = mapKey(data.primary_agent) || activeCase.router.primary;
          const consultKey = mapKey(data.consult_agent) || activeCase.router.consult;
          const scores = activeCase.router.scores;
          const status = { ...activeCase.router.status };
          if (primaryKey) status[primaryKey] = 'lead';
          result = {
            ...activeCase.router,
            primary: primaryKey,
            consult: consultKey,
            scores,
            status
          };
        }
      } catch (e) {
        // Fallback to activeCase.router
      }

      state.routing = result;
      syncUI();
      return;
    }

    if (state.phase === 'signoff') {
      replay();
      return;
    }

    // Toggle Pause / Resume
    const now = performance.now();
    if (state.running) {
      // Pausing
      state.running = false;
      pausedElapsed = now - state.subStateTime;
    } else {
      // Resuming
      state.running = true;
      state.subStateTime = now - pausedElapsed;
      phaseTimer = now;
    }
    syncUI();
  }

  function replay() {
    resetToInitialState();
    handleMainControl();
  }

  $('#b-main-control').addEventListener('click', handleMainControl);
  $('#b-replay').addEventListener('click', replay);

  /* Case Selector Change */
  const caseSelect = $('#case-select');
  Object.keys(CASES).forEach(k => {
    const opt = document.createElement('option');
    opt.value = k;
    opt.textContent = `${CASES[k].name} — ${CASES[k].dx.split(' ')[0]} (${CASES[k].acuity.split('·')[0].trim()})`;
    caseSelect.appendChild(opt);
  });

  caseSelect.addEventListener('change', () => {
    currentCaseKey = caseSelect.value;
    activeCase = CASES[currentCaseKey];
    populateSidebar(activeCase);
    setupDraftPlan(activeCase);
    resetToInitialState();
  });

  // Logo navigation to Intake
  const vhLogo = document.querySelector('.vh');
  if (vhLogo) {
    vhLogo.addEventListener('click', (e) => {
      e.preventDefault();
      if (window.parent && window.parent !== window) {
        window.parent.postMessage({ type: 'NAVIGATE', tab: 'INTAKE' }, '*');
      }
    });
  }

  /* Boot Sequence */
  populateSidebar(activeCase);
  setupDraftPlan(activeCase);
  resetToInitialState();
  layout();
  requestAnimationFrame(tick);

})();
'''
