# -*- coding: utf-8 -*-
"""
CSS Module for case-room.html
Implements exact styling rules from case-room-bugfix audit.
"""

CSS_CONTENT = '''
:root {
  color-scheme: light;
  box-sizing: border-box;
  --paper: #F7F8FB;
  --white: #FFFFFF;
  --ink: #0F1222;
  --graphite: #4A5068;
  --mute: #6B7189;
  --hair: #E3E6EE;
  --hair-2: #EEF0F5;
  --indigo: #2B2FD9;
  --indigo-50: #EEEFFD;
  --indigo-600: #2226B8;
  --verdant: #13A06B;
  --verdant-50: #E8F6EF;
  --crit: #C2374F;
  --crit-50: #FCEBEE;
  --warn: #9A5B00;
  --warn-50: #FBF1E2;
  --amber: #D97706;
  --amber-50: #FEF3C7;
  --display: "Funnel Display", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --body: "Host Grotesk", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --shadow: 0 1px 3px rgba(15,18,34,.05), 0 10px 28px rgba(31,36,90,.06);
  --shadow-lg: 0 12px 36px rgba(15,18,34,.12);
  --ease: cubic-bezier(.2,.7,.2,1);
}
* { box-sizing: border-box; }
html, body {
  margin: 0; padding: 0;
  background: var(--paper);
  color: var(--ink);
  font: 400 14px/1.55 var(--body);
  -webkit-font-smoothing: antialiased;
}
button { font: inherit; color: inherit; }
:focus-visible { outline: 2px solid var(--indigo); outline-offset: 2px; border-radius: 8px; }
.num { font-variant-numeric: tabular-nums; }
[hidden] { display: none !important; }

/* ---------- Page Layout (Grid) ---------- */
.case-room {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr);
  gap: 18px;
  width: min(1680px, calc(100% - 32px));
  margin: 16px auto 32px;
  align-items: start;
}
.case-main {
  display: grid;
  gap: 18px;
  min-width: 0;
}
.case-body {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(340px, .85fr);
  gap: 18px;
  align-items: stretch;
}

/* ---------- Cards Base ---------- */
.card {
  background: var(--white);
  border-radius: 16px;
  box-shadow: var(--shadow);
  border: 1px solid var(--hair);
  position: relative;
}

/* ---------- Left Panel: Clinical Dossier ---------- */
.dossier {
  background: var(--white);
  border: 1px solid var(--hair);
  border-radius: 16px;
  box-shadow: var(--shadow);
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: sticky;
  top: 16px;
  max-height: calc(100vh - 32px);
  overflow-y: auto;
  scrollbar-width: thin;
}
.dossier::-webkit-scrollbar { width: 6px; }
.dossier::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 4px; }

.dossier-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--hair-2);
  padding-bottom: 12px;
}
.dossier-header h2 {
  margin: 0;
  font: 600 15px var(--display);
  color: var(--ink);
  display: flex;
  align-items: center;
  gap: 8px;
}
.dossier-badges {
  display: flex;
  align-items: center;
  gap: 6px;
}
.badge-synthetic {
  font-size: 11px;
  font-weight: 600;
  color: var(--warn);
  background: var(--warn-50);
  border: 1px solid #FDE68A;
  padding: 2px 8px;
  border-radius: 999px;
}
.badge-status {
  font-size: 11px;
  font-weight: 600;
  color: var(--verdant);
  background: var(--verdant-50);
  border: 1px solid #BFE6D2;
  padding: 2px 8px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  gap: 5px;
}
.badge-status.awaiting {
  color: var(--indigo);
  background: var(--indigo-50);
  border-color: #C7D2FE;
}
.badge-status::before {
  content: "";
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  animation: pulse-dot 1.8s infinite;
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.85); }
}

/* Patient Case Selector */
.case-select-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.case-select-group label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--mute);
}
.case-select {
  width: 100%;
  padding: 9px 11px;
  border-radius: 10px;
  border: 1px solid var(--hair);
  background: var(--paper);
  color: var(--ink);
  font: 600 13px var(--body);
  cursor: pointer;
  transition: all .2s;
  outline: none;
}
.case-select:focus {
  border-color: var(--indigo);
  background: var(--white);
  box-shadow: 0 0 0 3px var(--indigo-50);
}

/* Clean Voice Audio Switch */
.switch {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--graphite);
  padding: 4px 0;
  user-select: none;
}
.switch input {
  appearance: none;
  width: 34px;
  height: 20px;
  border-radius: 999px;
  background: #E3E6EE;
  position: relative;
  cursor: pointer;
  transition: background .2s;
  flex: none;
  margin: 0;
}
.switch input::after {
  content: "";
  position: absolute;
  top: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15,18,34,.2);
  transition: transform .2s;
}
.switch input:checked { background: var(--indigo); }
.switch input:checked::after { transform: translateX(14px); }
.switch input:focus-visible { outline: 2px solid var(--indigo); outline-offset: 2px; }

/* Patient Card */
.patient-card {
  background: var(--paper);
  border: 1px solid var(--hair-2);
  border-radius: 12px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.patient-card-name {
  font: 700 15px var(--display);
  color: var(--ink);
}
.patient-card-id {
  font-size: 11.5px;
  font-family: monospace;
  color: var(--mute);
  font-weight: 600;
}
.patient-card-demog {
  font-size: 12.5px;
  color: var(--graphite);
}
.badge-esi {
  display: inline-block;
  align-self: flex-start;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
  margin-top: 4px;
}
.badge-esi.esi1 { background: var(--crit-50); color: var(--crit); border: 1px solid #F5C2C7; }
.badge-esi.esi2 { background: var(--amber-50); color: var(--warn); border: 1px solid #FDE68A; }
.badge-esi.esi3 { background: var(--verdant-50); color: var(--verdant); border: 1px solid #A7F3D0; }

/* Dossier Text Sections */
.dossier-sec {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.dossier-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--mute);
}
.dossier-text {
  background: var(--paper);
  border: 1px solid var(--hair-2);
  border-radius: 10px;
  padding: 9px 11px;
  font-size: 12.5px;
  line-height: 1.45;
  color: var(--graphite);
}

/* Vitals Grid (3x2) */
.vitals-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
}
.vital-item {
  background: var(--paper);
  border: 1px solid var(--hair-2);
  border-radius: 8px;
  padding: 6px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.vital-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--mute);
}
.vital-val {
  font: 700 13px/1.2 var(--display);
  color: var(--ink);
  font-variant-numeric: tabular-nums;
  display: flex;
  align-items: baseline;
  gap: 2px;
}
.vital-val small { font-size: 10px; font-weight: 400; color: var(--mute); }
.vital-item.abnormal {
  border-color: #F87171;
  background: #FEF2F2;
}
.vital-item.abnormal .vital-val { color: var(--crit); }

/* Labs: No Nested Scrollbar! Natural Height */
.labs-wrap {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.labs-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.lab-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--paper);
  border: 1px solid var(--hair-2);
  border-radius: 7px;
  padding: 5px 9px;
  font-size: 11.5px;
}
.lab-name { font-weight: 600; color: var(--ink); }
.lab-right {
  display: flex;
  align-items: center;
  gap: 6px;
}
.lab-val {
  font-weight: 700;
  color: var(--graphite);
  font-variant-numeric: tabular-nums;
  text-align: right;
}
.lab-flag {
  font-size: 10.5px;
  font-weight: 700;
  text-align: right;
  min-width: 32px;
}
.lab-flag.low, .lab-flag.high {
  color: var(--crit);
}
.lab-flag.critical {
  background: var(--crit);
  color: var(--white);
  padding: 1px 6px;
  border-radius: 999px;
  font-size: 9.5px;
  text-transform: uppercase;
}
.show-all-labs-btn {
  background: none;
  border: none;
  padding: 4px 0;
  font-size: 11.5px;
  font-weight: 600;
  color: var(--indigo);
  cursor: pointer;
  text-align: left;
}
.show-all-labs-btn:hover { text-decoration: underline; }

/* Imaging Studies */
.imaging-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.imaging-card {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  background: var(--paper);
  border: 1px solid var(--hair-2);
  border-radius: 9px;
  padding: 8px 10px;
}
.imaging-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}
.imaging-title {
  font: 600 12px var(--body);
  color: var(--ink);
}
.imaging-findings {
  font-size: 11px;
  line-height: 1.4;
  color: var(--mute);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.imaging-btn {
  background: var(--indigo-50);
  border: 1px solid #C7D2FE;
  color: var(--indigo);
  font-size: 11px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 5px;
  cursor: pointer;
  flex: none;
}
.imaging-btn:hover { background: #E0E7FF; }

/* Modal for Imaging */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15,18,34,.65);
  backdrop-filter: blur(4px);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.modal-box {
  background: var(--white);
  border-radius: 16px;
  box-shadow: var(--shadow-lg);
  max-width: 600px;
  width: 100%;
  max-height: 85vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid var(--hair);
}
.modal-head h3 {
  margin: 0;
  font: 600 16px var(--display);
  color: var(--ink);
}
.modal-close {
  background: none;
  border: none;
  font-size: 20px;
  line-height: 1;
  color: var(--mute);
  cursor: pointer;
  padding: 4px;
}
.modal-close:hover { color: var(--ink); }
.modal-body {
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.modal-preview-box {
  background: #0F1222;
  border-radius: 10px;
  padding: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}
.modal-report {
  background: var(--paper);
  border-radius: 10px;
  padding: 12px 14px;
  font-size: 13px;
  line-height: 1.5;
  color: var(--graphite);
  border: 1px solid var(--hair-2);
}

/* ---------- MedGemma Router Card ---------- */
.router { padding: 16px 18px; }
.router .rh {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}
.router .rh img {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: var(--paper);
  padding: 3px;
  border: 1px solid var(--hair);
}
.router .rh h2 {
  margin: 0;
  font: 600 16px var(--display);
  letter-spacing: -.01em;
}
.router .rh span {
  font-size: 13px;
  color: var(--mute);
  margin-left: 2px;
}

/* Router Columns & Tiles */
.rcols {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: minmax(150px, 1fr);
  gap: 10px;
  overflow-x: auto;
  scrollbar-width: none;
}
.rc {
  display: grid;
  gap: 6px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid #E3E6EE;
  background: #fff;
  text-align: left;
  cursor: pointer;
  transition: border-color .2s, background .2s;
}
.rc[aria-pressed="true"] {
  border-color: var(--c);
  background: color-mix(in srgb, var(--c) 6%, white);
}
.rc .nm {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
}
.rc .nm img {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  flex: none;
}
.rc .pc {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}
.rc .pc b {
  font: 600 24px/1 var(--display);
  font-variant-numeric: tabular-nums;
}
.rc .tag {
  font-size: 11.5px;
  font-weight: 500;
  border-radius: 6px;
  padding: 2px 7px;
  background: #F7F8FB;
  color: #4A5068;
}
.rc .tag.lead {
  background: #EEEFFD;
  color: #2B2FD9;
}
.rc .rbar {
  display: block;
  height: 5px;
  border-radius: 5px;
  background: #EEF0F5;
  overflow: hidden;
}
.rc .rbar i {
  display: block;
  height: 100%;
  width: 0;
  background: var(--c);
  border-radius: 5px;
  transition: width .3s ease-out;
}
.rc.standby {
  background: #F7F8FB;
}
.rc.standby img {
  filter: grayscale(.8) opacity(.6);
}
.rc.standby .pc b {
  color: #6B7189;
}

/* ---------- Specialist Agents Card & Table ---------- */
.ch {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 18px 0;
}
.ch h2 {
  margin: 0;
  font: 600 16px var(--display);
  letter-spacing: -.01em;
}
.stage {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 12.5px;
  color: var(--mute);
}
.stage .segs {
  display: inline-flex;
  gap: 3px;
}
.stage .segs i {
  display: block;
  width: 14px;
  height: 4px;
  border-radius: 2px;
  background: var(--hair);
  transition: background .2s;
}
.stage .segs i.on { background: var(--indigo); }

.controls-wrap {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.btn-primary-control {
  height: 32px;
  padding: 0 12px;
  border-radius: 8px;
  border: none;
  background: var(--indigo);
  color: var(--white);
  font: 600 12.5px var(--body);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  transition: all .15s;
}
.btn-primary-control:hover { background: var(--indigo-600); }
.btn-primary-control svg { width: 14px; height: 14px; }
.btn-replay-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 1px solid var(--hair);
  background: var(--white);
  color: var(--graphite);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
.btn-replay-icon:hover { background: var(--paper); border-color: #CBD5E1; }
.btn-replay-icon svg { width: 14px; height: 14px; }

/* The Circular Room */
.room {
  position: relative;
  aspect-ratio: 1.55 / 1;
  min-height: 440px;
  margin: 6px 12px 0;
}
.room canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
.board {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: min(290px, 58%);
  padding: 14px 16px;
  background: var(--white);
  border: 1px solid var(--hair);
  border-radius: 14px;
  box-shadow: 0 4px 18px rgba(15,18,34,.06);
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 4px;
  z-index: 2;
  transition: all .25s var(--ease);
}
.board b {
  font: 600 13px var(--display);
  color: var(--ink);
  display: block;
}
.board p {
  margin: 0;
  font-size: 12.5px;
  color: var(--graphite);
  line-height: 1.4;
}

/* Agent Node button on circle */
.node {
  position: absolute;
  width: 90px;
  transform: translate(-50%, -22px);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  cursor: pointer;
  z-index: 3;
  padding: 0;
  transition: opacity .2s, transform .2s;
}
.node.dim { opacity: .35; }
.node .av {
  position: relative;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: 2px solid var(--c);
  background: var(--white);
  box-shadow: 0 2px 8px rgba(15,18,34,.08);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform .2s, box-shadow .2s;
}
.node:hover .av { transform: scale(1.08); box-shadow: 0 4px 14px rgba(15,18,34,.14); }
.node .av-face {
  position: relative;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  overflow: hidden;
}
.node.standby .av-face { filter: grayscale(.75) opacity(.6); }
.node.speaking .av {
  transform: scale(1.12);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--c) 25%, transparent), 0 6px 18px rgba(15,18,34,.16);
}
.node.thinking .av {
  animation: pulse-node 1.2s infinite alternate;
}
@keyframes pulse-node {
  0% { transform: scale(1); }
  100% { transform: scale(1.08); box-shadow: 0 0 0 4px color-mix(in srgb, var(--c) 30%, transparent); }
}
.node .lbl {
  font: 600 12px var(--body);
  color: var(--ink);
  text-align: center;
  white-space: nowrap;
}
.node .st {
  font-size: 10.5px;
  font-weight: 500;
  color: var(--mute);
  text-align: center;
  white-space: nowrap;
}
.node.speaking .st, .node.thinking .st { color: var(--c); }
.node.agreed .st { color: var(--verdant); }
.node.sel .av { border-width: 3px; transform: scale(1.1); }

.routed-footer {
  font-size: 11.5px;
  color: var(--mute);
  padding: 6px 18px 14px;
  margin: 0;
}

/* ---------- Decision Panel (Right Column) ---------- */
.decision {
  display: flex;
  flex-direction: column;
  min-height: 100%;
  max-height: calc(100vh - 32px);
  position: sticky;
  top: 16px;
}
.decision .pane {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  scrollbar-width: thin;
}
.seg {
  display: inline-flex;
  gap: 2px;
  background: var(--paper);
  padding: 3px;
  border-radius: 9px;
  border: 1px solid var(--hair-2);
}
.seg button {
  padding: 5px 12px;
  border-radius: 7px;
  border: none;
  background: none;
  font: 600 12px var(--body);
  color: var(--graphite);
  cursor: pointer;
  transition: all .15s;
}
.seg button[aria-selected="true"] {
  background: var(--white);
  color: var(--ink);
  box-shadow: 0 1px 3px rgba(15,18,34,.08);
}
.seg button em {
  font-style: normal;
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 999px;
  background: var(--hair);
  margin-left: 3px;
}
.seg button em.has-unread {
  background: var(--indigo);
  color: var(--white);
}

/* Draft Content & Empty State */
.draft-empty {
  padding: 32px 12px;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 14px;
  align-items: center;
}
.draft-empty p {
  margin: 0;
  font-size: 13px;
  color: var(--mute);
  max-width: 260px;
  line-height: 1.45;
}
.draft-empty-outline {
  width: 100%;
  border: 1.5px dashed #CBD5E1;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  opacity: 0.6;
}
.draft-empty-line {
  height: 10px;
  border-radius: 5px;
  background: var(--hair);
}

.dx-l {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .05em;
  color: var(--mute);
}
.dx {
  margin: 0;
  font: 700 19px/1.25 var(--display);
  color: var(--ink);
  letter-spacing: -.01em;
}
.conf {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--graphite);
}
.conf .t {
  flex: 1;
  height: 6px;
  background: var(--hair-2);
  border-radius: 3px;
  overflow: hidden;
}
.conf .t i {
  display: block;
  height: 100%;
  background: var(--verdant);
  border-radius: 3px;
  transition: width .3s;
}
.conf b { font-weight: 600; color: var(--ink); }

.note {
  font-size: 12px;
  line-height: 1.45;
  color: var(--graphite);
  margin: 0;
}
.note b { color: var(--ink); }

.plan-h {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .05em;
  color: var(--mute);
  margin-top: 4px;
}
.plan-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.plan-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 12px;
  line-height: 1.4;
  color: var(--graphite);
  padding: 8px 10px;
  border-radius: 9px;
  background: var(--paper);
  border: 1px solid var(--hair-2);
  transition: all .2s;
}
.plan-item.agreed {
  border-color: #BFE6D2;
  background: #F4FAF7;
}
.plan-item input[type="checkbox"] {
  margin-top: 2px;
  accent-color: var(--verdant);
}
.plan-item .owners {
  display: inline-flex;
  gap: 3px;
  margin-right: 4px;
}
.plan-item .own-pill {
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 1px 4px;
  border-radius: 4px;
  background: var(--hair);
  color: var(--graphite);
}

.sign-box {
  padding: 12px 18px 16px;
  border-top: 1px solid var(--hair-2);
  background: var(--white);
  border-radius: 0 0 16px 16px;
}
.btn-sign {
  width: 100%;
  height: 40px;
  border-radius: 10px;
  background: var(--ink);
  color: var(--white);
  border: none;
  font: 600 13px var(--body);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  cursor: pointer;
  transition: all .2s;
}
.btn-sign:hover:not(:disabled) { background: #232738; }
.btn-sign:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Discussion Pane & Messages */
.disc-empty {
  padding: 40px 12px;
  text-align: center;
  font-size: 13px;
  color: var(--mute);
}
.filter-chip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  background: var(--indigo-50);
  border-radius: 8px;
  font-size: 11.5px;
  color: var(--indigo);
  margin-bottom: 8px;
}
.filter-chip button {
  background: none;
  border: none;
  font-size: 11px;
  font-weight: 600;
  color: var(--indigo);
  cursor: pointer;
}
.msg {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 9px 11px;
  border-radius: 10px;
  background: var(--paper);
  border: 1px solid var(--hair-2);
  font-size: 12px;
  line-height: 1.45;
}
.msg-hdr {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
}
.msg-who {
  display: flex;
  align-items: center;
  gap: 5px;
  font-weight: 700;
  color: var(--ink);
}
.msg-who img {
  width: 16px;
  height: 16px;
  border-radius: 50%;
}
.msg-cite {
  font-size: 10px;
  color: var(--mute);
  font-style: italic;
}

/* Responsive */
@media (max-width: 1280px) {
  .case-room { grid-template-columns: minmax(0, 1fr); }
  .dossier { position: static; max-height: none; }
}
@media (max-width: 1080px) {
  .case-body { grid-template-columns: minmax(0, 1fr); }
  .decision { position: static; max-height: none; }
}
@media (max-width: 640px) {
  .rcols { grid-auto-flow: row; grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
}
'''
