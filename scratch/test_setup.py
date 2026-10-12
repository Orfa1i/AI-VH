# -*- coding: utf-8 -*-
import json
import os

with open('frontend/public/case-room.html', 'r', encoding='utf-8') as f_orig:
    orig = f_orig.read()

av_idx = orig.find('const AV = {')
avsvg_idx = orig.find('const AVSVG = {')
dollar_idx = orig.find('const $ = s =>')

av_str = orig[av_idx:avsvg_idx].strip()
avsvg_str = orig[avsvg_idx:dollar_idx].strip()

html_content = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Virtual Hospital Case Room - Multidisciplinary AI Triage</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Funnel+Display:wght@500;600;700&family=Host+Grotesk:wght@400;500;600;700&display=swap">
<style>
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
  --display: "Funnel Display", "Host Grotesk", -apple-system, BlinkMacSystemFont, sans-serif;
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

/* ---------- Main Layout ---------- */
.app-layout {
  display: grid;
  grid-template-columns: 370px minmax(0, 1fr);
  gap: 16px;
  width: min(1680px, calc(100% - 32px));
  margin: 16px auto 32px;
  align-items: start;
}

/* ---------- Left Sidebar: Case Dossier ---------- */
.case-sidebar {
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
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--hair-2);
  padding-bottom: 12px;
}
.sidebar-header h2 {
  margin: 0;
  font: 600 15px var(--display);
  color: var(--ink);
  display: flex;
  align-items: center;
  gap: 8px;
}
.sidebar-header .live-badge {
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
.sidebar-header .live-badge::before {
  content: "";
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--verdant);
  animation: pulse-dot 1.8s infinite;
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.85); }
}

.case-select-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
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
  padding: 10px 12px;
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

.action-row {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}
.btn-triage {
  width: 100%;
  height: 42px;
  border-radius: 10px;
  background: var(--indigo);
  color: var(--white);
  border: none;
  font: 600 14px var(--body);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  transition: all .2s;
  box-shadow: 0 3px 12px rgba(43,47,217,.28);
}
.btn-triage:hover:not(:disabled) {
  background: var(--indigo-600);
  transform: translateY(-1px);
}
.btn-triage:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}
.btn-triage svg { width: 16px; height: 16px; }

.toggles-panel {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  background: var(--paper);
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid var(--hair-2);
}
.toggle-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 500;
  color: var(--graphite);
  cursor: pointer;
  user-select: none;
}
.toggle-btn input[type="checkbox"] {
  width: 15px;
  height: 15px;
  accent-color: var(--indigo);
  cursor: pointer;
}
.audio-wave {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  height: 12px;
}
.audio-wave span {
  display: inline-block;
  width: 2.5px;
  height: 4px;
  background: var(--indigo);
  border-radius: 2px;
  transition: height .2s;
}
.audio-wave.active span {
  animation: wave-bar 0.9s infinite alternate;
}
.audio-wave.active span:nth-child(1) { animation-delay: 0.1s; }
.audio-wave.active span:nth-child(2) { animation-delay: 0.3s; }
.audio-wave.active span:nth-child(3) { animation-delay: 0.2s; }
.audio-wave.active span:nth-child(4) { animation-delay: 0.4s; }
@keyframes wave-bar {
  0% { height: 3px; }
  100% { height: 12px; }
}

/* Patient summary card */
.patient-card {
  background: var(--paper);
  border: 1px solid var(--hair-2);
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.patient-card-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}
.patient-card-name {
  font: 700 16px var(--display);
  color: var(--ink);
}
.patient-card-mrn {
  font-size: 11px;
  font-family: monospace;
  color: var(--mute);
}
.patient-card-sub {
  font-size: 12px;
  color: var(--graphite);
  display: flex;
  align-items: center;
  gap: 6px;
}
.patient-card-sub .badge-acuity {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  text-transform: uppercase;
}
.badge-esi1 { background: var(--crit-50); color: var(--crit); border: 1px solid #F1C7CF; }
.badge-esi2 { background: var(--warn-50); color: var(--warn); border: 1px solid #F6D7A8; }

/* Clinical details */
.dossier-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.dossier-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .05em;
  color: var(--mute);
}
.dossier-box {
  background: var(--white);
  border: 1px solid var(--hair);
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 12.5px;
  line-height: 1.45;
  color: var(--ink);
}
.dossier-box.hpi {
  color: var(--graphite);
  font-size: 12px;
  background: #FCFCFD;
}

/* Vitals grid */
.vitals-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
}
.v-pill {
  padding: 8px 10px;
  border-radius: 8px;
  background: var(--white);
  border: 1px solid var(--hair);
  display: flex;
  flex-direction: column;
}
.v-pill .v-lbl {
  font-size: 10px;
  text-transform: uppercase;
  color: var(--mute);
  font-weight: 600;
}
.v-pill .v-val {
  font-size: 13.5px;
  font-weight: 700;
  color: var(--ink);
  font-variant-numeric: tabular-nums;
}
.v-pill.crit {
  background: var(--crit-50);
  border-color: #F1C7CF;
}
.v-pill.crit .v-val {
  color: var(--crit);
}
.v-pill.warn {
  background: var(--warn-50);
  border-color: #F6D7A8;
}
.v-pill.warn .v-val {
  color: var(--warn);
}

