# -*- coding: utf-8 -*-
"""
HTML Markup Module for case-room.html
Implements exact semantic markup from case-room-bugfix audit:
- Single primary control in specialist agents card header (no Start Triage in dossier)
- Clean switch for voice audio
- Full-height abnormal labs with inline expander link
- ESI 2 badge and synthetic badge
- Empty states for Draft and Discussion panels
- 7 canonical agents
"""

def get_html_markup(logo_src):
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Virtual Hospital Case Room — Multidisciplinary AI Deliberation</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Funnel+Display:wght@500;600;700&family=Host+Grotesk:wght@400;500;600;700&display=swap">
<style>
/* CSS will be injected here */
</style>
</head>
<body>

<main class="case-room" id="case">
  <!-- LEFT PANEL: CLINICAL DOSSIER -->
  <aside class="dossier" id="case-sidebar" aria-label="Clinical dossier">
    <div class="dossier-header">
      <h2>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:17px;height:17px;color:var(--indigo)"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
        Clinical Dossier
      </h2>
      <div class="dossier-badges">
        <span class="badge-synthetic" id="dossier-synthetic" hidden>Synthetic case</span>
        <span class="badge-status" id="dossier-status" hidden>Live</span>
      </div>
    </div>

    <!-- Case Selector -->
    <div class="case-select-group">
      <label for="case-select">Select Patient Case</label>
      <select id="case-select" class="case-select"></select>
    </div>

    <!-- Clean Voice Audio Switch -->
    <label class="switch" title="Synthesize brief verbal updates from specialists (Fish Audio)">
      <input type="checkbox" id="voice" role="switch">
      <span>Read agent messages aloud</span>
    </label>

    <!-- Patient Header Card -->
    <div class="patient-card">
      <div class="patient-card-name" id="pt-name">Elena Vance</div>
      <div class="patient-card-id" id="pt-id">#VH-8921-OB</div>
      <div class="patient-card-demog" id="pt-demog">32F · G2P1 (34+2 wks)</div>
      <span class="badge-esi esi2" id="pt-acuity">ESI 2 · Emergent</span>
    </div>

    <!-- Chief Complaint -->
    <div class="dossier-sec">
      <span class="dossier-title">Chief Complaint</span>
      <div class="dossier-text" id="pt-cc">
        Severe throbbing frontal headache, blurred vision with floaters, sharp RUQ pain.
      </div>
    </div>

    <!-- HPI -->
    <div class="dossier-sec">
      <span class="dossier-title">History of Present Illness</span>
      <div class="dossier-text" id="pt-hpi">
        32-year-old female at 34+2 weeks gestation presenting with acute-onset severe headache unresponsive to acetaminophen, scotomas, and worsening RUQ pain over the past 6 hours.
      </div>
    </div>

    <!-- Vitals (3x2 grid, SpO2) -->
    <div class="dossier-sec">
      <span class="dossier-title">Vital Signs</span>
      <div class="vitals-grid" id="vitals-grid">
        <!-- Rendered dynamically -->
      </div>
    </div>

    <!-- Diagnostic Labs (No inner scroll, natural height, abnormal only by default) -->
    <div class="dossier-sec">
      <span class="dossier-title">Diagnostic Labs</span>
      <div class="labs-wrap">
        <div class="labs-list" id="labs-list">
          <!-- Rendered dynamically -->
        </div>
        <button type="button" class="show-all-labs-btn" id="b-show-all-labs">Show all labs (12)</button>
      </div>
    </div>

    <!-- Imaging & Studies (2-line clamp, finding first) -->
    <div class="dossier-sec">
      <span class="dossier-title">Imaging & Studies</span>
      <div class="imaging-list" id="imaging-list">
        <!-- Rendered dynamically -->
      </div>
    </div>
  </aside>

  <!-- RIGHT COLUMN: MAIN WORKSPACE -->
  <div class="case-main">
    <!-- ROUTER CARD -->
    <section class="card router" aria-label="MedGemma routing">
      <div class="rh">
        <img src="{logo_src}" alt="Virtual Hospital" class="vh" style="cursor:pointer;" title="Virtual Hospital Hospital Symbol">
        <h2>MedGemma router</h2>
        <span id="r-sum">Not routed yet</span>
      </div>
      <div class="rcols" id="rcols">
        <!-- 7 Agent Tiles rendered dynamically -->
      </div>
    </section>

    <!-- AGENTS AT WORK & CLINICAL REVIEW (Equal-height grid) -->
    <div class="case-body">
      <!-- SPECIALIST ROOM -->
      <section class="card" aria-label="Specialist agents">
        <div class="ch">
          <h2>Specialist agents</h2>
          <div style="display:flex;align-items:center;gap:12px;">
            <div class="stage">
              <span id="stage-t">Not started</span>
              <span class="segs" aria-hidden="true"><i></i><i></i><i></i><i></i></span>
            </div>
            <div class="controls-wrap">
              <button class="btn-primary-control" id="b-main-control" type="button" aria-label="Route case">
                <svg viewBox="0 0 16 16" fill="currentColor"><polygon points="3.5 2.5 13.5 8 3.5 13.5"/></svg>
                <span>Route case</span>
              </button>
              <button class="btn-replay-icon" id="b-replay" type="button" aria-label="Replay from the start" hidden>
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M2.5 8a5.5 5.5 0 1 0 1.7-4"/><path d="M2.5 2.5v3h3"/></svg>
              </button>
            </div>
          </div>
        </div>
        <div class="room" id="table">
          <canvas id="cv" aria-hidden="true"></canvas>
          <div class="board" id="board" aria-live="polite">
            <b>MedGemma router</b>
            <p>Press Route case to assign specialists.</p>
          </div>
        </div>
        <p class="routed-footer" id="table-footer">Select an agent, here or in the router, to read only its messages.</p>
      </section>

      <!-- WHAT THE PHYSICIAN SIGNS -->
      <section class="card decision" aria-label="Draft for physician review">
        <div class="ch" style="padding-bottom:12px;border-bottom:1px solid var(--hair-2);">
          <div class="seg" role="tablist" aria-label="View">
            <button type="button" role="tab" id="t-draft" aria-selected="true" aria-controls="p-draft">Draft</button>
            <button type="button" role="tab" id="t-disc" aria-selected="false" aria-controls="p-disc">Discussion <em id="count">0</em></button>
          </div>
        </div>

        <!-- DRAFT PANEL (Default tab on load) -->
        <div class="pane" id="p-draft" role="tabpanel" aria-labelledby="t-draft">
          <!-- Empty state in idle -->
          <div class="draft-empty" id="draft-empty">
            <p>No draft yet. Route the case to start the specialist review.</p>
            <div class="draft-empty-outline" aria-hidden="true">
              <div class="draft-empty-line" style="width:45%;"></div>
              <div class="draft-empty-line" style="width:85%;"></div>
              <div class="draft-empty-line" style="width:65%;"></div>
              <div class="draft-empty-line" style="width:75%;margin-top:8px;"></div>
              <div class="draft-empty-line" style="width:90%;"></div>
            </div>
          </div>

          <!-- Dynamic Draft Content -->
          <div id="draft-content" style="display:flex;flex-direction:column;gap:12px;" hidden>
            <div class="dx-l">Working diagnosis</div>
            <h2 class="dx" id="dx">Preeclampsia with severe features</h2>
            <div class="conf">
              <span class="t"><i id="meter" style="width:0%"></i></span>
              <span>Confidence <b id="conf">0.75</b></span>
              <span>·</span>
              <span><b id="agree">0</b> of 6 agree</span>
            </div>
            <p class="note"><b>Less likely:</b> <span id="ddx">acute fatty liver of pregnancy, microangiopathic hemolytic anemia, acute cholecystitis</span>.</p>
            <p class="note"><b>Watch for:</b> <span id="watch-for">focal neurological deficit, intractable headache, capsular hematoma, pulmonary edema</span>.</p>
            
            <div class="plan-h">Actionable Clinical Plan</div>
            <ul class="plan-list" id="plan">
              <!-- Rendered dynamically -->
            </ul>
          </div>
        </div>

        <!-- DISCUSSION PANEL -->
        <div class="pane" id="p-disc" role="tabpanel" aria-labelledby="t-disc" hidden>
          <div class="filter-chip" id="filter-chip" hidden>
            <span id="filter-chip-text">Obstetrics only</span>
            <button type="button" id="b-clear-filter">Show all</button>
          </div>
          <div class="disc-empty" id="disc-empty">Messages appear here as the agents work.</div>
          <div id="disc-list" style="display:flex;flex-direction:column;gap:10px;">
            <!-- Rendered dynamically -->
          </div>
        </div>

        <!-- FOOTER: REVIEW AND SIGN -->
        <div class="sign-box">
          <button class="btn-sign" id="b-sign" type="button" disabled title="Available when the agents agree">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px"><polyline points="20 6 9 17 4 12"/></svg>
            <span>Review and sign</span>
          </button>
        </div>
      </section>
    </div>
  </div>
</main>

<!-- IMAGING MODAL -->
<div class="modal-overlay" id="imaging-modal" hidden>
  <div class="modal-box">
    <div class="modal-head">
      <h3 id="modal-title">Diagnostic Study</h3>
      <button class="modal-close" id="modal-close" type="button" aria-label="Close modal">&times;</button>
    </div>
    <div class="modal-body">
      <div class="modal-preview-box" id="modal-preview"></div>
      <div class="modal-report" id="modal-report"></div>
    </div>
  </div>
</div>

<script>
// Logic injected here
</script>
</body>
</html>
'''
