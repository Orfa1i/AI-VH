const $ = s => document.querySelector(s);
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  const AG = {
    ob: { name: 'Obstetrics', c: '#2E9FE6', lead: true, rel: 97 },
    em: { name: 'Emergency Medicine', short: 'Emergency', c: '#0E9AA7', rel: 92 },
    im: { name: 'Internal Medicine', short: 'Internal Med.', c: '#2B2FD9', rel: 88 },
    ca: { name: 'Cardiology', c: '#1F7BEA', rel: 81 },
    ne: { name: 'Neurology', c: '#5B3DF5', rel: 79 },
    su: { name: 'Surgery', c: '#13A06B', rel: 64 },
    gy: { name: 'Gynecology', c: '#0FA88A', standby: true, rel: 18 },
    router: { name: 'MedGemma router', c: '#4A5068', sys: true },
    report: { name: 'NVIDIA Nemotron', c: '#4A5068', sys: true },
  };
  const ASSIGNED = ['ob', 'em', 'im', 'ca', 'ne', 'su'];
  const TABLE = ['ob', 'em', 'ca', 'su', 'gy', 'ne', 'im'];
  AV.report = AV.router;

  /* ---------- plan and differential ---------- */
  const PLAN = [
    { id: 'monitor', own: ['em'], t: '<b>Stabilise:</b> left lateral position, two large-bore IV lines, seizure precautions, continuous CTG.' },
    { id: 'bp', own: ['ca', 'ob'], t: '<b>Severe-range BP:</b> IV labetalol 20 mg, then 40 and 80 mg every 10 min while still severe. Target 140–150 / 90–100.' },
    { id: 'mg', own: ['ob', 'ne'], t: '<b>Seizure prophylaxis:</b> magnesium sulfate 4 g IV over 20 min, then 1 g/h. Hourly reflexes, respiratory rate and urine output.' },
    { id: 'deliver', own: ['ob'], t: '<b>Delivery</b> after maternal stabilisation. Corticosteroids must not delay it.' },
    { id: 'labs', own: ['im'], t: '<b>Repeat</b> platelets, liver enzymes, LDH and coagulation within 6 h. Neuraxial anaesthesia while platelets stay ≥70 ×10⁹/L.' },
    { id: 'us', own: ['su'], t: '<b>Bedside RUQ ultrasound</b> to exclude a subcapsular hepatic haematoma. Surgery attends delivery if one is found.' },
    { id: 'imaging', own: ['ne', 'ob'], t: '<b>No brain imaging before delivery.</b> Image if a focal sign appears, a seizure occurs on magnesium, or symptoms persist after delivery.' },
  ];
  const DDX = [
    { id: 'pe', t: 'Severe preeclampsia + HELLP' }, { id: 'aflp', t: 'Acute fatty liver' },
    { id: 'chole', t: 'Acute cholecystitis' }, { id: 'ttp', t: 'TTP / HUS' }, { id: 'other', t: 'Other' },
  ];
  const DX0 = { pe: .62, aflp: .14, chole: .10, ttp: .08, other: .06 };

  /* ---------- the deliberation script ---------- */
  const EV = [
    { who: 'router', kind: 'system', ph: 0, think: 'Routing', short: 'Case routed to six specialists',
      text: 'Lead: Obstetrics. Assigned: Emergency Medicine, Internal Medicine, Cardiology, Neurology and Surgery. Gynecology on standby.' },
    { who: 'em', kind: 'assessment', ph: 1, think: 'Reading vitals', short: 'Obstetric emergency. Stabilise first.',
      text: 'Severe-range BP on two readings 15 minutes apart, with headache and visual symptoms. Treat as an obstetric emergency: left lateral, two large-bore lines, seizure precautions, continuous CTG.',
      cites: ["Tintinalli's"], fx: { plan: { monitor: 'proposed' } } },
    { who: 'ob', kind: 'assessment', ph: 1, think: 'Applying HELLP criteria', short: 'Severe preeclampsia with HELLP',
      text: 'Severe-range BP, proteinuria 3+, headache and RUQ pain at 34 + 2 weeks: preeclampsia with severe features. Platelets 88, AST 142 and LDH 720 meet the Tennessee criteria for HELLP. At this gestation the plan is delivery once she is stable.',
      cites: ['Williams Obstetrics', 'PubMed · ACOG Practice Bulletin 222'], fx: { dx: { pe: .82, aflp: .08, chole: .05, ttp: .03, other: .02 }, plan: { deliver: 'proposed', mg: 'proposed' } } },
    { who: 'im', kind: 'assessment', ph: 1, think: 'Checking the differential', short: 'Acute fatty liver is less likely',
      text: 'Haemolysis, raised liver enzymes and low platelets fit HELLP. Glucose 5.1 and fibrinogen 3.4 argue against acute fatty liver. Creatinine 87 µmol/L is normal for now; magnesium is cleared by the kidneys, so urine output matters.',
      cites: ["Harrison's"], fx: { dx: { pe: .88, aflp: .04, chole: .04, ttp: .02, other: .02 }, plan: { labs: 'proposed' } } },
    { who: 'ca', kind: 'assessment', ph: 1, think: 'Choosing an antihypertensive', short: 'Lower BP within 30 to 60 minutes',
      text: 'Confirmed severe-range BP needs treatment within 30 to 60 minutes. First line: IV labetalol 20 mg, or oral immediate-release nifedipine 10 mg if IV access is delayed. Avoid a sudden drop; aim for 140–150 / 90–100.',
      cites: ["Braunwald's", 'PubMed · ACOG Committee Opinion 767'], fx: { plan: { bp: 'proposed' } } },
    { who: 'ne', kind: 'assessment', ph: 1, think: 'Assessing seizure risk', short: 'High risk of eclampsia',
      text: 'Headache, flashing lights and clonus put her at high risk of an eclamptic seizure. Magnesium sulfate is the drug of choice for prophylaxis. Keep PRES and cerebral venous thrombosis in the differential.',
      cites: ["Adams and Victor's"] },
    { who: 'su', kind: 'assessment', ph: 1, think: 'Reviewing the RUQ pain', short: 'Exclude a hepatic haematoma',
      text: 'RUQ pain with HELLP is most often stretching of the liver capsule. A subcapsular haematoma needs excluding before theatre; rupture is rare but surgical. Cholecystitis is unlikely with this lab pattern.',
      cites: ["Schwartz's"], fx: { dx: { pe: .90, aflp: .04, chole: .02, ttp: .02, other: .02 }, plan: { us: 'proposed' } } },
    { who: 'ne', to: ['ob'], kind: 'challenge', ph: 2, think: 'Weighing imaging', short: 'Should we image the brain before delivery?',
      text: 'I would like an MRI of the brain before delivery to exclude PRES or venous thrombosis.', fx: { plan: { imaging: 'discussing' } } },
    { who: 'ob', to: ['ne'], kind: 'challenge', ph: 2, think: 'Weighing delay against benefit', short: 'Imaging now would delay the treatment',
      text: 'Delivery treats the cause, and imaging now delays it. GCS is 15 with no focal deficit. I propose imaging only if a focal sign appears, a seizure occurs on magnesium, or symptoms persist after delivery.',
      cites: ['Williams Obstetrics'] },
    { who: 'em', to: ['ne'], kind: 'agree', ph: 2, think: 'Checking monitoring needs', short: 'Keep her on the monitor',
      text: 'Agree with Obstetrics. A trip to MRI takes her off continuous monitoring while her BP is still in the severe range.', fx: { agree: ['em'], plan: { monitor: 'agreed' } } },
    { who: 'ne', kind: 'revision', ph: 2, think: 'Revising', short: 'Accepted, with triggers recorded',
      text: 'Accepted. No imaging before delivery. Triggers recorded: focal deficit, seizure despite magnesium, or headache and visual symptoms that persist after delivery.',
      fx: { agree: ['ne'], plan: { imaging: 'agreed' } } },
    { who: 'im', to: ['ca'], kind: 'evidence', ph: 2, think: 'Checking the drug label', short: 'No contraindication to labetalol',
      text: 'No asthma or heart block recorded, and HR is 104, so labetalol is suitable. If bradycardia develops, switch to hydralazine or oral nifedipine.',
      cites: ['openFDA · Labetalol label', 'RxNorm'] },
    { who: 'ca', kind: 'agree', ph: 2, think: 'Confirming', short: 'Labetalol first line',
      text: 'Agreed. IV labetalol first, escalating every 10 minutes while BP stays severe, with the target unchanged.', fx: { agree: ['ca'], plan: { bp: 'agreed' } } },
    { who: 'im', to: ['ob'], kind: 'evidence', ph: 2, think: 'Checking anaesthesia thresholds', short: 'Platelets 88 allow neuraxial',
      text: 'A platelet count of 88 still permits neuraxial anaesthesia; the consensus threshold is 70. HELLP counts can fall quickly, so repeat within 6 hours and tell anaesthesia now.',
      cites: ['PubMed · SOAP consensus 2021'], fx: { agree: ['im'], plan: { labs: 'agreed' } } },
    { who: 'ob', kind: 'revision', ph: 2, think: 'Writing the plan', short: 'Magnesium and delivery confirmed',
      text: 'Magnesium sulfate 4 g IV over 20 minutes, then 1 g/h. Delivery after stabilisation; corticosteroids must not delay it. Mode of delivery after the ultrasound and cervical assessment.',
      cites: ['openFDA · Magnesium sulfate label', 'Williams Obstetrics'], fx: { agree: ['ob'], plan: { mg: 'agreed', deliver: 'agreed' } } },
    { who: 'su', kind: 'agree', ph: 2, think: 'Confirming', short: 'Ultrasound first, surgery on call',
      text: 'Agreed. RUQ ultrasound goes first. If a haematoma is seen, surgery attends the delivery and blood products are prepared.',
      fx: { agree: ['su'], plan: { us: 'agreed' }, dx: { pe: .91, aflp: .04, chole: .02, ttp: .02, other: .01 } } },
    { who: 'report', kind: 'system', ph: 3, think: 'Assembling the report', short: 'Consensus reached. Draft report assembled.',
      text: 'Six of six assigned agents agree. NVIDIA Nemotron assembled the draft: working diagnosis, seven-step plan and every citation above.' },
    { who: 'router', kind: 'system', ph: 4, think: 'Queueing for review', short: 'Waiting for the on-call obstetrician',
      text: 'Draft placed in the review queue. Nothing reaches the patient until the on-call obstetrician signs, edits or rejects it.', fx: { done: true } },
  ];

  const STAGES = ['Independent review', 'Cross-check', 'Consensus', 'Ready to sign'];

  /* ---------- the table ---------- */
  const table = $('#table'); const nodes = {};
  TABLE.forEach((k, i) => {
    const a = AG[k], b = document.createElement('button'); b.type = 'button'; b.className = 'node' + (a.standby ? ' standby' : ''); b.style.setProperty('--c', a.c);
    b.setAttribute('aria-label', `${a.name} agent. Show only its messages.`);
    b.style.setProperty('--d', (-i * .63).toFixed(2) + 's'); b.style.setProperty('--bd', (i * .8 + .4).toFixed(2) + 's');
    b.innerHTML = `<span class="av"><span class="halo"></span><span class="spin"></span><span class="orbit" aria-hidden="true"><i style="--a:0deg"></i><i style="--a:-28deg"></i><i style="--a:-52deg"></i></span><span class="face" aria-hidden="true">${AVSVG[k]}</span><span class="ok" aria-hidden="true"><svg viewBox="0 0 12 12" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M2.5 6.3l2.3 2.2 4.7-5"/></svg></span></span><span class="nm">${a.short && innerWidth < 640 ? a.short : a.name}</span><span class="st">${a.standby ? 'Standby' : 'Ready'}</span>`;
    b.addEventListener('click', () => { setFilter(filter === k ? null : k); if (filter) showTab('disc'); });
    table.appendChild(b); nodes[k] = b;
  });
  const planEl = $('#plan'); const planRows = {};
  const CHECK = '<svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M2.5 6.3l2.3 2.2 4.7-5"/></svg>';
  PLAN.forEach(p => { const li = document.createElement('li'); li.className = 'step pending'; li.innerHTML = `<span class="ic" aria-hidden="true"></span><span>${p.t}<small></small></span>`; planEl.appendChild(li); planRows[p.id] = li; });


  /* ---------- MedGemma routing: relevance per agent, counted up when the case is routed ---------- */
  const rcols = $('#rcols'); const rcol = {};
  Object.keys(AG).filter(k => !AG[k].sys).sort((a, b) => AG[b].rel - AG[a].rel).forEach(k => {
    const a = AG[k], b = document.createElement('button'); b.type = 'button'; b.className = 'rc' + (a.standby ? ' standby' : ''); b.style.setProperty('--c', a.c);
    b.setAttribute('aria-pressed', 'false'); b.setAttribute('aria-label', `${a.name}: ${a.rel}% relevance, ${a.lead ? 'lead' : a.standby ? 'standby' : 'assigned'}. Show only its messages.`);
    b.innerHTML = `<span class="nm"><img src="${AV[k]}" alt=""><span>${a.short || a.name}</span></span><span class="pc"><b><span class="v">0</span><small>%</small></b><span class="tag${a.lead ? ' lead' : ''}">${a.lead ? 'Lead' : a.standby ? 'Standby' : 'Assigned'}</span></span><span class="rbar"><i></i></span>`;
    b.addEventListener('click', () => { setFilter(filter === k ? null : k); if (filter) showTab('disc'); });
    rcols.appendChild(b); rcol[k] = b;
  });
  let routeAnim = 0;
  const route = (u) => { Object.entries(rcol).forEach(([k, b]) => { const v = Math.round(AG[k].rel * u); b.querySelector('.v').textContent = v; b.querySelector('.rbar i').style.width = (AG[k].rel * u) + '%'; });
    $('#r-sum').textContent = u >= 1 ? 'Routed 14:17 · 6 of 7 specialists assigned · Obstetrics leads' : 'Routing the case…'; };
  const routeTo = animate => { cancelAnimationFrame(routeAnim);
    if (!animate) { route(1); return; }
    const t0 = performance.now(); const step = now => { const k = Math.min(1, (now - t0) / 1300); route(1 - Math.pow(1 - k, 3)); if (k < 1) routeAnim = requestAnimationFrame(step); }; routeAnim = requestAnimationFrame(step); };
  /* ---------- tabs ---------- */
  let tab = 'draft', unseen = 0;
  const showTab = t => { tab = t;
    $('#t-draft').setAttribute('aria-selected', String(t === 'draft')); $('#t-disc').setAttribute('aria-selected', String(t === 'disc'));
    $('#p-draft').hidden = t !== 'draft'; $('#p-disc').hidden = t !== 'disc';
    if (t === 'disc') { unseen = 0; const m = $('#p-disc'); m.scrollTop = m.scrollHeight; } render(); };
  $('#t-draft').addEventListener('click', () => showTab('draft'));
  $('#t-disc').addEventListener('click', () => showTab('disc'));

  /* ---------- state ---------- */
  let S;
  const reset = () => {
    S = { i: 0, dx: { ...DX0 }, plan: {}, agree: new Set(), phase: 0, clock: 14 * 3600 + 18 * 60 + 4, msgs: 0 };
    $('#msgs').innerHTML = ''; $('#typing').innerHTML = ''; unseen = 0;
    PLAN.forEach(p => S.plan[p.id] = 'pending');
    TABLE.forEach(k => { nodes[k].classList.remove('thinking', 'speaking', 'agreed'); nodes[k].querySelector('.st').textContent = AG[k].standby ? 'Standby' : 'Ready'; });
    setBoard('router', 'Reading the intake…', false); routeTo(false); route(0);
    $('#b-send').disabled = true; render();
  };
  const fmt = s => [Math.floor(s / 3600), Math.floor(s / 60) % 60].map(n => String(n).padStart(2, '0')).join(':');

  const render = () => {
    const st = Math.max(0, S.phase - 1);
    $('#stage-t').textContent = STAGES[Math.min(3, st)];
    [...document.querySelectorAll('.segs i')].forEach((el, i) => el.className = i < st ? 'done' : i === st ? (st === 3 ? 'done' : 'on') : '');
    const p = S.dx.pe;
    $('#meter').style.width = (p * 100) + '%'; $('#conf').textContent = p.toFixed(2);
    $('#dx').textContent = p >= .85 ? 'Preeclampsia with severe features and HELLP syndrome' : 'Preeclampsia with severe features';
    $('#ddx').textContent = DDX.filter(d => d.id !== 'pe' && d.id !== 'other').map(d => `${d.t} ${S.dx[d.id].toFixed(2)}`).join(', ');
    $('#agree').textContent = S.agree.size;
    TABLE.forEach(k => nodes[k].classList.toggle('agreed', S.agree.has(k) && !nodes[k].classList.contains('thinking') && !nodes[k].classList.contains('speaking')));
    let ag = 0;
    PLAN.forEach(pl => { const s2 = S.plan[pl.id], li = planRows[pl.id]; if (s2 === 'agreed') ag++;
      li.className = 'step ' + s2; li.querySelector('.ic').innerHTML = s2 === 'agreed' ? CHECK : '';
      li.querySelector('small').textContent = s2 === 'discussing' ? 'Under discussion' : ''; });
    $('#plan-t').textContent = `${ag} of ${PLAN.length} agreed`;
    const c = $('#count'); c.textContent = S.msgs; c.className = unseen && tab !== 'disc' ? 'new' : '';
    const done = S.phase >= 4;
    $('#trail-sign')?.classList.toggle('on', done);
    $('#sign-t').textContent = done ? 'Ready for the on-call obstetrician.' : 'Available when the agents agree.';
  };

  /* ---------- messages ---------- */
  let filter = null;
  const KIND = { challenge: '<span class="chal">challenges</span>', agree: '<span class="agr">agrees</span>', revision: '<span>revises</span>', evidence: '<span>adds evidence</span>' };
  const addMsg = e => {
    const a = AG[e.who], el = document.createElement('article');
    el.className = 'msg' + (a.sys ? ' sys' : ''); el.dataset.who = e.who; el.style.setProperty('--c', a.c);
    const to = e.to ? `<span>to ${e.to.map(k => AG[k].short || AG[k].name).join(', ')}</span>` : '';
    el.innerHTML = `<img src="${AV[e.who]}" alt=""><div><header><b>${a.short || a.name}</b>${KIND[e.kind] || ''}${to}<span style="margin-left:auto">${fmt(S.clock)}</span></header><p>${e.text}</p>${e.cites ? `<div class="src">${e.cites.join(' · ')}</div>` : ''}</div>`;
    if (filter && e.who !== filter) el.hidden = true;
    $('#msgs').appendChild(el); S.msgs++; if (tab !== 'disc') unseen++;
    const m = $('#p-disc'); if (tab === 'disc') m.scrollTop = m.scrollHeight;
  };
  function setFilter(k) {
    filter = k;
    document.querySelectorAll('.msg').forEach(m => m.hidden = !!k && m.dataset.who !== k);
    TABLE.forEach(t => { nodes[t].classList.toggle('sel', t === k); nodes[t].classList.toggle('dim', !!k && t !== k); });
    Object.entries(rcol).forEach(([kk, b]) => b.setAttribute('aria-pressed', String(kk === k)));
    $('#filter').hidden = !k; if (k) $('#filter-t').textContent = `${AG[k].name} only`;
  }
  $('#filter-x').addEventListener('click', () => setFilter(null));
  const setBoard = (who, text, animate) => { const b = $('#board'); b.style.setProperty('--c', AG[who].c);
    b.innerHTML = `<b>${AG[who].short || AG[who].name}</b><p>${text}</p>`;
    if (animate) { b.classList.remove('fresh'); void b.offsetWidth; b.classList.add('fresh'); } };

  const apply = (e, animate) => {
    S.clock += 18 + Math.round(Math.random() * 16);
    S.phase = Math.max(S.phase, e.ph);
    const fx = e.fx || {};
    if (fx.dx) S.dx = { ...fx.dx };
    if (fx.plan) Object.entries(fx.plan).forEach(([id, st]) => S.plan[id] = st);
    if (fx.agree) fx.agree.forEach(k => { S.agree.add(k); if (animate) setTimeout(() => pulse(k, 'nod', 950), 250); });
    if (fx.done) { S.phase = 4; $('#b-send').disabled = false; }
    if (e.ph === 3) S.agree = new Set(ASSIGNED);
    if (e.who === 'router' && e.ph === 0) routeTo(animate);
    addMsg(e);
    setBoard(e.who, (e.to ? '→ ' + e.to.map(k => AG[k].short || AG[k].name).join(', ') + ': ' : '') + e.short, animate);
    TABLE.forEach(k => { if (!AG[k].standby && !nodes[k].classList.contains('thinking')) nodes[k].querySelector('.st').textContent = S.agree.has(k) ? 'Agrees' : (heard.has(k) ? 'Listening' : 'Ready'); });
    render();
  };
  const heard = new Set();

  /* ---------- geometry ---------- */
  const cv = $('#cv'), ctx = cv.getContext('2d'); let W = 0, H = 0, DPR = Math.min(2, devicePixelRatio || 1), pos = {}, core = { x: 0, y: 0 };
  const layout = () => {
    W = table.clientWidth; H = table.clientHeight; cv.width = W * DPR; cv.height = H * DPR; ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    const small = W < 520, rx = W * (small ? .37 : .395), ry = H * (small ? .36 : .355);
    core = { x: W / 2, y: H / 2 };
    TABLE.forEach((k, i) => {
      const a = -Math.PI / 2 + i * Math.PI * 2 / TABLE.length;
      const x = W / 2 + Math.cos(a) * rx, y = H / 2 + Math.sin(a) * ry - (small ? 6 : 10);
      pos[k] = { x, y }; nodes[k].style.left = x + 'px'; nodes[k].style.top = y + 'px';
    });
    pos.router = pos.report = core;
    draw(performance.now());
  };
  new ResizeObserver(layout).observe(table);

  /* ---------- the agents watch each other: eyes follow the speaker, or your pointer ---------- */
  let speakerAt = null, pointerIn = false;
  const gaze = (pt, except) => TABLE.forEach(k => {
    const n = nodes[k], p = pos[k]; if (!p || AG[k].standby) return;
    if (!pt || k === except) { n.style.setProperty('--gx', '0px'); n.style.setProperty('--gy', '0px'); return; }
    const dx = pt.x - p.x, dy = pt.y - p.y, d = Math.hypot(dx, dy) || 1, m = Math.min(1, d / 120);
    n.style.setProperty('--gx', (dx / d * 30 * m).toFixed(1) + 'px'); n.style.setProperty('--gy', (dy / d * 22 * m).toFixed(1) + 'px');
  });
  const pulse = (k, cls, ms) => { const n = nodes[k]; if (!n) return; n.classList.remove(cls); void n.offsetWidth; n.classList.add(cls); setTimeout(() => n.classList.remove(cls), ms); };
  if (!reduce) {
    table.addEventListener('pointermove', e => { const r = table.getBoundingClientRect(); pointerIn = true; gaze({ x: e.clientX - r.left, y: e.clientY - r.top }); });
    table.addEventListener('pointerleave', () => { pointerIn = false; gaze(speakerAt); });
  }

  /* ---------- packets, sparks and the drawing ---------- */
  const packets = []; const ripples = [];
  const curve = (a, b, bend) => { const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2; return { x: mx + (core.x - mx) * bend, y: my + (core.y - my) * bend }; };
  const qp = (a, c, b, t) => ({ x: (1 - t) ** 2 * a.x + 2 * (1 - t) * t * c.x + t * t * b.x, y: (1 - t) ** 2 * a.y + 2 * (1 - t) * t * c.y + t * t * b.y });
  const send = (from, to, col, dur, now, onArrive) => {
    const a = pos[from] || core, b = to === 'core' ? core : pos[to];
    packets.push({ a, b, c: to === 'core' || from === 'router' || from === 'report' ? { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 } : curve(a, b, .55), col, t0: now, dur, onArrive });
  };
  const KCOL = { challenge: '#C2374F', agree: '#13A06B' };
  const draw = now => {
    ctx.clearRect(0, 0, W, H);
    // spokes to the shared board
    TABLE.forEach(k => { const p = pos[k]; if (!p) return; const sb = AG[k].standby;
      ctx.strokeStyle = sb ? 'rgba(201,206,218,.5)' : '#DDE1EA'; ctx.lineWidth = 1; ctx.setLineDash(sb ? [3, 5] : []);
      ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(core.x, core.y); ctx.stroke(); });
    ctx.setLineDash([]);
    ctx.globalAlpha = 1;
    // live message arcs
    for (let i = packets.length - 1; i >= 0; i--) {
      const P = packets[i], u = Math.min(1, (now - P.t0) / P.dur), e = u < .5 ? 2 * u * u : 1 - (-2 * u + 2) ** 2 / 2;
      ctx.strokeStyle = P.col; ctx.lineWidth = 2; ctx.globalAlpha = .55 * (1 - Math.max(0, u - .7) / .3);
      ctx.beginPath(); for (let s = 0; s <= 24; s++) { const q = qp(P.a, P.c, P.b, Math.min(e, s / 24)); s ? ctx.lineTo(q.x, q.y) : ctx.moveTo(q.x, q.y); } ctx.stroke();
      const h = qp(P.a, P.c, P.b, e); ctx.globalAlpha = 1;
      const g = ctx.createRadialGradient(h.x, h.y, 0, h.x, h.y, 14); g.addColorStop(0, P.col + '55'); g.addColorStop(1, P.col + '00');
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(h.x, h.y, 14, 0, 7); ctx.fill();
      ctx.fillStyle = P.col; ctx.beginPath(); ctx.arc(h.x, h.y, 4, 0, 7); ctx.fill();
      if (u >= 1) { packets.splice(i, 1); P.onArrive && P.onArrive(now); }
    }
    ctx.globalAlpha = 1;
    // ripples on the board
    for (let i = ripples.length - 1; i >= 0; i--) { const r = ripples[i], u = (now - r.t0) / 900; if (u >= 1) { ripples.splice(i, 1); continue; }
      ctx.strokeStyle = r.col; ctx.globalAlpha = (1 - u) * .5; ctx.lineWidth = 2; ctx.beginPath(); ctx.ellipse(core.x, core.y, 60 + u * 90, 40 + u * 60, 0, 0, 7); ctx.stroke(); }
    ctx.globalAlpha = 1;
  };


  /* ---------- the player ---------- */
  let playing = !reduce, stage = 'idle', cur = null, stageAt = 0;
  const THINK = 1500, FLY = 950, GAP = 1600;
  const stepTo = i => { while (S.i < i) { const e = EV[S.i]; heard.add(e.who); apply(e, false); S.i++; } };
  const startEvent = now => {
    cur = EV[S.i]; stage = 'think'; stageAt = now;
    const n = nodes[cur.who];
    if (n) { n.classList.add('thinking'); n.classList.remove('agreed'); n.querySelector('.st').textContent = cur.think + '…'; }
    const t = $('#typing'); t.style.setProperty('--c', AG[cur.who].c);
    t.innerHTML = `<img src="${AV[cur.who]}" alt=""><span>${AG[cur.who].short || AG[cur.who].name} is ${cur.think.toLowerCase()}</span><span class="dots"><i></i><i></i><i></i></span>`;
  };
  const speak = now => {
    stage = 'fly'; stageAt = now;
    const n = nodes[cur.who]; if (n) { n.classList.remove('thinking'); n.classList.add('speaking'); n.querySelector('.st').textContent = 'Sharing'; }
    const col = KCOL[cur.kind] || AG[cur.who].c; const e = cur;
    speakerAt = AG[e.who].sys ? core : pos[e.who]; if (!pointerIn) gaze(speakerAt, e.who);
    const land = () => {
      $('#typing').innerHTML = ''; heard.add(e.who); apply(e, true); S.i++;
      ripples.push({ col, t0: performance.now() });
      if (n) setTimeout(() => { n.classList.remove('speaking'); render(); if (!AG[e.who].standby) n.querySelector('.st').textContent = S.agree.has(e.who) ? 'Agrees' : 'Listening'; }, 700);
      stage = 'gap'; stageAt = performance.now();
    };
    if (e.to) { let left = e.to.length; e.to.forEach(k => send(e.who, k, col, FLY, now, () => { pulse(k, 'hear', 700); if (--left === 0) land(); })); }
    else if (AG[e.who].sys) ASSIGNED.forEach((k, j) => send('router', k, col, FLY, now, j === 0 ? land : null));
    else send(e.who, 'core', col, FLY, now, land);
  };
  const tick = now => {
    if (playing) {
      if (stage === 'idle' && S.i < EV.length) startEvent(now);
      else if (stage === 'think' && now - stageAt > THINK) speak(now);
      else if (stage === 'gap' && now - stageAt > GAP) { stage = 'idle'; if (S.i >= EV.length) { stage = 'end'; syncPlay(); } }
    }
    if (!reduce) { draw(now); requestAnimationFrame(tick); }
  };

  /* ---------- controls ---------- */
  const playBtn = $('#b-play');
  const syncPlay = () => {
    const showPlay = !playing || stage === 'end';
    playBtn.setAttribute('aria-label', stage === 'end' ? 'Play again' : playing ? 'Pause' : 'Play');
    playBtn.querySelector('svg').innerHTML = showPlay ? '<path d="M4 2.5v11l9-5.5z"/>' : '<rect x="3" y="2.5" width="3.4" height="11" rx="1"/><rect x="9.6" y="2.5" width="3.4" height="11" rx="1"/>'; };
  playBtn.addEventListener('click', () => { if (stage === 'end') { replay(); return; } playing = !playing; syncPlay(); });
  const replay = () => { speakerAt = null; gaze(null); packets.length = 0; ripples.length = 0; heard.clear(); reset(); stage = 'idle'; playing = !reduce; if (reduce) stepTo(EV.length); syncPlay(); };
  $('#b-replay').addEventListener('click', replay);
  const toast = $('#toast'); let tt;
  const say = m => { toast.textContent = m; toast.classList.add('on'); clearTimeout(tt); tt = setTimeout(() => toast.classList.remove('on'), 3200); };
  $('#b-send').addEventListener('click', () => {
    if (window.parent && window.parent !== window) {
      window.parent.postMessage({ type: 'NAVIGATE', tab: 'REVIEWING' }, '*');
    }
    say('Reviewing: opening clinical draft for signature, edits or rejection.');
  });
  document.querySelectorAll('[data-tab]').forEach(b => b.addEventListener('click', (e) => {
    e.preventDefault();
    const tabName = b.getAttribute('data-tab');
    if (window.parent && window.parent !== window) {
      if (tabName === 'triage') window.parent.postMessage({ type: 'NAVIGATE', tab: 'INTAKE' }, '*');
      else if (tabName === 'attending') window.parent.postMessage({ type: 'NAVIGATE', tab: 'PATIENTS' }, '*');
      else if (tabName === 'signoff') window.parent.postMessage({ type: 'NAVIGATE', tab: 'REVIEWING' }, '*');
    }
    say('Switching to ' + b.textContent.trim());
  }));
  const vhLogo = document.querySelector('.vh');
  if (vhLogo) {
    vhLogo.addEventListener('click', (e) => {
      e.preventDefault();
      if (window.parent && window.parent !== window) {
        window.parent.postMessage({ type: 'NAVIGATE', tab: 'INTAKE' }, '*');
      }
    });
  }

  reset(); layout();
  const on = $('.tab.on'); if (on) on.scrollIntoView({ block: 'nearest', inline: 'nearest' });
  if (reduce) { stepTo(EV.length); syncPlay(); }
  else { stepTo(4); speakerAt = pos[EV[3].who]; gaze(speakerAt, EV[3].who); syncPlay(); requestAnimationFrame(tick); }
})();
</script>

</body></html>