/* Labs compact list */
.labs-container {
  border: 1px solid var(--hair);
  border-radius: 10px;
  background: var(--white);
  max-height: 130px;
  overflow-y: auto;
  padding: 6px 10px;
}
.lab-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 3px 0;
  border-bottom: 1px solid var(--hair-2);
  font-size: 11.5px;
}
.lab-row:last-child { border-bottom: 0; }
.lab-row .lab-name { color: var(--graphite); }
.lab-row .lab-val-wrap { display: flex; align-items: center; gap: 6px; }
.lab-row .lab-val { font-weight: 600; font-variant-numeric: tabular-nums; }
.lab-tag {
  font-size: 9px;
  font-weight: 700;
  padding: 1px 4px;
  border-radius: 3px;
  text-transform: uppercase;
}
.lab-tag.hi { background: var(--crit-50); color: var(--crit); }
.lab-tag.lo { background: #EFF6FF; color: #1D4ED8; }
.lab-tag.norm { background: var(--verdant-50); color: var(--verdant); }

/* Imaging thumbnails */
.imaging-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.img-card {
  border: 1px solid var(--hair);
  border-radius: 10px;
  padding: 8px;
  background: #0F1222;
  color: #fff;
  cursor: pointer;
  transition: all .2s;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.img-card:hover {
  border-color: var(--indigo);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(15,18,34,.18);
}
.img-card-preview {
  height: 48px;
  border-radius: 6px;
  background: #1C2237;
  display: flex;
  align-items: center;
  justify-content: center;
}
.img-card-preview svg { width: 22px; height: 22px; color: #94A3B8; }
.img-card-title {
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.img-card-badge {
  font-size: 9.5px;
  color: #94A3B8;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* ---------- Workspace (Right) ---------- */
.case-workspace {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

/* Router Top Card */
.card {
  background: var(--white);
  border: 1px solid var(--hair);
  border-radius: 16px;
  box-shadow: var(--shadow);
  min-width: 0;
}
.router {
  padding: 14px 18px 16px;
}
.router .rh {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.router-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}
.router-brand img {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: var(--paper);
  padding: 3px;
  border: 1px solid var(--hair);
}
.router-brand h2 {
  margin: 0;
  font: 600 16px var(--display);
  letter-spacing: -.01em;
  color: var(--ink);
}
.router-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 5px 12px;
  border-radius: 999px;
  background: var(--paper);
  border: 1px solid var(--hair);
  font-size: 12.5px;
  color: var(--graphite);
}
.router-status-pill .status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--indigo);
  box-shadow: 0 0 0 2px var(--indigo-50);
}
.router-status-pill.active .status-dot {
  background: var(--verdant);
  box-shadow: 0 0 0 2px var(--verdant-50);
}

/* Router Cards Grid (NO PERCENTAGES) */
.rcols {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 10px;
}
.rc {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1.5px solid var(--hair);
  background: var(--white);
  text-align: left;
  cursor: pointer;
  transition: border-color .2s, background .2s, box-shadow .2s;
  position: relative;
}
.rc:hover {
  border-color: #CBD5E1;
}
.rc[aria-pressed="true"] {
  border-color: var(--c);
  background: color-mix(in srgb, var(--c) 6%, white);
}
.rc.lead {
  border-color: var(--c);
  background: color-mix(in srgb, var(--c) 4%, white);
  box-shadow: 0 2px 8px color-mix(in srgb, var(--c) 15%, transparent);
}
.rc.consult {
  border-color: #10B981;
  background: #F0FDF4;
}
.rc.standby {
  background: var(--paper);
  border-color: var(--hair-2);
  opacity: 0.75;
}
.rc.standby .nm img {
  filter: grayscale(.8) opacity(.6);
}
.rc .nm {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.rc .nm img {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  flex: none;
}
.rc .nm-info {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.rc .nm-title {
  font: 600 12.5px var(--body);
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.rc .nm-doc {
  font-size: 11px;
  color: var(--mute);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.rc .rc-badge-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 2px;
}
.rc .tag {
  font-size: 10.5px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .03em;
  border-radius: 6px;
  padding: 2px 6px;
  background: var(--paper);
  color: var(--graphite);
}
.rc .tag.lead {
  background: var(--indigo-50);
  color: var(--indigo);
  border: 1px solid #C7D2FE;
}
.rc .tag.consult {
  background: var(--verdant-50);
  color: var(--verdant);
  border: 1px solid #A7F3D0;
}
.rc .tag.assigned {
  background: #F1F5F9;
  color: #334155;
}
.rc .tag.standby {
  background: #F8FAFC;
  color: #94A3B8;
}
.rc .rc-book {
  font-size: 10px;
  color: var(--mute);
  font-style: italic;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Two-column Body: Round Table & Draft */
.body {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(360px, .85fr);
  gap: 16px;
  align-items: start;
}
.ch {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 18px 0;
  flex-wrap: wrap;
}
.ch h2 {
  margin: 0;
  font: 600 16px var(--display);
  letter-spacing: -.01em;
}
.stage {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--graphite);
}
.segs { display: flex; gap: 3px; }
.segs i { width: 22px; height: 4px; border-radius: 4px; background: var(--hair); transition: background .4s; }
.segs i.on { background: var(--indigo); }
.segs i.done { background: var(--verdant); }
.play { display: flex; align-items: center; gap: 6px; }
.ib {
  width: 32px;
  height: 32px;
  border-radius: 9px;
  border: 1px solid var(--hair);
  background: var(--white);
  display: grid;
  place-items: center;
  cursor: pointer;
  color: var(--graphite);
  transition: all .15s;
}
.ib:hover { color: var(--ink); background: var(--paper); }
.ib svg { width: 14px; height: 14px; }

/* Round Table Canvas & Nodes */
.room {
  position: relative;
  margin: 8px 14px 0;
  aspect-ratio: 760 / 520;
  max-width: calc(100% - 28px);
}
.room canvas { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }
.node {
  position: absolute;
  transform: translate(-50%, -32px);
  display: grid;
  justify-items: center;
  gap: 4px;
  background: none;
  border: 0;
  padding: 0;
  cursor: pointer;
  width: 140px;
  z-index: 2;
}
.node .av {
  position: relative;
  width: 64px;
  height: 64px;
  margin-bottom: 8px;
  animation: bob 4.4s ease-in-out infinite;
  animation-delay: var(--d, 0s);
}
.node .face {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  display: block;
  position: relative;
  z-index: 1;
  box-shadow: 0 6px 16px rgba(31,36,90,.14);
  transition: transform .45s var(--ease), filter .4s, box-shadow .4s;
  overflow: hidden;
}
.node .face svg { width: 100%; height: 100%; display: block; }
.face .eye, .face .mouth, .face .talk, .face .hd, .face .nn, .face .led, .face .cheek, .face .pod, .face .beam {
  transform-box: fill-box;
  transform-origin: center;
}
.face .eyes { transform: translate(var(--gx, 0px), var(--gy, 0px)); transition: transform .5s var(--ease); }
.face .eye { animation: blink 5.6s infinite; animation-delay: var(--bd, 0s); }
.face .led { animation: led 2.8s ease-in-out infinite; animation-delay: var(--d, 0s); }
.face .trace { stroke-dasharray: 260; animation: trace 2.6s linear infinite; }
.face .nn { animation: nn 2.4s ease-in-out infinite; }
.face .nn:nth-of-type(2) { animation-delay: .3s; }
.face .nn:nth-of-type(3) { animation-delay: .6s; }
.face .beam { animation: beam 3.2s ease-in-out infinite; }
.face .mouth, .face .talk, .face .cheek { transition: transform .35s var(--ease), opacity .25s; }
.face .hd { transition: transform .5s var(--ease); }

@keyframes bob { 50% { transform: translateY(-5px); } }
@keyframes blink { 0%, 93%, 100% { transform: scaleY(1); } 95.5% { transform: scaleY(.08); } }
@keyframes led { 50% { opacity: .35; } }
@keyframes trace { from { stroke-dashoffset: 520; } to { stroke-dashoffset: 0; } }
@keyframes nn { 50% { transform: scale(1.35); } }
@keyframes beam { 50% { transform: scale(1.25); opacity: .2; } }

.node.thinking .face .eyes { animation: look 2.6s ease-in-out infinite; }
.node.thinking .face .hd { animation: tilt 2.6s ease-in-out infinite; }
.node.thinking .face .mouth { transform: scale(.5, .2); }
.node.thinking .face .led { animation-duration: .45s; }
.node.thinking .face .trace { animation-duration: .9s; }
.node.thinking .av { animation-duration: 2.2s; }
.node .orbit {
  position: absolute;
  inset: -10px;
  border-radius: 50%;
  opacity: 0;
  transition: opacity .35s;
  animation: spin 2.8s linear infinite;
  pointer-events: none;
}
.node .orbit i {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 7px;
  height: 7px;
  margin: -3.5px;
  border-radius: 50%;
  background: var(--c);
  transform: rotate(var(--a)) translate(40px);
}
.node .orbit i:nth-child(2) { opacity: .6; width: 5px; height: 5px; margin: -2.5px; }
.node .orbit i:nth-child(3) { opacity: .35; width: 4px; height: 4px; margin: -2px; }
.node.thinking .orbit { opacity: 1; }

@keyframes look { 0%, 100% { transform: translate(0, 0); } 22% { transform: translate(-32px, -24px); } 50% { transform: translate(32px, -24px); } 74% { transform: translate(8px, -8px); } }
@keyframes tilt { 0%, 100% { transform: rotate(0); } 30% { transform: rotate(-5deg); } 70% { transform: rotate(4deg); } }

.node.speaking .face .mouth { opacity: 0; }
.node.speaking .face .talk { opacity: 1; animation: talk .34s ease-in-out infinite alternate; }
.node.speaking .face .pod { animation: led .5s ease-in-out infinite; }
.node.speaking .face { transform: scale(1.12); box-shadow: 0 10px 26px color-mix(in srgb, var(--c) 35%, transparent); }
.node.speaking .av { animation: none; }
@keyframes talk { from { transform: scale(.9, .3); } to { transform: scale(1, 1); } }

.node.hear .face { animation: perk .7s var(--ease); }
@keyframes perk { 35% { transform: translateY(-7px) scale(1.07); } }

.node.nod .face .hd { animation: nod .9s ease-in-out; }
@keyframes nod { 20%, 60% { transform: translateY(42px); } 40%, 80% { transform: translateY(0); } }
.node.agreed .face .cheek { transform: scale(1.25); opacity: .32; }
.node .ok {
  position: absolute;
  right: -4px;
  bottom: -2px;
  z-index: 2;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--verdant);
  border: 2px solid var(--white);
  display: grid;
  place-items: center;
  transform: scale(0);
  transition: transform .45s cubic-bezier(.3,1.6,.5,1);
}
.node .ok svg { width: 11px; height: 11px; }
.node.agreed .ok { transform: scale(1); }

.node.standby .face { filter: grayscale(.75) opacity(.6); box-shadow: none; }
.node.standby .face .eye { animation: none; transform: scaleY(.28); }
.node.standby .face .led { animation: led 6s ease-in-out infinite; }
.node.standby .av { animation-duration: 7s; }

.node .halo { position: absolute; inset: -9px; border-radius: 50%; border: 2px solid var(--c); opacity: 0; transition: opacity .3s; }
.node .spin {
  position: absolute;
  inset: -7px;
  border-radius: 50%;
  background: conic-gradient(from 0deg, transparent 0 62%, var(--c) 100%);
  -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - 3px), #000 calc(100% - 3px));
  mask: radial-gradient(farthest-side, transparent calc(100% - 3px), #000 calc(100% - 3px));
  opacity: 0;
  transition: opacity .3s;
  animation: spin 1.1s linear infinite;
}
.node .nm { font: 600 12.5px/1.2 var(--body); color: var(--ink); text-align: center; white-space: nowrap; }
.node .st {
  font: 500 11px/1 var(--body);
  color: var(--mute);
  white-space: nowrap;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color .3s;
}
.node.thinking .spin { opacity: 1; }
.node.thinking .st, .node.speaking .st { color: var(--c); }
.node.speaking .halo { opacity: .9; animation: ping 1.4s var(--ease) infinite; }
.node.agreed .st { color: var(--verdant); }
.node.standby .nm { color: var(--mute); }
.node.dim { opacity: .35; }
.node:hover .face { transform: scale(1.06); }
.node.sel .nm { text-decoration: underline; text-decoration-color: var(--c); text-underline-offset: 3px; }

@keyframes spin { to { transform: rotate(360deg); } }
@keyframes ping { 0% { transform: scale(.92); opacity: .9; } 100% { transform: scale(1.28); opacity: 0; } }

.board {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: min(44%, 300px);
  text-align: center;
  z-index: 1;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(255,255,255,.95);
  border: 1px solid var(--hair);
  box-shadow: 0 12px 30px rgba(31,36,90,.08);
  backdrop-filter: blur(8px);
}
.board b { display: block; font-size: 12px; color: var(--c, var(--mute)); font-weight: 700; margin-bottom: 2px; }
.board p { margin: 0; font-size: 14px; line-height: 1.4; color: var(--ink); text-wrap: balance; }
.board.fresh { animation: fresh .5s var(--ease); }
@keyframes fresh { from { opacity: .3; transform: translate(-50%, calc(-50% + 4px)); } }
.routed { padding: 4px 18px 16px; font-size: 12.5px; color: var(--mute); }

/* Right Panel: Decision Draft & Discussion */
.dec {
  position: sticky;
  top: 16px;
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 32px);
}
.seg {
  display: inline-flex;
  background: var(--paper);
  border-radius: 10px;
  padding: 3px;
  gap: 2px;
}
.seg button {
  height: 30px;
  padding: 0 14px;
  border: 0;
  border-radius: 8px;
  background: none;
  cursor: pointer;
  font-size: 13.5px;
  font-weight: 500;
  color: var(--graphite);
  display: inline-flex;
  align-items: center;
  gap: 7px;
}
.seg button[aria-selected="true"] {
  background: var(--white);
  color: var(--ink);
  box-shadow: 0 1px 3px rgba(15,18,34,.1);
}
.seg em {
  font-style: normal;
  font-size: 11.5px;
  min-width: 20px;
  height: 18px;
  padding: 0 6px;
  border-radius: 9px;
  background: var(--hair);
  color: var(--graphite);
  display: inline-grid;
  place-items: center;
}
.seg em.new { background: var(--indigo); color: #fff; }
.dec .ch { padding-bottom: 12px; border-bottom: 1px solid var(--hair-2); }
.pane { padding: 14px 18px 18px; overflow-y: auto; flex: 1; min-height: 0; }
.dx-l { font-size: 12px; font-weight: 600; text-transform: uppercase; color: var(--mute); letter-spacing: .05em; }
.dx { margin: 4px 0 10px; font: 600 21px/1.25 var(--display); letter-spacing: -.02em; color: var(--ink); }

.conf-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: var(--graphite);
  margin-bottom: 10px;
}
.conf-wrap .t {
  flex: 1;
  height: 6px;
  border-radius: 6px;
  background: var(--hair-2);
  overflow: hidden;
  max-width: 140px;
}
.conf-wrap .t i { display: block; height: 100%; background: var(--indigo); border-radius: 6px; transition: width 1s var(--ease); }
.conf-wrap b { color: var(--ink); font-variant-numeric: tabular-nums; }

/* Referral Banner in Draft */
.referral-banner {
  margin: 10px 0;
  background: #FFFBEB;
  border: 1px solid #FDE68A;
  border-radius: 10px;
  padding: 10px 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  animation: slidein .3s ease;
}
.referral-banner .ref-icon {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: #F59E0B;
  color: #fff;
  display: grid;
  place-items: center;
  flex: none;
}
.referral-banner .ref-icon svg { width: 14px; height: 14px; }
.referral-banner .ref-text { display: flex; flex-direction: column; font-size: 12px; }
.referral-banner .ref-text strong { color: #92400E; font-weight: 600; }
.referral-banner .ref-text span { color: #B45309; }

.note { margin: 10px 0 0; font-size: 13px; color: var(--graphite); }
.note b { color: var(--ink); font-weight: 600; }
.plan { list-style: none; margin: 16px 0 0; padding: 12px 0 0; border-top: 1px solid var(--hair); display: grid; gap: 8px; }
.plan-h { display: flex; justify-content: space-between; font-size: 12px; font-weight: 600; text-transform: uppercase; color: var(--mute); letter-spacing: .05em; margin-bottom: 2px; }
.step { display: grid; grid-template-columns: 20px minmax(0, 1fr); gap: 10px; font-size: 13.5px; line-height: 1.45; color: var(--ink); transition: opacity .4s; }
.step .ic { width: 20px; height: 20px; border-radius: 50%; display: grid; place-items: center; margin-top: 1px; border: 1.5px solid #C9CEDA; }
.step .ic svg { width: 11px; height: 11px; }
.step.agreed .ic { background: var(--verdant); border-color: var(--verdant); color: #fff; }
.step.discussing .ic { border-color: var(--warn); background: var(--warn-50); }
.step.discussing .ic::after { content: ""; width: 6px; height: 6px; border-radius: 50%; background: var(--warn); }
.step.pending { opacity: .4; }
.step small { display: block; color: var(--warn); font-size: 11.5px; font-weight: 600; }
.step b { font-weight: 600; }

.foot-act {
  border-top: 1px solid var(--hair);
  padding: 14px 18px;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.sign {
  height: 42px;
  padding: 0 20px;
  border-radius: 10px;
  border: 0;
  background: var(--indigo);
  color: #fff;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all .2s;
  box-shadow: 0 4px 12px rgba(43,47,217,.25);
}
.sign:disabled {
  background: #E7E9F1;
  color: var(--mute);
  cursor: not-allowed;
  box-shadow: none;
}
.sign:not(:disabled):hover { background: var(--indigo-600); }
.foot-act span { font-size: 12.5px; color: var(--mute); }

/* Discussion Pane */
.filter { display: flex; align-items: center; gap: 8px; font-size: 12.5px; color: var(--graphite); margin-bottom: 6px; }
.filter button { border: 0; background: none; color: var(--indigo); font-weight: 600; cursor: pointer; padding: 0; }
.msg { display: grid; grid-template-columns: 30px minmax(0, 1fr); gap: 10px; padding: 12px 0; border-bottom: 1px solid var(--hair-2); animation: msgin .4s var(--ease); }
.msg:last-child { border-bottom: 0; }
.msg > img { width: 30px; height: 30px; border-radius: 50%; }
.msg header { display: flex; flex-wrap: wrap; align-items: baseline; gap: 2px 8px; font-size: 13px; }
.msg header b { font-weight: 600; color: var(--c); }
.msg header span { color: var(--mute); }
.msg header .chal { color: var(--crit); font-weight: 600; }
.msg header .agr { color: var(--verdant); font-weight: 600; }
.msg header .ref { color: var(--amber); font-weight: 600; }
.msg p { margin: 3px 0 0; font-size: 13.5px; line-height: 1.5; color: var(--ink); }
.msg .src { margin-top: 4px; font-size: 11.5px; color: var(--mute); font-style: italic; }
.msg.sys > img { padding: 4px; background: var(--paper); }
.msg.sys p { color: var(--graphite); }
@keyframes msgin { from { opacity: 0; transform: translateY(6px); } }

.typing { display: flex; align-items: center; gap: 8px; padding: 8px 0 0; font-size: 12.5px; color: var(--mute); min-height: 30px; }
.typing img { width: 20px; height: 20px; border-radius: 50%; }
.typing .dots { display: inline-flex; gap: 3px; }
.typing .dots i { width: 4px; height: 4px; border-radius: 50%; background: var(--c, var(--mute)); animation: blinkd 1.2s infinite; }
.typing .dots i:nth-child(2) { animation-delay: .15s; }
.typing .dots i:nth-child(3) { animation-delay: .3s; }
@keyframes blinkd { 0%, 80%, 100% { opacity: .25; } 40% { opacity: 1; } }

/* Lightbox Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15,18,34,.65);
  backdrop-filter: blur(4px);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.modal-content {
  background: var(--white);
  border-radius: 16px;
  width: min(640px, 100%);
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
}
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--hair);
}
.modal-header h3 { margin: 0; font: 600 16px var(--display); color: var(--ink); }
.modal-close { background: none; border: 0; font-size: 22px; color: var(--mute); cursor: pointer; line-height: 1; }
.modal-close:hover { color: var(--ink); }
.modal-body { padding: 20px; display: flex; flex-direction: column; gap: 14px; }
.modal-visual-frame {
  background: #0B0F19;
  border-radius: 12px;
  padding: 16px;
  min-height: 220px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}
.modal-report-box {
  background: var(--paper);
  border: 1px solid var(--hair-2);
  border-radius: 10px;
  padding: 14px;
  font-size: 13px;
  line-height: 1.5;
  color: var(--ink);
}
.modal-report-box h4 {
  margin: 0 0 6px;
  font-size: 12px;
  text-transform: uppercase;
  color: var(--mute);
  letter-spacing: .05em;
}

/* Toast */
.toast {
  position: fixed;
  left: 50%;
  bottom: calc(env(safe-area-inset-bottom, 0px) + 20px);
  transform: translate(-50%, 20px);
  background: var(--ink);
  color: #fff;
  padding: 10px 18px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
  opacity: 0;
  pointer-events: none;
  transition: all .3s var(--ease);
  z-index: 120;
}
.toast.on { opacity: 1; transform: translate(-50%, 0); }

@media (max-width: 1280px) {
  .app-layout { grid-template-columns: 330px minmax(0, 1fr); }
  .body { grid-template-columns: minmax(0, 1fr); }
  .dec { position: static; max-height: none; }
  .pane { max-height: 520px; }
}
@media (max-width: 900px) {
  .app-layout { grid-template-columns: 1fr; }
  .case-sidebar { position: static; max-height: none; }
  .rcols { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
}
</style>
</head>
<body>

<main id="case" class="app-layout">
  <!-- LEFT SIDEBAR: CASE DOSSIER -->
  <aside class="case-sidebar" id="case-sidebar" aria-label="Patient Case Dossier">
    <div class="sidebar-header">
      <h2>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:18px;height:18px;color:var(--indigo)"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
        Clinical Dossier
      </h2>
      <span class="live-badge">Live Case</span>
    </div>

    <!-- Case Selector -->
    <div class="case-select-group">
      <label for="case-select">Select Patient Case</label>
      <select id="case-select" class="case-select"></select>
    </div>

    <!-- Actions & Toggles -->
    <div class="action-row">
      <button class="btn-triage" id="b-start-triage" type="button">
        <svg viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
        <span>Start Triage</span>
      </button>
      <div class="toggles-panel">
        <label class="toggle-btn" title="Automatically route when selecting a case">
          <input type="checkbox" id="toggle-auto" checked>
          <span>Auto-Triage</span>
        </label>
        <label class="toggle-btn" title="Synthesize brief voice updates from specialists (Fish Audio)">
          <input type="checkbox" id="toggle-voice" checked>
          <span>Voice Audio</span>
          <span class="audio-wave" id="audio-wave-icon">
            <span></span><span></span><span></span><span></span>
          </span>
        </label>
      </div>
    </div>

    <!-- Patient Header Card -->
    <div class="patient-card">
      <div class="patient-card-header">
        <span class="patient-card-name" id="pt-name">Elena Vance</span>
        <span class="patient-card-mrn" id="pt-mrn">#VH-8921-OB</span>
      </div>
      <div class="patient-card-sub">
        <span id="pt-demog">32F · G2P1 (34+2 wks)</span>
        <span class="badge-acuity badge-esi1" id="pt-acuity">ESI 1 · Resuscitation</span>
      </div>
    </div>

    <!-- Chief Complaint -->
    <div class="dossier-section">
      <span class="dossier-title">Chief Complaint</span>
      <div class="dossier-box" id="pt-cc">
        Severe throbbing headache, blurred vision, right upper quadrant pain.
      </div>
    </div>

    <!-- HPI -->
    <div class="dossier-section">
      <span class="dossier-title">History of Present Illness</span>
      <div class="dossier-box hpi" id="pt-hpi">
        32-year-old female at 34+2 weeks gestation presenting with acute-onset severe headache unresponsive to acetaminophen, scotomas, and worsening RUQ pain over the past 6 hours.
      </div>
    </div>

    <!-- Vitals -->
    <div class="dossier-section">
      <span class="dossier-title">Vital Signs</span>
      <div class="vitals-grid" id="vitals-grid">
        <!-- Rendered dynamically -->
      </div>
    </div>

    <!-- Key Labs -->
    <div class="dossier-section">
      <span class="dossier-title">Diagnostic Labs</span>
      <div class="labs-container" id="labs-list">
        <!-- Rendered dynamically -->
      </div>
    </div>

    <!-- Imaging Studies -->
    <div class="dossier-section">
      <span class="dossier-title">Imaging & Studies</span>
      <div class="imaging-container" id="imaging-list">
        <!-- Rendered dynamically -->
      </div>
    </div>
  </aside>

  <!-- RIGHT COLUMN: WORKSPACE -->
  <div class="case-workspace">
    <!-- ROUTER SECTION (NO PERCENTAGES) -->
    <section class="card router" aria-label="MedGemma routing">
      <div class="rh">
        <div class="router-brand">
          <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIGFyaWEtbGFiZWw9IlZpcnR1YWwgSG9zcGl0YWwgc3ltYm9sIiB2aWV3Qm94PSIyNiAyIDE4OCAyMzYiIHdpZHRoPSIxODgiIGhlaWdodD0iMjM2IiB4bWxuczpjMnBhPSJodHRwOi8vYzJwYS5vcmcvbWFuaWZlc3QiPjxtZXRhZGF0YT48YzJwYTptYW5pZmVzdD5BQUFXZ21wMWJXSUFBQUFlYW5WdFpHTXljR0VBRVFBUWdBQUFxZ0E0bTNFRFl6SndZUUFBQUJaY2FuVnRZZ0FBQUVkcWRXMWtZekp0WVFBUkFCQ0FBQUNxQURpYmNRTjFjbTQ2WXpKd1lUbzJZamd3Wm1KaU9DMW1NbVV6TFRSaVpqZ3RZVEl4TUMwNFpUQTRPRFl5WldNek1Ea0FBQUFEbDJwMWJXSUFBQUFwYW5WdFpHTXlZWE1BRVFBUWdBQUFxZ0E0bTNFRFl6SndZUzVoYzNObGNuUnBiMjV6QUFBQUFMeHFkVzFpQUFBQVJHcDFiV1JqWW05eUFCRUFFSUFBQUtvQU9KdHhFMk15Y0dFdWFXNW5jbVZrYVdWdWRDNTJNd0FBQUFBWVl6SnphQlNLeWhQSTBSNndSYUp1YTcrelo3TUFBQUJ3WTJKdmNxTnBaR002Wm05eWJXRjBiV2x0WVdkbEwzTjJaeXQ0Yld4cWFXNXpkR0Z1WTJWSlJIZ3NlRzF3T21scFpEbzBPR1prTnpZd05DMHdPVFkyTFRSaE1qVXRPR1ZsTXkwME16RXpaR1F3WkdNeE5tVnNjbVZzWVhScGIyNXphR2x3YUhCaGNtVnVkRTltQUFBQjRtcDFiV0lBQUFCQmFuVnRaR05pYjNJQUVRQVFnQUFBcWdBNG0zRVRZekp3WVM1aFkzUnBiMjV6TG5ZeUFBQUFBQmhqTW5Ob3plTnN1VkRRZGZTcDUyT25lSFFOQWdBQUFabGpZbTl5b21kaFkzUnBiMjV6Z3FKbVlXTjBhVzl1YTJNeWNHRXViM0JsYm1Wa2FuQmhjbUZ0WlhSbGNuT2hhMmx1WjNKbFpHbGxiblJ6Z2FKamRYSnNlQzF6Wld4bUkycDFiV0ptUFdNeWNHRXVZWE56WlhKMGFXOXVjeTlqTW5CaExtbHVaM0psWkdsbGJuUXVkak5rYUdGemFGZ2djTnVtVmRGRC9PMExIRW43S2lrRXNoNDRWQUlQZVd6NDlRaFNiTDZ0RHdDa1ptRmpkR2x2Ym5nZFkyOXRMbUZ1ZEdoeWIzQnBZeTVqYkdGMVpHVXVjSEp2ZG1sa1pXUnFjR0Z5WVcxbGRHVnljNkY0SDJOdmJTNWhiblJvY205d2FXTXViM0pwWjJsdUxXTnZibVpwWkdWdVkyVm5kVzVyYm05M2JtdGtaWE5qY21sd2RHbHZibmhtUTJ4aGRXUmxJSEJ5YjNacFpHVmtJSFJvYVhNZ1ptbHNaU0JoZENCMGFHVWdjbVZ4ZFdWemRDQnZaaUJoSUhWelpYSWdZVzVrSUcxaGVTQm9ZWFpsSUdOeVpXRjBaV1FnYjNJZ2JXOWthV1pwWldRZ2RHaGxJR1pwYkdVZ1kyOXVkR1Z1ZEhNdWJYTnZablIzWVhKbFFXZGxiblNoWkc1aGJXVm1RMnhoZFdSbGNtRnNiRUZqZEdsdmJuTkpibU5zZFdSbFpQVUFBQURJYW5WdFlnQUFBRUJxZFcxa1kySnZjZ0FSQUJDQUFBQ3FBRGliY1JOak1uQmhMbWhoYzJndVpHRjBZUUFBQUFBWVl6SnphTDM0M3Y4NW1OT2NGNFJpS1JZUHEwd0FBQUNBWTJKdmNxVmpZV3huWm5Ob1lUSTFObU53WVdSTkFBQUFBQUFBQUFBQUFBQUFBR1JvWVhOb1dDQUhhTm9OS1NrUlg1aVJNT2kxeXBoV2RjR21rWnA0SVU2L0JqZmN1ajZzcW1SdVlXMWxibXAxYldKbUlHMWhibWxtWlhOMGFtVjRZMngxYzJsdmJuT0JvbVZ6ZEdGeWRCaThabXhsYm1kMGFCa2VCQUFBQWo1cWRXMWlBQUFBSjJwMWJXUmpNbU5zQUJFQUVJQUFBS29BT0p0eEEyTXljR0V1WTJ4aGFXMHVkaklBQUFBQ0QyTmliM0tsWTJGc1oyWnphR0V5TlRacGMybG5ibUYwZFhKbGVFMXpaV3htSTJwMWJXSm1QUzlqTW5CaEwzVnlianBqTW5CaE9qWmlPREJtWW1JNExXWXlaVE10TkdKbU9DMWhNakV3TFRobE1EZzROakpsWXpNd09TOWpNbkJoTG5OcFoyNWhkSFZ5WldwcGJuTjBZVzVqWlVsRWVDeDRiWEE2YVdsa09qYzNNalEzWWpoaExUTmpOVEl0TkRJMVl5MWlOamswTFdWa05XRXhaR1psWWpjd09ISmpjbVZoZEdWa1gyRnpjMlZ5ZEdsdmJuT0RvbU4xY214NExYTmxiR1lqYW5WdFltWTlZekp3WVM1aGMzTmxjblJwYjI1ekwyTXljR0V1YVc1bmNtVmthV1Z1ZEM1Mk0yUm9ZWE5vV0NCdzI2WlYwVVA4N1FzY1Nmc3FLUVN5SGpoVUFnOTViUGoxQ0ZKc3ZxMFBBS0pqZFhKc2VDcHpaV3htSTJwMWJXSm1QV015Y0dFdVlYTnpaWEowYVc5dWN5OWpNbkJoTG1GamRHbHZibk11ZGpKa2FHRnphRmdnTFVWK2dBTS9xOEZxYWZ5THZOM0dOZ09ETEhmakxuVUpvemRLd3dSRTBjeWlZM1Z5YkhncGMyVnNaaU5xZFcxaVpqMWpNbkJoTG1GemMyVnlkR2x2Ym5Ndll6SndZUzVvWVhOb0xtUmhkR0ZrYUdGemFGZ2dYMFFReEhzTmI3cU53aFZsM2tzZUNUZTRpenhQNWFUR2lRNTd1Vnd6K0Y1MFkyeGhhVzFmWjJWdVpYSmhkRzl5WDJsdVptK2paRzVoYldWdlFXNTBhSEp2Y0dsaklFWnBiR1Z6WjNabGNuTnBiMjVsTVM0d0xqQnJjM0JsWTFabGNuTnBiMjVsTWk0MExqQUFBQkE0YW5WdFlnQUFBQ2hxZFcxa1l6Smpjd0FSQUJDQUFBQ3FBRGliY1FOak1uQmhMbk5wWjI1aGRIVnlaUUFBQUJBSVkySnZjdEtFV1FJU29nRW1HQ0ZaQWdvd2dnSUdNSUlCamFBREFnRUNBaFJBNWFBSzdzSTUwTDY0Zy9vR1FnVTlaMVVUQURBS0JnZ3Foa2pPUFFRREF6QkpNUmN3RlFZRFZRUUtFdzVCYm5Sb2NtOXdhV01zSUZCQ1F6RXVNQ3dHQTFVRUF4TWxRVzUwYUhKdmNHbGpJRU52Ym5SbGJuUWdRM0psWkdWdWRHbGhiSE1nVW05dmRDQkRRVEFlRncweU5qQTRNRGN4T0RRek5UWmFGdzB5T0RBNE1EWXhPVFF6TlRaYU1FUXhGekFWQmdOVkJBb1REa0Z1ZEdoeWIzQnBZeXdnVUVKRE1Ta3dKd1lEVlFRREV5QkJiblJvY205d2FXTWdRMnhoZFdSbElFTnZiblJsYm5RZ1UybG5ibWx1WnpCWk1CTUdCeXFHU000OUFnRUdDQ3FHU000OUF3RUhBMElBQkpoNkNtdkxVQmdGRk5VMHZVS2xPVnRFNmRqZDE3TDVTdXdYMExlbUZpc0JNM2RrZC8zY3lqeEZBM1FvNVM0NmZYMC9paFkwVlo3bWZiOUtGNzAzdDVPaldEQldNQTRHQTFVZER3RUIvd1FFQXdJSGdEQVZCZ05WSFNVRURqQU1CZ29yQmdFRUFZUG9YZ0lCTUF3R0ExVWRFd0VCL3dRQ01BQXdId1lEVlIwakJCZ3dGb0FVemxIaUJJRk9aRnNqK09QRXo1bytuTUhYWE1Jd0NnWUlLb1pJemowRUF3TURad0F3WkFJd01YTWRGSjRCZXRMTFZZN09SdUU5bm9xYmJBWk9abi9hQXJYeVR3RkFaZktyUHp4RjJ2UG9KTmYxK1VDZGcxWEdBakJ3WDF6ZDlXR3FZa3FtTDVTRnF3MVF5U2pyMXpKZnBKTTkrMXJkRHdTUExNT1BPakt1aVhqb1UvcFVVZUc5UndtaFkzQmhaRmtObmdBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBNkZqYTNYZTMxaEozZXZFMnBnZzRrdnljZlZ5ZGFQYjN3b2pyNjd3TVRrekFBQUJ3WTJKdmNxTnBaR002Wm05eWJXRjBiV2x0WVdkbEwzTjJaeXQ0Yld4cWFXNXpkR0Z1WTJWSlJIZ3NlRzF3T21scFpEbzBPR1prTnpZd05DMHdPVFkyTFRSaE1qVXRPR1ZsTXkwME16RXpaR1F3WkdNeE5tVnNjbVZzWVhScGIyNXphR2x3YUhCaGNtVnVkRTltQUFBQjRtcDFiV0lBQUFCQmFuVnRaR05pYjNJQUVRQVFnQUFBcWdBNG0zRVRZekp3WVM1aFkzUnBiMjV6TG5ZeUFBQUFBQmhqTW5Ob3plTnN1VkRRZGZTcDUyT25lSFFOQWdBQUFabGpZbTl5b21kaFkzUnBiMjV6Z3FKbVlXTjBhVzl1YTJNeWNHRXViM0JsYm1Wa2FuQmhjbUZ0WlhSbGNuT2hhMmx1WjNKbFpHbGxiblJ6Z2FKamRYSnNlQzF6Wld4bUkycDFiV0ptUFdNeWNHRXVZWE56WlhKMGFXOXVjeTlqTW5CaExtbHVaM0psWkdsbGJuUXVkak5rYUdGemFGZ2djTnVtVmRGRC9PMExIRW43S2lrRXNoNDRWQUlQZVd6NDlRaFNiTDZ0RHdDa1ptRmpkR2x2Ym5nZFkyOXRMbUZ1ZEdoeWIzQnBZeTVqYkdGMVpHVXVjSEp2ZG1sa1pXUnFjR0Z5WVcxbGRHVnljNkY0SDJOdmJTNWhiblJvY205d2FXTXViM0pwWjJsdUxXTnZibVpwWkdWdVkyVm5kVzVyYm05M2JtdGtaWE5qY21sd2RHbHZibmhtUTJ4aGRXUmxJSEJ5YjNacFpHVmtJSFJvYVhNZ1ptbHNaU0JoZENCMGFHVWdjbVZ4ZFdWemRDQnZaaUJoSUhWelpYSWdZVzVrSUcxaGVTQm9ZWFpsSUdOeVpXRjBaV1FnYjNJZ2JXOWthV1pwWldRZ2RHaGxJR1pwYkdVZ1kyOXVkR1Z1ZEhNdWJYTnZablIzWVhKbFFXZGxiblNoWkc1aGJXVm1RMnhoZFdSbGNtRnNiRUZqZEdsdmJuTkpibU5zZFdSbFpQVUFBQURJYW5WdFlnQUFBRUJxZFcxa1kySnZjZ0FSQUJDQUFBQ3FBRGliY1JOak1uQmhMbWhoYzJndVpHRjBZUUFBQUFBWVl6SnphTDM0M3Y4NW1OT2NGNFJpS1JZUHEwd0FBQUNBWTJKdmNxVmpZV3huWm5Ob1lUSTFObU53WVdSTkFBQUFBQUFBQUFBQUFBQUFBR1JvWVhOb1dDQUhhTm9OS1NrUlg1aVJNT2kxeXBoV2RjR21rWnA0SVU2L0JqZmN1ajZzcW1SdVlXMWxibXAxYldKbUlHMWhibWxtWlhOMGFtVjRZMngxYzJsdmJuT0JvbVZ6ZEdGeWRCaThabXhsYm1kMGFCa2VCQUFBQWo1cWRXMWlBQUFBSjJwMWJXUmpNbU5zQUJFQUVJQUFBS29BT0p0eEEyTXljR0V1WTJ4aGFXMHVkaklBQUFBQ0QyTmliM0tsWTJGc1oyWnphR0V5TlRacGMybG5ibUYwZFhKbGVFMXpaV3htSTJwMWJXSm1QUzlqTW5CaEwzVnlianBqTW5CaE9qWmlPREJtWW1JNExXWXlaVE10TkdKbU9DMWhNakV3TFRobE1EZzROakpsWXpNd09TOWpNbkJoTG5OcFoyNWhkSFZ5WldwcGJuTjBZVzVqWlVsRWVDeDRiWEE2YVdsa09qYzNNalEzWWpoaExUTmpOVEl0TkRJMVl5MWlOamswTFdWa05XRXhaR1psWWpjd09ISmpjbVZoZEdWa1gyRnpjMlZ5ZEdsdmJuT0RvbU4xY214NExYTmxiR1lqYW5WdFltWTlZekp3WVM1aGMzTmxjblJwYjI1ekwyTXljR0V1YVc1bmNtVmthV1Z1ZEM1Mk0yUm9ZWE5vV0NCdzI2WlYwVVA4N1FzY1Nmc3FLUVN5SGpoVUFnOTViUGoxQ0ZKc3ZxMFBBS0pqZFhKc2VDcHpaV3htSTJwMWJXSm1QV015Y0dFdVlYTnpaWEowYVc5dWN5OWpNbkJoTG1GamRHbHZibk11ZGpKa2FHRnphRmdnTFVWK2dBTS9xOEZxYWZ5THZOM0dOZ09ETEhmakxuVUpvemRLd3dSRTBjeWlZM1Z5YkhncGMyVnNaaU5xZFcxaVpqMWpNbkJoTG1GemMyVnlkR2x2Ym5Ndll6SndZUzVvWVhOb0xtUmhkR0ZrYUdGemFGZ2dYMFFReEhzTmI3cU53aFZsM2tzZUNUZTRpenhQNWFUR2lRNTd1Vnd6K0Y1MFkyeGhhVzFmWjJWdVpYSmhkRzl5WDJsdVptK2paRzVoYldWdlFXNTBhSEp2Y0dsaklFWnBiR1Z6WjNabGNuTnBiMjVsTVM0d0xqQnJjM0JsWTFabGNuTnBiMjVsTWk0MExqQUFBQkE0YW5WdFlnQUFBQ2hxZFcxa1l6Smpjd0FSQUJDQUFBQ3FBRGliY1FOak1uQmhMbk5wWjI1aGRIVnlaUUFBQUJBSVkySnZjdEtFV1FJU29nRW1HQ0ZaQWdvd2dnSUdNSUlCamFBREFnRUNBaFJBNWFBSzdzSTUwTDY0Zy9vR1FnVTlaMVVUQURBS0JnZ3Foa2pPUFFRREF6QkpNUmN3RlFZRFZRUUtFdzVCYm5Sb2NtOXdhV01zSUZCQ1F6RXVNQ3dHQTFVRUF4TWxRVzUwYUhKdmNHbGpJRU52Ym5SbGJuUWdRM0psWkdWdWRHbGhiSE1nVW05dmRDQkRRVEFlRncweU5qQTRNRGN4T0RRek5UWmFGdzB5T0RBNE1EWXhPVFF6TlRaYU1FUXhGekFWQmdOVkJBb1REa0Z1ZEdoeWIzQnBZeXdnVUVKRE1Ta3dKd1lEVlFRREV5QkJiblJvY205d2FXTWdRMnhoZFdSbElFTnZiblJsYm5RZ1UybG5ibWx1WnpCWk1CTUdCeXFHU000OUFnRUdDQ3FHU000OUF3RUhBMElBQkpoNkNtdkxVQmdGRk5VMHZVS2xPVnRFNmRqZDE3TDVTdXdYMExlbUZpc0JNM2RrZC8zY3lqeEZBM1FvNVM0NmZYMC9paFkwVlo3bWZiOUtGNzAzdDVPaldEQldNQTRHQTFVZER3RUIvd1FFQXdJSGdEQVZCZ05WSFNVRURqQU1CZ29yQmdFRUFZUG9YZ0lCTUF3R0ExVWRFd0VCL3dRQ01BQXdId1lEVlIwakJCZ3dGb0FVemxIaUJJRk9aRnNqK09QRXo1bytuTUhYWE1Jd0NnWUlLb1pJemowRUF3TURad0F3WkFJd01YTWRGSjRCZXRMTFZZN09SdUU5bm9xYmJBWk9abi9hQXJYeVR3RkFaZktyUHp4RjJ2UG9KTmYxK1VDZGcxWEdBakJ3WDF6ZDlXR3FZa3FtTDVTRnF3MVF5U2pyMXpKZnBKTTkrMXJkRHdTUExNT1BPakt1aVhqb1UvcFVVZUc5UndtaFkzQmhaRmtObmdBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBNkZqYTNYZTMxaEozZXZFMnBnZzRrdnljZlZ5ZGFQYjN3b2pyNjd3TVRrekFBQUJ3WTJKdmNxTnBaR002Wm05eWJXRjBiV2x0WVdkbEwzTjJaeXQ0Yld4cWFXNXpkR0Z1WTJWSlJIZ3NlRzF3T21scFpEbzBPR1prTnpZd05DMHdPVFkyTFRSaE1qVXRPR1ZsTXkwME16RXpaR1F3WkdNeE5tVnNjbVZzWVhScGIyNXphR2x3YUhCaGNtVnVkRTltQUFBQjRtcDFiV0lBQUFCQmFuVnRaR05pYjNJQUVRQVFnQUFBcWdBNG0zRVRZekp3WVM1aFkzUnBiMjV6TG5ZeUFBQUFBQmhqTW5Ob3plTnN1VkRRZGZTcDUyT25lSFFOQWdBQUFabGpZbTl5b21kaFkzUnBiMjV6Z3FKbVlXTjBhVzl1YTJNeWNHRXViM0JsYm1Wa2FuQmhjbUZ0WlhSbGNuT2hhMmx1WjNKbFpHbGxiblJ6Z2FKamRYSnNlQzF6Wld4bUkycDFiV0ptUFdNeWNHRXVZWE56WlhKMGFXOXVjeTlqTW5CaExtbHVaM0psWkdsbGJuUXVkak5rYUdGemFGZ2djTnVtVmRGRC9PMExIRW43S2lrRXNoNDRWQUlQZVd6NDlRaFNiTDZ0RHdDa1ptRmpkR2x2Ym5nZFkyOXRMbUZ1ZEdoeWIzQnBZeTVqYkdGMVpHVXVjSEp2ZG1sa1pXUnFjR0Z5WVcxbGRHVnljNkY0SDJOdmJTNWhiblJvY205d2FXTXViM0pwWjJsdUxXTnZibVpwWkdWdVkyVm5kVzVyYm05M2JtdGtaWE5qY21sd2RHbHZibmhtUTJ4aGRXUmxJSEJ5YjNacFpHVmtJSFJvYVhNZ1ptbHNaU0JoZENCMGFHVWdjbVZ4ZFdWemRDQnZaaUJoSUhWelpYSWdZVzVrSUcxaGVTQm9ZWFpsSUdOeVpXRjBaV1FnYjNJZ2JXOWthV1pwWldRZ2RHaGxJR1pwYkdVZ1kyOXVkR1Z1ZEhNdWJYTnZablIzWVhKbFFXZGxiblNoWkc1aGJXVm1RMnhoZFdSbGNtRnNiRUZqZEdsdmJuTkpibU5zZFdSbFpQVUFBQURJYW5WdFlnQUFBRUJxZFcxa1kySnZjZ0FSQUJDQUFBQ3FBRGliY1JOak1uQmhMbWhoYzJndVpHRjBZUUFBQUFBWVl6SnphTDM0M3Y4NW1OT2NGNFJpS1JZUHEwd0FBQUNBWTJKdmNxVmpZV3huWm5Ob1lUSTFObU53WVdSTkFBQUFBQUFBQUFBQUFBQUFBR1JvWVhOb1dDQUhhTm9OS1NrUlg1aVJNT2kxeXBoV2RjR21rWnA0SVU2L0JqZmN1ajZzcW1SdVlXMWxibXAxYldKbUlHMWhibWxtWlhOMGFtVjRZMngxYzJsdmJuT0JvbVZ6ZEdGeWRCaThabXhsYm1kMGFCa2VCQUFBQWo1cWRXMWlBQUFBSjJwMWJXUmpNbU5zQUJFQUVJQUFBS29BT0p0eEEyTXljR0V1WTJ4aGFXMHVkaklBQUFBQ0QyTmliM0tsWTJGc1oyWnphR0V5TlRacGMybG5ibUYwZFhKbGVFMXpaV3htSTJwMWJXSm1QUzlqTW5CaEwzVnlianBqTW5CaE9qWmlPREJtWW1JNExXWXlaVE10TkdKbU9DMWhNakV3TFRobE1EZzROakpsWXpNd09TOWpNbkJoTG5OcFoyNWhkSFZ5WldwcGJuTjBZVzVqWlVsRWVDeDRiWEE2YVdsa09qYzNNalEzWWpoaExUTmpOVEl0TkRJMVl5MWlOamswTFdWa05XRXhaR1psWWpjd09ISmpjbVZoZEdWa1gyRnpjMlZ5ZEdsdmJuT0RvbU4xY214NExYTmxiR1lqYW5WdFltWTlZekp3WVM1aGMzTmxjblJwYjI1ekwyTXljR0V1YVc1bmNtVmthV1Z1ZEM1Mk0yUm9ZWE5vV0NCdzI2WlYwVVA4N1FzY1Nmc3FLUVN5SGpoVUFnOTViUGoxQ0ZKc3ZxMFBBS0pqZFhKc2VDcHpaV3htSTJwMWJXSm1QV015Y0dFdVlYTnpaWEowYVc5dWN5OWpNbkJoTG1GamRHbHZibk11ZGpKa2FHRnphRmdnTFVWK2dBTS9xOEZxYWZ5THZOM0dOZ09ETEhmakxuVUpvemRLd3dSRTBjeWlZM1Z5YkhncGMyVnNaaU5xZFcxaVpqMWpNbkJoTG1GemMyVnlkR2x2Ym5Ndll6SndZUzVvWVhOb0xtUmhkR0ZrYUdGemFGZ2dYMFFReEhzTmI3cU53aFZsM2tzZUNUZTRpenhQNWFUR2lRNTd1Vnd6K0Y1MFkyeGhhVzFmWjJWdVpYSmhkRzl5WDJsdVptK2paRzVoYldWdlFXNTBhSEp2Y0dsaklFWnBiR1Z6WjNabGNuTnBiMjVsTVM0d0xqQnJjM0JsWTFabGNuTnBiMjVsTWk0MExqQUFBQkE0YW5WdFlnQUFBQ2hxZFcxa1l6Smpjd0FSQUJDQUFBQ3FBRGliY1FOak1uQmhMbk5wWjI1aGRIVnlaUUFBQUJBSVkySnZjdEtFV1FJU29nRW1HQ0ZaQWdvd2dnSUdNSUlCamFBREFnRUNBaFJBNWFBSzdzSTUwTDY0Zy9vR1FnVTlaMVVUQURBS0JnZ3Foa2pPUFFRREF6QkpNUmN3RlFZRFZRUUtFdzVCYm5Sb2NtOXdhV01zSUZCQ1F6RXVNQ3dHQTFVRUF4TWxRVzUwYUhKdmNHbGpJRU52Ym5SbGJuUWdRM0psWkdWdWRHbGhiSE1nVW05dmRDQkRRVEFlRncweU5qQTRNRGN4T0RRek5UWmFGdzB5T0RBNE1EWXhPVFF6TlRaYU1FUXhGekFWQmdOVkJBb1REa0Z1ZEdoeWIzQnBZeXdnVUVKRE1Ta3dKd1lEVlFRREV5QkJiblJvY205d2FXTWdRMnhoZFdSbElFTnZiblJsYm5RZ1UybG5ibWx1WnpCWk1CTUdCeXFHU000OUFnRUdDQ3FHU000OUF3RUhBMElBQkpoNkNtdkxVQmdGRk5VMHZVS2xPVnRFNmRqZDE3TDVTdXdYMExlbUZpc0JNM2RrZC8zY3lqeEZBM1FvNVM0NmZYMC9paFkwVlo3bWZiOUtGNzAzdDVPaldEQldNQTRHQTFVZER3RUIvd1FFQXdJSGdEQVZCZ05WSFNVRURqQU1CZ29yQmdFRUFZUG9YZ0lCTUF3R0ExVWRFd0VCL3dRQ01BQXdId1lEVlIwakJCZ3dGb0FVemxIaUJJRk9aRnNqK09QRXo1bytuTUhYWE1Jd0NnWUlLb1pJemowRUF3TURad0F3WkFJd01YTWRGSjRCZXRMTFZZN09SdUU5bm9xYmJBWk9abi9hQXJYeVR3RkFaZktyUHp4RjJ2UG9KTmYxK1VDZGcxWEdBakJ3WDF6ZDlXR3FZa3FtTDVTRnF3MVF5U2pyMXpKZnBKTTkrMXJkRHdTUExNT1BPakt1aVhqb1UvcFVVZUc5UndtaFkzQmhaRmtObmdBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBNkZqYTNYZTMxaEozZXZFMnBnZzRrdnljZlZ5ZGFQYjN3b2pyNjd3TVRrekFBQUJ3WTJKdmNxTnBaR002Wm05eWJXRjBiV2x0WVdkbEwzTjJaeXQ0Yld4cWFXNXpkR0Z1WTJWSlJIZ3NlRzF3T21scFpEbzBPR1prTnpZd05DMHdPVFkyTFRSaE1qVXRPR1ZsTXkwME16RXpaR1F3WkdNeE5tVnNjbVZzWVhScGIyNXphR2x3YUhCaGNtVnVkRTltQUFBQjRtcDFiV0lBQUFCQmFuVnRaR05pYjNJQUVRQVFnQUFBcWdBNG0zRVRZekp3WVM1aFkzUnBiMjV6TG5ZeUFBQUFBQmhqTW5Ob3plTnN1VkRRZGZTcDUyT25lSFFOQWdBQUFabGpZbTl5b21kaFkzUnBiMjV6Z3FKbVlXTjBhVzl1YTJNeWNHRXViM0JsYm1Wa2FuQmhjbUZ0WlhSbGNuT2hhMmx1WjNKbFpHbGxiblJ6Z2FKamRYSnNlQzF6Wld4bUkycDFiV0ptUFdNeWNHRXVZWE56WlhKMGFXOXVjeTlqTW5CaExtbHVaM0psWkdsbGJuUXVkak5rYUdGemFGZ2djTnVtVmRGRC9PMExIRW43S2lrRXNoNDRWQUlQZVd6NDlRaFNiTDZ0RHdDa1ptRmpkR2x2Ym5nZFkyOXRMbUZ1ZEdoeWIzQnBZeTVqYkdGMVpHVXVjSEp2ZG1sa1pXUnFjR0Z5WVcxbGRHVnljNkY0SDJOdmJTNWhiblJvY205d2FXTXViM0pwWjJsdUxXTnZibVpwWkdWdVkyVm5kVzVyYm05M2JtdGtaWE5qY21sd2RHbHZibmhtUTJ4aGRXUmxJSEJ5YjNacFpHVmtJSFJvYVhNZ1ptbHNaU0JoZENCMGFHVWdjbVZ4ZFdWemRDQnZaaUJoSUhWelpYSWdZVzVrSUcxaGVTQm9ZWFpsSUdOeVpXRjBaV1FnYjNJZ2JXOWthV1pwWldRZ2RHaGxJR1pwYkdVZ1kyOXVkR1Z1ZEhNdWJYTnZablIzWVhKbFFXZGxiblNoWkc1aGJXVm1RMnhoZFdSbGNtRnNiRUZqZEdsdmJuTkpibU5zZFdSbFpQVUFBQURJYW5WdFlnQUFBRUJxZFcxa1kySnZjZ0FSQUJDQUFBQ3FBRGliY1JOak1uQmhMbWhoYzJndVpHRjBZUUFBQUFBWVl6SnphTDM0M3Y4NW1OT2NGNFJpS1JZUHEwd0FBQUNBWTJKdmNxVmpZV3huWm5Ob1lUSTFObU53WVdSTkFBQUFBQUFBQUFBQUFBQUFBR1JvWVhOb1dDQUhhTm9OS1NrUlg1aVJNT2kxeXBoV2RjR21rWnA0SVU2L0JqZmN1ajZzcW1SdVlXMWxibXAxYldKbUlHMWhibWxtWlhOMGFtVjRZMngxYzJsdmJuT0JvbVZ6ZEdGeWRCaThabXhsYm1kMGFCa2VCQUFBQWo1cWRXMWlBQUFBSjJwMWJXUmpNbU5zQUJFQUVJQUFBS29BT0p0eEEyTXljR0V1WTJ4aGFXMHVkaklBQUFBQ0QyTmliM0tsWTJGc1oyWnphR0V5TlRacGMybG5ibUYwZFhKbGVFMXpaV3htSTJwMWJXSm1QUzlqTW5CaEwzVnlianBqTW5CaE9qWmlPREJtWW1JNExXWXlaVE10TkdKbU9DMWhNakV3TFRobE1EZzROakpsWXpNd09TOWpNbkJoTG5OcFoyNWhkSFZ5WldwcGJuTjBZVzVqWlVsRWVDeDRiWEE2YVdsa09qYzNNalEzWWpoaExUTmpOVEl0TkRJMVl5MWlOamswTFdWa05XRXhaR1psWWpjd09ISmpjbVZoZEdWa1gyRnpjMlZ5ZEdsdmJuT0RvbU4xY214NExYTmxiR1lqYW5WdFltWTlZekp3WVM1aGMzTmxjblJwYjI1ekwyTXljR0V1YVc1bmNtVmthV1Z1ZEM1Mk0yUm9ZWE5vV0NCdzI2WlYwVVA4N1FzY1Nmc3FLUVN5SGpoVUFnOTViUGoxQ0ZKc3ZxMFBBS0pqZFhKc2VDcHpaV3htSTJwMWJXSm1QV015Y0dFdVlYTnpaWEowYVc5dWN5OWpNbkJoTG1GamRHbHZibk11ZGpKa2FHRnphRmdnTFVWK2dBTS9xOEZxYWZ5THZOM0dOZ09ETEhmakxuVUpvemRLd3dSRTBjeWlZM1Z5YkhncGMyVnNaaU5xZFcxaVpqMWpNbkJoTG1GemMyVnlkR2x2Ym5Ndll6SndZUzVvWVhOb0xtUmhkR0ZrYUdGemFGZ2dYMFFReEhzTmI3cU53aFZsM2tzZUNUZTRpenhQNWFUR2lRNTd1Vnd6K0Y1MFkyeGhhVzFmWjJWdVpYSmhkRzl5WDJsdVptK2paRzVoYldWdlFXNTBhSEp2Y0dsaklFWnBiR1Z6WjNabGNuTnBiMjVsTVM0d0xqQnJjM0JsWTFabGNuTnBiMjVsTWk0MExqQUFBQkE0YW5WdFlnQUFBQ2hxZFcxa1l6Smpjd0FSQUJDQUFBQ3FBRGliY1FOak1uQmhMbk5wWjI1aGRIVnlaUUFBQUJBSVkySnZjdEtFV1FJU29nRW1HQ0ZaQWdvd2dnSUdNSUlCamFBREFnRUNBaFJBNWFBSzdzSTUwTDY0Zy9vR1FnVTlaMVVUQURBS0JnZ3Foa2pPUFFRREF6QkpNUmN3RlFZRFZRUUtFdzVCYm5Sb2NtOXdhV01zSUZCQ1F6RXVNQ3dHQTFVRUF4TWxRVzUwYUhKdmNHbGpJRU52Ym5SbGJuUWdRM0psWkdWdWRHbGhiSE1nVW05dmRDQkRRVEFlRncweU5qQTRNRGN4T0RRek5UWmFGdzB5T0RBNE1EWXhPVFF6TlRaYU1FUXhGekFWQmdOVkJBb1REa0Z1ZEdoeWIzQnBZeXdnVUVKRE1Ta3dKd1lEVlFRREV5QkJiblJvY205d2FXTWdRMnhoZFdSbElFTnZiblJsYm5RZ1UybG5ibWx1WnpCWk1CTUdCeXFHU000OUFnRUdDQ3FHU000OUF3RUhBMElBQkpoNkNtdkxVQmdGRk5VMHZVS2xPVnRFNmRqZDE3TDVTdXdYMExlbUZpc0JNM2RrZC8zY3lqeEZBM1FvNVM0NmZYMC9paFkwVlo3bWZiOUtGNzAzdDVPaldEQldNQTRHQTFVZER3RUIvd1FFQXdJSGdEQVZCZ05WSFNVRURqQU1CZ29yQmdFRUFZUG9YZ0lCTUF3R0ExVWRFd0VCL3dRQ01BQXdId1lEVlIwakJCZ3dGb0FVemxIaUJJRk9aRnNqK09QRXo1bytuTUhYWE1Jd0NnWUlLb1pJemowRUF3TURad0F3WkFJd01YTWRGSjRCZXRMTFZZN09SdUU5bm9xYmJBWk9abi9hQXJYeVR3RkFaZktyUHp4RjJ2UG9KTmYxK1VDZGcxWEdBakJ3WDF6ZDlXR3FZa3FtTDVTRnF3MVF5U2pyMXpKZnBKTTkrMXJkRHdTUExNT1BPakt1aVhqb1UvcFVVZUc5UndtaFkzQmhaRmtObmdBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBNkZqYTNYZTMxaEozZXZFMnBnZzRrdnljZlZ5ZGFQYjN3b2pyNjd3TVRrekFBQUJ3WTJKdmNxTnBaR002Wm05eWJXRjBiV2x0WVdkbEwzTjJaeXQ0Yld4cWFXNXpkR0Z1WTJWSlJIZ3NlRzF3T21scFpEbzBPR1prTnpZd05DMHdPVFkyTFRSaE1qVXRPR1ZsTXkwME16RXpaR1F3WkdNeE5tVnNjbVZzWVhScGIyNXphR2x3YUhCaGNtVnVkRTltQUFBQjRtcDFiV0lBQUFCQmFuVnRaR05pYjNJQUVRQVFnQUFBcWdBNG0zRVRZekp3WVM1aFkzUnBiMjV6TG5ZeUFBQUFBQmhqTW5Ob3plTnN1VkRRZGZTcDUyT25lSFFOQWdBQUFabGpZbTl5b21kaFkzUnBiMjV6Z3FKbVlXTjBhVzl1YTJNeWNHRXViM0JsYm1Wa2FuQmhjbUZ0WlhSbGNuT2hhMmx1WjNKbFpHbGxiblJ6Z2FKamRYSnNlQzF6Wld4bUkycDFiV0ptUFdNeWNHRXVZWE56WlhKMGFXOXVjeTlqTW5CaExtbHVaM0psWkdsbGJuUXVkak5rYUdGemFGZ2djTnVtVmRGRC9PMExIRW43S2lrRXNoNDRWQUlQZVd6NDlRaFNiTDZ0RHdDa1ptRmpkR2x2Ym5nZFkyOXRMbUZ1ZEdoeWIzQnBZeTVqYkdGMVpHVXVjSEp2ZG1sa1pXUnFjR0Z5WVcxbGRHVnljNkY0SDJOdmJTNWhiblJvY205d2FXTXViM0pwWjJsdUxXTnZibVpwWkdWdVkyVm5kVzVyYm05M2JtdGtaWE5qY21sd2RHbHZibmhtUTJ4aGRXUmxJSEJ5YjNacFpHVmtJSFJvYVhNZ1ptbHNaU0JoZENCMGFHVWdjbVZ4ZFdWemRDQnZaaUJoSUhWelpYSWdZVzVrSUcxaGVTQm9ZWFpsSUdOeVpXRjBaV1FnYjNJZ2JXOWthV1pwWldRZ2RHaGxJR1pwYkdVZ1kyOXVkR1Z1ZEhNdWJYTnZablIzWVhKbFFXZGxiblNoWkc1aGJXVm1RMnhoZFdSbGNtRnNiRUZqZEdsdmJuTkpibU5zZFdSbFpQVUFBQURJYW5WdFlnQUFBRUJxZFcxa1kySnZjZ0FSQUJDQUFBQ3FBRGliY1JOak1uQmhMbWhoYzJndVpHRjBZUUFBQUFBWVl6SnphTDM0M3Y4NW1OT2NGNFJpS1JZUHEwd0FBQUNBWTJKdmNxVmpZV3huWm5Ob1lUSTFObU53WVdSTkFBQUFBQUFBQUFBQUFBQUFBR1JvWVhOb1dDQUhhTm9OS1NrUlg1aVJNT2kxeXBoV2RjR21rWnA0SVU2L0JqZmN1ajZzcW1SdVlXMWxibXAxYldKbUlHMWhibWxtWlhOMGFtVjRZMngxYzJsdmJuT0JvbVZ6ZEdGeWRCaThabXhsYm1kMGFCa2VCQUFBQWo1cWRXMWlBQUFBSjJwMWJXUmpNbU5zQUJFQUVJQUFBS29BT0p0eEEyTXljR0V1WTJ4aGFXMHVkaklBQUFBQ0QyTmliM0tsWTJGc1oyWnphR0V5TlRacGMybG5ibUYwZFhKbGVFMXpaV3htSTJwMWJXSm1QUzlqTW5CaEwzVnlianBqTW5CaE9qWmlPREJtWW1JNExXWXlaVE10TkdKbU9DMWhNakV3TFRobE1EZzROakpsWXpNd09TOWpNbkJoTG5OcFoyNWhkSFZ5WldwcGJuTjBZVzVqWlVsRWVDeDRiWEE2YVdsa09qYzNNalEzWWpoaExUTmpOVEl0TkRJMVl5MWlOamswTFdWa05XRXhaR1psWWpjd09ISmpjbVZoZEdWa1gyRnpjMlZ5ZEdsdmJuT0RvbU4xY214NExYTmxiR1lqYW5WdFltWTlZekp3WVM1aGMzTmxjblJwYjI1ekwyTXljR0V1YVc1bmNtVmthV1Z1ZEM1Mk0yUm9ZWE5vV0NCdzI2WlYwVVA4N1FzY1Nmc3FLUVN5SGpoVUFnOTViUGoxQ0ZKc3ZxMFBBS0pqZFhKc2VDcHpaV3htSTJwMWJXSm1QV015Y0dFdVlYTnpaWEowYVc5dWN5OWpNbkJoTG1GamRHbHZibk11ZGpKa2FHRnphRmdnTFVWK2dBTS9xOEZxYWZ5THZOM0dOZ09ETEhmakxuVUpvemRLd3dSRTBjeWlZM1Z5YkhncGMyVnNaaU5xZFcxaVpqMWpNbkJoTG1GemMyVnlkR2x2Ym5Ndll6SndZUzVvWVhOb0xtUmhkR0ZrYUdGemFGZ2dYMFFReEhzTmI3cU53aFZsM2tzZUNUZTRpenhQNWFUR2lRNTd1Vnd6K0Y1MFkyeGhhVzFmWjJWdVpYSmhkRzl5WDJsdVptK2paRzVoYldWdlFXNTBhSEp2Y0dsaklFWnBiR1Z6WjNabGNuTnBiMjVsTVM0d0xqQnJjM0JsWTFabGNuTnBiMjVsTWk0MExqQUFBQkE0YW5WdFlnQUFBQ2hxZFcxa1l6Smpjd0FSQUJDQUFBQ3FBRGliY1FOak1uQmhMbk5wWjI1aGRIVnlaUUFBQUJBSVkySnZjdEtFV1FJU29nRW1HQ0ZaQWdvd2dnSUdNSUlCamFBREFnRUNBaFJBNWFBSzdzSTUwTDY0Zy9vR1FnVTlaMVVUQURBS0JnZ3Foa2pPUFFRREF6QkpNUmN3RlFZRFZRUUtFdzVCYm5Sb2NtOXdhV01zSUZCQ1F6RXVNQ3dHQTFVRUF4TWxRVzUwYUhKdmNHbGpJRU52Ym5SbGJuUWdRM0psWkdWdWRHbGhiSE1nVW05dmRDQkRRVEFlRncweU5qQTRNRGN4T0RRek5UWmFGdzB5T0RBNE1EWXhPVFF6TlRaYU1FUXhGekFWQmdOVkJBb1REa0Z1ZEdoeWIzQnBZeXdnVUVKRE1Ta3dKd1lEVlFRREV5QkJiblJvY205d2FXTWdRMnhoZFdSbElFTnZiblJsYm5RZ1UybG5ibWx1WnpCWk1CTUdCeXFHU000OUFnRUdDQ3FHU000OUF3RUhBMElBQkpoNkNtdkxVQmdGRk5VMHZVS2xPVnRFNmRqZDE3TDVTdXdYMExlbUZpc0JNM2RrZC8zY3lqeEZBM1FvNVM0NmZYMC9paFkwVlo3bWZiOUtGNzAzdDVPaldEQldNQTRHQTFVZER3RUIvd1FFQXdJSGdEQVZCZ05WSFNVRURqQU1CZ29yQmdFRUFZUG9YZ0lCTUF3R0ExVWRFd0VCL3dRQ01BQXdId1lEVlIwakJCZ3dGb0FVemxIaUJJRk9aRnNqK09QRXo1bytuTUhYWE1Jd0NnWUlLb1pJemowRUF3TURad0F3WkFJd01YTWRGSjRCZXRMTFZZN09SdUU5bm9xYmJBWk9abi9hQXJYeVR3RkFaZktyUHp4RjJ2UG9KTmYxK1VDZGcxWEdBakJ3WDF6ZDlXR3FZa3FtTDVTRnF3MVF5U2pyMXpKZnBKTTkrMXJkRHdTUExNT1BPakt1aVhqb1UvcFVVZUc5UndtaFkzQmhaRmtObmdBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBNkZqYTNYZTMxaEozZXZFMnBnZzRrdnljZlZ5ZGFQYjN3b2pyNjd3TVRrekFBQUJ3WTJKdmNxTnBaR002Wm05eWJXRjBiV2x0WVdkbEwzTjJaeXQ0Yld4cWFXNXpkR0Z1WTJWSlJIZ3NlRzF3T21scFpEbzBPR1prTnpZd05DMHdPVFkyTFRSaE1qVXRPR1ZsTXkwME16RXpaR1F3WkdNeE5tVnNjbVZzWVhScGIyNXphR2x3YUhCaGNtVnVkRTltQUFBQjRtcDFiV0lBQUFCQmFuVnRaR05pYjNJQUVRQVFnQUFBcWdBNG0zRVRZekp3WVM1aFkzUnBiMjV6TG5ZeUFBQUFBQmhqTW5Ob3plTnN1VkRRZGZTcDUyT25lSFFOQWdBQUFabGpZbTl5b21kaFkzUnBiMjV6Z3FKbVlXTjBhVzl1YTJNeWNHRXViM0JsYm1Wa2FuQmhjbUZ0WlhSbGNuT2hhMmx1WjNKbFpHbGxiblJ6Z2FKamRYSnNlQzF6Wld4bUkycDFiV0ptUFdNeWNHRXVZWE56WlhKMGFXOXVjeTlqTW5CaExtbHVaM0psWkdsbGJuUXVkak5rYUdGemFGZ2djTnVtVmRGRC9PMExIRW43S2lrRXNoNDRWQUlQZVd6NDlRaFNiTDZ0RHdDa1ptRmpkR2x2Ym5nZFkyOXRMbUZ1ZEdoeWIzQnBZeTVqYkdGMVpHVXVjSEp2ZG1sa1pXUnFjR0Z5WVcxbGRHVnljNkY0SDJOdmJTNWhiblJvY205d2FXTXViM0pwWjJsdUxXTnZibVpwWkdWdVkyVm5kVzVyYm05M2JtdGtaWE5qY21sd2RHbHZibmhtUTJ4aGRXUmxJSEJ5YjNacFpHVmtJSFJvYVhNZ1ptbHNaU0JoZENCMGFHVWdjbVZ4ZFdWemRDQnZaaUJoSUhWelpYSWdZVzVrSUcxaGVTQm9ZWFpsSUdOeVpXRjBaV1FnYjNJZ2JXOWthV1pwWldRZ2RHaGxJR1pwYkdVZ1kyOXVkR1Z1ZEhNdWJYTnZablIzWVhKbFFXZGxiblNoWkc1aGJXVm1RMnhoZFdSbGNtRnNiRUZqZEdsdmJuTkpibU5zZFdSbFpQVUFBQURJYW5WdFlnQUFBRUJxZFcxa1kySnZjZ0FSQUJDQUFBQ3FBRGliY1JOak1uQmhMbWhoYzJndVpHRjBZUUFBQUFBWVl6SnphTDM0M3Y4NW1OT2NGNFJpS1JZUHEwd0FBQUNBWTJKdmNxVmpZV3huWm5Ob1lUSTFObU53WVdSTkFBQUFBQUFBQUFBQUFBQUFBR1JvWVhOb1dDQUhhTm9OS1NrUlg1aVJNT2kxeXBoV2RjR21rWnA0SVU2L0JqZmN1ajZzcW1SdVlXMWxibXAxYldKbUlHMWhibWxtWlhOMGFtVjRZMngxYzJsdmJuT0JvbVZ6ZEdGeWRCaThabXhsYm1kMGFCa2VCQUFBQWo1cWRXMWlBQUFBSjJwMWJXUmpNbU5zQUJFQUVJQUFBS29BT0p0eEEyTXljR0V1WTJ4aGFXMHVkaklBQUFBQ0QyTmliM0tsWTJGc1oyWnphR0V5TlRacGMybG5ibUYwZFhKbGVFMXpaV3htSTJwMWJXSm1QUzlqTW5CaEwzVnlianBqTW5CaE9qWmlPREJtWW1JNExXWXlaVE10TkdKbU9DMWhNakV3TFRobE1EZzROakpsWXpNd09TOWpNbkJoTG5OcFoyNWhkSFZ5WldwcGJuTjBZVzVqWlVsRWVDeDRiWEE2YVdsa09qYzNNalEzWWpoaExUTmpOVEl0TkRJMVl5MWlOamswTFdWa05XRXhaR1psWWpjd09ISmpjbVZoZEdWa1gyRnpjMlZ5ZEdsdmJuT0RvbU4xY214NExYTmxiR1lqYW5WdFltWTlZekp3WVM1aGMzTmxjblJwYjI1ekwyTXljR0V1YVc1bmNtVmthV1Z1ZEM1Mk0yUm9ZWE5vV0NCdzI2WlYwVVA4N1FzY1Nmc3FLUVN5SGpoVUFnOTViUGoxQ0ZKc3ZxMFBBS0pqZFhKc2VDcHpaV3htSTJwMWJXSm1QV015Y0dFdVlYTnpaWEowYVc5dWN5OWpNbkJoTG1GamRHbHZibk11ZGpKa2FHRnphRmdnTFVWK2dBTS9xOEZxYWZ5THZOM0dOZ09ETEhmakxuVUpvemRLd3dSRTBjeWlZM1Z5YkhncGMyVnNaaU5xZFcxaVpqMWpNbkJoTG1GemMyVnlkR2x2Ym5Ndll6SndZUzVvWVhOb0xtUmhkR0ZrYUdGemFGZ2dYMFFReEhzTmI3cU53aFZsM2tzZUNUZTRpenhQNWFUR2lRNTd1Vnd6K0Y1MFkyeGhhVzFmWjJWdVpYSmhkRzl5WDJsdVptK2paRzVoYldWdlFXNTBhSEp2Y0dsaklFWnBiR1Z6WjNabGNuTnBiMjVsTVM0d0xqQnJjM0JsWTFabGNuTnBiMjVsTWk0MExqQUFBQkE0YW5WdFlnQUFBQ2hxZFcxa1l6Smpjd0FSQUJDQUFBQ3FBRGliY1FOak1uQmhMbk5wWjI1aGRIVnlaUUFBQUJBSVkySnZjdEtFV1FJU29nRW1HQ0ZaQWdvd2dnSUdNSUlCamFBREFnRUNBaFJBNWFBSzdzSTUwTDY0Zy9vR1FnVTlaMVVUQURBS0JnZ3Foa2pPUFFRREF6QkpNUmN3RlFZRFZRUUtFdzVCYm5Sb2NtOXdhV01zSUZCQ1F6RXVNQ3dHQTFVRUF4TWxRVzUwYUhKdmNHbGpJRU52Ym5SbGJuUWdRM0psWkdWdWRHbGhiSE1nVW05dmRDQkRRVEFlRncweU5qQTRNRGN4T0RRek5UWmFGdzB5T0RBNE1EWXhPVFF6TlRaYU1FUXhGekFWQmdOVkJBb1REa0Z1ZEdoeWIzQnBZeXdnVUVKRE1Ta3dKd1lEVlFRREV5QkJiblJvY205d2FXTWdRMnhoZFdSbElFTnZiblJsYm5RZ1UybG5ibWx1WnpCWk1CTUdCeXFHU000OUFnRUdDQ3FHU000OUF3RUhBMElBQkpoNkNtdkxVQmdGRk5VMHZVS2xPVnRFNmRqZDE3TDVTdXdYMExlbUZpc0JNM2RrZC8zY3lqeEZBM1FvNVM0NmZYMC9paFkwVlo3bWZiOUtGNzAzdDVPaldEQldNQTRHQTFVZER3RUIvd1FFQXdJSGdEQVZCZ05WSFNVRURqQU1CZ29yQmdFRUFZUG9YZ0lCTUF3R0ExVWRFd0VCL3dRQ01BQXdId1lEVlIwakJCZ3dGb0FVemxIaUJJRk9aRnNqK09QRXo1bytuTUhYWE1Jd0NnWUlLb1pJemowRUF3TURad0F3WkFJd01YTWRGSjRCZXRMTFZZN09SdUU5bm9xYmJBWk9abi9hQXJYeVR3RkFaZktyUHp4RjJ2UG9KTmYxK1VDZGcxWEdBakJ3WDF6ZDlXR3FZa3FtTDVTRnF3MVF5U2pyMXpKZnBKTTkrMXJkRHdTUExNT1BPakt1aVhqb1UvcFVVZUc5UndtaFkzQmhaRmtObmdBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBNkZqYTNYZTMxaEozZXZFMnBnZzRrdnljZlZ5ZGFQYjN3b2pyNjd3TVRrekFBQUJ3WTJKdmNxTnBaR002Wm05eWJXRjBiV2x0WVdkbEwzTjJaeXQ0Yld4cWFXNXpkR0Z1WTJWSlJIZ3NlRzF3T21scFpEbzBPR1prTnpZd05DMHdPVFkyTFRSaE1qVXRPR1ZsTXkwME16RXpaR1F3WkdNeE5tVnNjbVZzWVhScGIyNXphR2x3YUhCaGNtVnVkRTltQUFBQjRtcDFiV0lBQUFCQmFuVnRaR05pYjNJQUVRQVFnQUFBcWdBNG0zRVRZekp3WVM1aFkzUnBiMjV6TG5ZeUFBQUFBQmhqTW5Ob3plTnN1VkRRZGZTcDUyT25lSFFOQWdBQUFabGpZbTl5b21kaFkzUnBiMjV6Z3FKbVlXTjBhVzl1YTJNeWNHRXViM0JsYm1Wa2FuQmhjbUZ0WlhSbGNuT2hhMmx1WjNKbFpHbGxiblJ6Z2FKamRYSnNlQzF6Wld4bUkycDFiV0ptUFdNeWNHRXVZWE56WlhKMGFXOXVjeTlqTW5CaExtbHVaM0psWkdsbGJuUXVkak5rYUdGemFGZ2djTnVtVmRGRC9PMExIRW43S2lrRXNoNDRWQUlQZVd6NDlRaFNiTDZ0RHdDa1ptRmpkR2x2Ym5nZFkyOXRMbUZ1ZEdoeWIzQnBZeTVqYkdGMVpHVXVjSEp2ZG1sa1pXUnFjR0Z5WVcxbGRHVnljNkY0SDJOdmJTNWhiblJvY205d2FXTXViM0pwWjJsdUxXTnZibVpwWkdWdVkyVm5kVzVyYm05M2JtdGtaWE5qY21sd2RHbHZibmhtUTJ4aGRXUmxJSEJ5YjNacFpHVmtJSFJvYVhNZ1ptbHNaU0JoZENCMGFHVWdjbVZ4ZFdWemRDQnZaaUJoSUhWelpYSWdZVzVrSUcxaGVTQm9ZWFpsSUdOeVpXRjBaV1FnYjNJZ2JXOWthV1pwWldRZ2RHaGxJR1pwYkdVZ1kyOXVkR1Z1ZEhNdWJYTnZablIzWVhKbFFXZGxiblNoWkc1aGJXVm1RMnhoZFdSbGNtRnNiRUZqZEdsdmJuTkpibU5zZFdSbFpQVUFBQURJYW5WdFlnQUFBRUJxZFcxa1kySnZjZ0FSQUJDQUFBQ3FBRGliY1JOak1uQmhMbWhoYzJndVpHRjBZUUFBQUFBWVl6SnphTDM0M3Y4NW1OT2NGNFJpS1JZUHEwd0FBQUNBWTJKdmNxVmpZV3huWm5Ob1lUSTFObU53WVdSTkFBQUFBQUFBQUFBQUFBQUFBR1JvWVhOb1dDQUhhTm9OS1NrUlg1aVJNT2kxeXBoV2RjR21rWnA0SVU2L0JqZmN1ajZzcW1SdVlXMWxibXAxYldKbUlHMWhibWxtWlhOMGFtVjRZMngxYzJsdmJuT0JvbVZ6ZEdGeWRCaThabXhsYm1kMGFCa2VCQUFBQWo1cWRXMWlBQUFBSjJwMWJXUmpNbU5zQUJFQUVJQUFBS29BT0p0eEEyTXljR0V1WTJ4aGFXMHVkaklBQUFBQ0QyTmliM0tsWTJGc1oyWnphR0V5TlRacGMybG5ibUYwZFhKbGVFMXpaV3htSTJwMWJXSm1QUzlqTW5CaEwzVnlianBqTW5CaE9qWmlPREJtWW1JNExXWXlaVE10TkdKbU9DMWhNakV3TFRobE1EZzROakpsWXpNd09TOWpNbkJoTG5OcFoyNWhkSFZ5WldwcGJuTjBZVzVqWlVsRWVDeDRiWEE2YVdsa09qYzNNalEzWWpoaExUTmpOVEl0TkRJMVl5MWlOamswTFdWa05XRXhaR1psWWpjd09ISmpjbVZoZEdWa1gyRnpjMlZ5ZEdsdmJuT0RvbU4xY214NExYTmxiR1lqYW5WdFltWTlZekp3WVM1aGMzTmxjblJwYjI1ekwyTXljR0V1YVc1bmNtVmthV1Z1ZEM1Mk0yUm9ZWE5vV0NCdzI2WlYwVVA4N1FzY1Nmc3FLUVN5SGpoVUFnOTViUGoxQ0ZKc3ZxMFBBS0pqZFhKc2VDcHpaV3htSTJwMWJXSm1QV015Y0dFdVlYTnpaWEowYVc5dWN5OWpNbkJoTG1GamRHbHZibk11ZGpKa2FHRnphRmdnTFVWK2dBTS9xOEZxYWZ5THZOM0dOZ09ETEhmakxuVUpvemRLd3dSRTBjeWlZM1Z5YkhncGMyVnNaaU5xZFcxaVpqMWpNbkJoTG1GemMyVnlkR2x2Ym5Ndll6SndZUzVvWVhOb0xtUmhkR0ZrYUdGemFGZ2dYMFFReEhzTmI3cU53aFZsM2tzZUNUZTRpenhQNWFUR2lRNTd1Vnd6K0Y1MFkyeGhhVzFmWjJWdVpYSmhkRzl5WDJsdVptK2paRzVoYldWdlFXNTBhSEp2Y0dsaklFWnBiR1Z6WjNabGNuTnBiMjVsTVM0d0xqQnJjM0JsWTFabGNuTnBiMjVsTWk0MExqQUFBQkE0YW5WdFlnQUFBQ2hxZFcxa1l6Smpjd0FSQUJDQUFBQ3FBRGliY1FOak1uQmhMbk5wWjI1aGRIVnlaUUFBQUJBSVkySnZjdEtFV1FJU29nRW1HQ0ZaQWdvd2dnSUdNSUlCamFBREFnRUNBaFJBNWFBSzdzSTUwTDY0Zy9vR1FnVTlaMVVUQURBS0JnZ3Foa2pPUFFRREF6QkpNUmN3RlFZRFZRUUtFdzVCYm5Sb2NtOXdhV01zSUZCQ1F6RXVNQ3dHQTFVRUF4TWxRVzUwYUhKdmNHbGpJRU52Ym5SbGJuUWdRM0psWkdWdWRHbGhiSE1nVW05dmRDQkRRVEFlRncweU5qQTRNRGN4T0RRek5UWmFGdzB5T0RBNE1EWXhPVFF6TlRaYU1FUXhGekFWQmdOVkJBb1REa0Z1ZEdoeWIzQnBZeXdnVUVKRE1Ta3dKd1lEVlFRREV5QkJiblJvY205d2FXTWdRMnhoZFdSbElFTnZiblJsYm5RZ1UybG5ibWx1WnpCWk1CTUdCeXFHU000OUFnRUdDQ3FHU000OUF3RUhBMElBQkpoNkNtdkxVQmdGRk5VMHZVS2xPVnRFNmRqZDE3TDVTdXdYMExlbUZpc0JNM2RrZC8zY3lqeEZBM1FvNVM0NmZYMC9paFkwVlo3bWZiOUtGNzAzdDVPaldEQldNQTRHQTFVZER3RUIvd1FFQXdJSGdEQVZCZ05WSFNVRURqQU1CZ29yQmdFRUFZUG9YZ0lCTUF3R0ExVWRFd0VCL3dRQ01BQXdId1lEVlIwakJCZ3dGb0FVemxIaUJJRk9aRnNqK09QRXo1bytuTUhYWE1Jd0NnWUlLb1pJemowRUF3TURad0F3WkFJd01YTWRGSjRCZXRMTFZZN09SdUU5bm9xYmJBWk9abi9hQXJYeVR3RkFaZktyUHp4RjJ2UG9KTmYxK1VDZGcxWEdBakJ3WDF6ZDlXR3FZa3FtTDVTRnF3MVF5U2pyMXpKZnBKTTkrMXJkRHdTUExNT1BPakt1aVhqb1UvcFVVZUc5UndtaFkzQmhaRmtObmdBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBNkZqYTNYZTMxaEozZXZFMnBnZzRrdnljZlZ5ZGFQYjN3b2pyNjd3TVRrekFBQUJ3WTJKdmNxTnBaR002Wm05eWJXRjBiV2x0WVdkbEwzTjJaeXQ0Yld4cWFXNXpkR0Z1WTJWSlJIZ3NlRzF3T21scFpEbzBPR1prTnpZd05DMHdPVFkyTFRSaE1qVXRPR1ZsTXkwME16RXpaR1F3WkdNeE5tVnNjbVZzWVhScGIyNXphR2x3YUhCaGNtVnVkRTltQUFBQjRtcDFiV0lBQUFCQmFuVnRaR05pYjNJQUVRQVFnQUFBcWdBNG0zRVRZekp3WVM1aFkzUnBiMjV6TG5ZeUFBQUFBQmhqTW5Ob3plTnN1VkRRZGZTcDUyT25lSFFOQWdBQUFabGpZbTl5b21kaFkzUnBiMjV6Z3FKbVlXTjBhVzl1YTJNeWNHRXViM0JsYm1Wa2FuQmhjbUZ0WlhSbGNuT2hhMmx1WjNKbFpHbGxiblJ6Z2FKamRYSnNlQzF6Wld4bUkycDFiV0ptUFdNeWNHRXVZWE56WlhKMGFXOXVjeTlqTW5CaExtbHVaM0psWkdsbGJuUXVkak5rYUdGemFGZ2djTnVtVmRGRC9PMExIRW43S2lrRXNoNDRWQUlQZVd6NDlRaFNiTDZ0RHdDa1ptRmpkR2x2Ym5nZFkyOXRMbUZ1ZEdoeWIzQnBZeTVqYkdGMVpHVXVjSEp2ZG1sa1pXUnFjR0Z5WVcxbGRHVnljNkY0SDJOdmJTNWhiblJvY205d2FXTXViM0pwWjJsdUxXTnZibVpwWkdWdVkyVm5kVzVyYm05M2JtdGtaWE5qY21sd2RHbHZibmhtUTJ4aGRXUmxJSEJ5YjNacFpHVmtJSFJvYVhNZ1ptbHNaU0JoZENCMGFHVWdjbVZ4ZFdWemRDQnZaaUJoSUhWelpYSWdZVzVrSUcxaGVTQm9ZWFpsSUdOeVpXRjBaV1FnYjNJZ2JXOWthV1pwWldRZ2RHaGxJR1pwYkdVZ1kyOXVkR1Z1ZEhNdWJYTnZablIzWVhKbFFXZGxiblNoWkc1aGJXVm1RMnhoZFdSbGNtRnNiRUZqZEdsdmJuTkpibU5zZFdSbFpQVUFBQURJYW5WdFlnQUFBRUJxZFcxa1kySnZjZ0FSQUJDQUFBQ3FBRGliY1JOak1uQmhMbWhoYzJndVpHRjBZUUFBQUFBWVl6SnphTDM0M3Y4NW1OT2NGNFJpS1JZUHEwd0FBQUNBWTJKdmNxVmpZV3huWm5Ob1lUSTFObU53WVdSTkFBQUFBQUFBQUFBQUFBQUFBR1JvWVhOb1dDQUhhTm9OS1NrUlg1aVJNT2kxeXBoV2RjR21rWnA0SVU2L0JqZmN1ajZzcW1SdVlXMWxibXAxYldKbUlHMWhibWxtWlhOMGFtVjRZMngxYzJsdmJuT0JvbVZ6ZEdGeWRCaThabXhsYm1kMGFCa2VCQUFBQWo1cWRXMWlBQUFBSjJwMWJXUmpNbU5zQUJFQUVJQUFBS29BT0p0eEEyTXljR0V1WTJ4aGFXMHVkaklBQUFBQ0QyTmliM0tsWTJGc1oyWnphR0V5TlRacGMybG5ibUYwZFhKbGVFMXpaV3htSTJwMWJXSm1QUzlqTW5CaEwzVnlianBqTW5CaE9qWmlPREJtWW1JNExXWXlaVE10TkdKbU9DMWhNakV3TFRobE1EZzROakpsWXpNd09TOWpNbkJoTG5OcFoyNWhkSFZ5WldwcGJuTjBZVzVqWlVsRWVDeDRiWEE2YVdsa09qYzNNalEzWWpoaExUTmpOVEl0TkRJMVl5MWlOamswTFdWa05XRXhaR1psWWpjd09ISmpjbVZoZEdWa1gyRnpjMlZ5ZEdsdmJuT0RvbU4xY214NExYTmxiR1lqYW5WdFltWTlZekp3WVM1aGMzTmxjblJwYjI1ekwyTXljR0V1YVc1bmNtVmthV1Z1ZEM1Mk0yUm9ZWE5vV0NCdzI2WlYwVVA4N1FzY1Nmc3FLUVN5SGpoVUFnOTViUGoxQ0ZKc3ZxMFBBS0pqZFhKc2VDcHpaV3htSTJwMWJXSm1QV015Y0dFdVlYTnpaWEowYVc5dWN5OWpNbkJoTG1GamRHbHZibk11ZGpKa2FHRnphRmdnTFVWK2dBTS9xOEZxYWZ5THZOM0dOZ09ETEhmakxuVUpvemRLd3dSRTBjeWlZM1Z5YkhncGMyVnNaaU5xZFcxaVpqMWpNbkJoTG1GemMyVnlkR2x2Ym5Ndll6SndZUzVvWVhOb0xtUmhkR0ZrYUdGemFGZ2dYMFFReEhzTmI3cU53aFZsM2tzZUNUZTRpenhQNWFUR2lRNTd1Vnd6K0Y1MFkyeGhhVzFmWjJWdVpYSmhkRzl5WDJsdVptK2paRzVoYldWdlFXNTBhSEp2Y0dsaklFWnBiR1Z6WjNabGNuTnBiMjVsTVM0d0xqQnJjM0JsWTFabGNuTnBiMjVsTWk0MExqQUFBQkE0YW5WdFlnQUFBQ2hxZFcxa1l6Smpjd0FSQUJDQUFBQ3FBRGliY1FOak1uQmhMbk5wWjI1aGRIVnlaUUFBQUJBSVkySnZjdEtFV1FJU29nRW1HQ0ZaQWdvd2dnSUdNSUlCamFBREFnRUNBaFJBNWFBSzdzSTUwTDY0Zy9vR1FnVTlaMVVUQURBS0JnZ3Foa2pPUFFRREF6QkpNUmN3RlFZRFZRUUtFdzVCYm5Sb2NtOXdhV01zSUZCQ1F6RXVNQ3dHQTFVRUF4TWxRVzUwYUhKdmNHbGpJRU52Ym5SbGJuUWdRM0psWkdWdWRHbGhiSE1nVW05dmRDQkRRVEFlRncweU5qQTRNRGN4T0RRek5UWmFGdzB5T0RBNE1EWXhPVFF6TlRaYU1FUXhGekFWQmdOVkJBb1REa0Z1ZEdoeWIzQnBZeXdnVUVKRE1Ta3dKd1lEVlFRREV5QkJiblJvY205d2FXTWdRMnhoZFdSbElFTnZiblJsYm5RZ1UybG5ibWx1WnpCWk1CTUdCeXFHU000OUFnRUdDQ3FHU000OUF3RUhBMElBQkpoNkNtdkxVQmdGRk5VMHZVS2xPVnRFNmRqZDE3TDVTdXdYMExlbUZpc0JNM2RrZC8zY3lqeEZBM1FvNVM0NmZYMC9paFkwVlo3bWZiOUtGNzAzdDVPaldEQldNQTRHQTFVZER3RUIvd1FFQXdJSGdEQVZCZ05WSFNVRURqQU1CZ29yQmdFRUFZUG9YZ0lCTUF3R0ExVWRFd0VCL3dRQ01BQXdId1lEVlIwakJCZ3dGb0FVemxIaUJJRk9aRnNqK09QRXo1bytuTUhYWE1Jd0NnWUlLb1pJemowRUF3TURad0F3WkFJd01YTWRGSjRCZXRMTFZZN09SdUU5bm9xYmJBWk9abi9hQXJYeVR3RkFaZktyUHp4RjJ2UG9KTmYxK1VDZGcxWEdBakJ3WDF6ZDlXR3FZa3FtTDVTRnF3MVF5U2pyMXpKZnBKTTkrMXJkRHdTUExNT1BPakt1aVhqb1UvcFVVZUc5UndtaFkzQmhaRmtObmdBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQVR2QUFBQUFBQUFBQUFBQUFBNkZqYTNYZTMxaEozZXZFMnBnZzRrdnljZlZ5ZGFQYjN3b2pyZ2tqZzQxTEhYUVJ2c2tLekZrdnljSVdrcWRYQlltU2dZSFZ2QUFBQUFYQUFBQUFjQ1BBQU13QUNRQVpBQUFBQUFFT293QkJBQVFBQUFRQUFBSlZBQUFBQUFjQkFBQ0FBQUFDQUFBUVVBQUVBSFFBQUFBQUFQQUFBQUFBQUFBQUFBQXdBQUFBQUJnQUJnQUJnQUJnQUJvQUFBREFCRUFEQUFBQUFBQ0NBQ1FBT0FBSXhnQUFnQUFTQUFBQURRQUJBQWhBQUNNQkFnQUdBT0FBQWp3QUFnQUFBQUFBQURRQUJBOFRRQUFvQU1BQnhBQ2dBTGdCQ0FDZ0FEQUFBRndCYUFBYUFBUk1BREFBUkFBQUFBQ1lBSGdCRUFEY0FMQUFBQUF3QUVBQUFvQUJBQUF1QUJBQUF1QURBQXRBRVlBQXdBQ0FCRUFHQ0FEQUE0QUFvQUVBQVVBREFBUUFBSUFJQUFqQUFBQWRBQUFBQWdBRUFBUkFBQUFMQUFFQUJBQVdBSXdBQndBQUFEb0FBUUNBQUFBQUFBQUFBQUFCQUFBQUFBY0FBQUFBQVFFQUZBQVpBQVVBQUFBQUFBQXRBTndBQXdBRUFBQkFBQUFBQUFBN0FIUUFEQUFnQUFBQUFBQWdBRVlBQXdBTUFCRUFCQUFSQUFBQUFBYWFBQkFBRUFBU0FDRUFCQUFSQUFBQUFBYWFBQ0VBSkFBQUFBRUFBUWdBQUFBQWdBQUFBQUFCQ0FBd0FBQUE4QkFBQUFCQUFBeWdBQUFCQUFBREFBQUFBQUFBQUFHNEFBQUFBQVFBQWlBQUFBQUVBQUFBQkFBQUFBQUFBQUFBQUFBQUFBQUFFQUFBQUFBUUFBQkFBQUFDRUFDd0FEQUFSQUJFQUJnQUFBQVNBQUFBRUFCUUFGQUFMQUF3QUd3QWdBQUFBQUFBYUFBNkZqYTNYZTMxaEozZXZFMnBnZzRrdnljZlZ5ZGFQYjN3b2pyZ2tqZzQxTEhYUVJ2c2tLekZrdnljSVdrcWRYQlltU2dZSFZ2QUFBQUFYQUFBQUFjQ1BBQU13QUNRQVpBQUFBQUFFT293QkJBQVFBQUFRQUFBSlZBQUFBQUFjQkFBQ0FBQUFDQUFBUVVBQUVBSFFBQUFBQUFQQUFBQUFBQUFBQUFBQXdBQUFBQUJnQUJnQUJnQUJnQUJvQUFBREFCRUFEQUFBQUFBQ0NBQ1FBT0FBSXhnQUFnQUFTQUFBQURRQUJBQWhBQUNNQkFnQUdBT0FBQWp3QUFnQUFBQUFBQURRQUJBOFRRQUFvQU1BQnhBQ2dBTGdCQ0FDZ0FEQUFBRndCYUFBYUFBUk1BREFBUkFBQUFBQ1lBSGdCRUFEY0FMQUFBQUF3QUVBQUFvQUJBQUF1QUJBQUF1QURBQXRBRVlBQXdBQ0FCRUFHQ0FEQUE0QUFvQUVBQVVBREFBUUFBSUFJQUFqQUFBQWRBQUFBQWdBRUFBUkFBQUFMQUFFQUJBQVdBSXdBQndBQUFEb0FBUUNBQUFBQUFBQUFBQUFCQUFBQUFBY0FBQUFBQVFFQUZBQVpBQVVBQUFBQUFBQXRBTndBQXdBRUFBQkFBQUFBQUFBN0FIUUFEQUFnQUFBQUFBQWdBRVlBQXdBTUFCRUFCQUFSQUFBQUFBYWFBQkFBRUFBU0FDRUFCQUFSQUFBQUFBYWFBQ0VBSkFBQUFBRUFBUWdBQUFBQWdBQUFBQUFCQ0FBd0FBQUE4QkFBQUFCQUFBeWdBQUFCQUFBREFBQUFBQUFBQUFHNEFBQUFBQVFBQWlBQUFBQUVBQUFBQkFBQUFBQUFBQUFBQUFBQUFBQUFFQUFBQUFBUUFBQkFBQUFDRUFDd0FEQUFSQUJFQUJnQUFBQVNBQUFBRUFCUUFGQUFMQUF3QUd3QWdBQUFBQUFBYUFBOEZqYTNYZTMxaEozZXZFMnBnZzRrdnljZlZ5ZGFQYjN3b2pyZ2tqZzQxTEhYUVJ2c2tLekZrdnljSVdrcWRYQlltU2dZSFZ2QUFBQUFYQUFBQUFjQ1BBQU13QUNRQVpBQUFBQUFFT293QkJBQVFBQUFRQUFBSlZBQUFBQUFjQkFBQ0FBQUFDQUFBUVVBQUVBSFFBQUFBQUFQQUFBQUFBQUFBQUFBQXdBQUFBQUJnQUJnQUJnQUJnQUJvQUFBREFCRUFEQUFBQUFBQ0NBQ1FBT0FBSXhnQUFnQUFTQUFBQURRQUJBQWhBQUNNQkFnQUdBT0FBQWp3QUFnQUFBQUFBQURRQUJBOFRRQUFvQU1BQnhBQ2dBTGdCQ0FDZ0FEQUFBRndCYUFBYUFBUk1BREFBUkFBQUFBQ1lBSGdCRUFEY0FMQUFBQUF3QUVBQUFvQUJBQUF1QUJBQUF1QURBQXRBRVlBQXdBQ0FCRUFHQ0FEQUE0QUFvQUVBQVVBREFBUUFBSUFJQUFqQUFBQWRBQUFBQWdBRUFBUkFBQUFMQUFFQUJBQVdBSXdBQndBQUFEb0FBUUNBQUFBQUFBQUFBQUFCQUFBQUFBY0FBQUFBQVFFQUZBQVpBQVVBQUFBQUFBQXRBTndBQXdBRUFBQkFBQUFBQUFBN0FIUUFEQUFnQUFBQUFBQWdBRVlBQXdBTUFCRUFCQUFSQUFBQUFBYWFBQkFBRUFBU0FDRUFCQUFSQUFBQUFBYWFBQ0VBSkFBQUFBRUFBUWdBQUFBQWdBQUFBQUFCQ0FBd0FBQUE4QkFBQUFCQUFBeWdBQUFCQUFBREFBQUFBQUFBQUFHNEFBQUFBQVFBQWlBQUFBQUVBQUFBQkFBQUFBQUFBQUFBQUFBQUFBQUFFQUFBQUFBUUFBQkFBQUFDRUFDd0FEQUFSQUJFQUJnQUFBQVNBQUFBRUFCUUFGQUFMQUF3QUd3QWdBQUFBQUFBYUE9PQ=="};
  AV.id = AV.ob;
  AV.report = AV.router;
'''
print(len(av_str), len(avsvg_str))
