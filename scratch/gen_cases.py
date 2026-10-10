# -*- coding: utf-8 -*-
"""
Clinical Cases Module for case-room.html
Contains 5 comprehensive clinical cases with 7 canonical agents:
im, ca, ne, su, em, ob, gy.
Strictly clinical SI units, ESI levels, and no human doctor names.
"""

CASES_CODE = '''
const CASES = {
  preeclampsia_hellp: {
    id: 'preeclampsia_hellp',
    synthetic: true,
    name: 'Elena Vance',
    mrn: '#VH-8921-OB',
    demog: '32F · G2P1 (34+2 wks)',
    esi: 2,
    acuity: 'ESI 2 · Emergent',
    acuityClass: 'esi2',
    chief_complaint: 'Severe throbbing frontal headache, blurred vision with floaters, sharp right upper quadrant pain.',
    hpi: '32-year-old female at 34+2 weeks gestation presenting with acute-onset severe headache unresponsive to acetaminophen, persistent scotomas, and worsening RUQ pain over the past 6 hours.',
    vitals: [
      { label: 'BP', val: '178/112', unit: 'mmHg', status: 'abnormal' },
      { label: 'HR', val: '88', unit: 'bpm', status: 'normal' },
      { label: 'RR', val: '18', unit: '/min', status: 'normal' },
      { label: 'SpO₂', val: '98%', unit: 'RA', status: 'normal' },
      { label: 'Temp', val: '36.8', unit: '°C', status: 'normal' },
      { label: 'GCS', val: '15', unit: '/15', status: 'normal' }
    ],
    labs: [
      { name: 'Platelets', val: '62 ×10⁹/L', ref: '150-400', flag: 'Low', status: 'low' },
      { name: 'AST / ALT', val: '210 / 195 U/L', ref: '<35', flag: 'High', status: 'high' },
      { name: 'LDH', val: '680 U/L', ref: '140-280', flag: 'High', status: 'high' },
      { name: 'Bilirubin', val: '31 µmol/L', ref: '3-21', flag: 'High', status: 'high' },
      { name: 'Urine PCR', val: '1.8 mg/mg', ref: '<0.3', flag: 'High', status: 'high' },
      { name: 'Creatinine', val: '97 µmol/L', ref: '45-84', flag: 'High', status: 'high' },
      { name: 'Hemoglobin', val: '118 g/L', ref: '110-140', flag: 'Normal', status: 'normal' },
      { name: 'WBC Count', val: '8.4 ×10⁹/L', ref: '4.5-11.0', flag: 'Normal', status: 'normal' },
      { name: 'Fibrinogen', val: '3.8 g/L', ref: '2.0-4.0', flag: 'Normal', status: 'normal' },
      { name: 'Sodium', val: '138 mmol/L', ref: '135-145', flag: 'Normal', status: 'normal' },
      { name: 'Potassium', val: '4.1 mmol/L', ref: '3.5-5.0', flag: 'Normal', status: 'normal' },
      { name: 'Glucose', val: '5.2 mmol/L', ref: '4.0-7.0', flag: 'Normal', status: 'normal' }
    ],
    imaging: [
      {
        title: 'Bedside RUQ Ultrasound',
        mod: 'POCUS Scan',
        desc: 'Liver capsule intact, no subcapsular haematoma; gallbladder normal',
        icon: 'scan',
        modalText: '<b>Findings:</b> Homogeneous liver parenchyma without subcapsular fluid collection or hematoma. Normal gallbladder without wall thickening or pericholecystic fluid. No intraperitoneal free fluid in Morison pouch.'
      },
      {
        title: 'Continuous Cardiotocography',
        mod: 'Fetal Monitoring',
        desc: 'Baseline 140 bpm, moderate variability, reactive non-stress pattern',
        icon: 'ecg',
        modalText: '<b>Findings:</b> Baseline fetal heart rate 140 bpm with moderate variability and recurrent variable decelerations. Reactive non-stress test; no sustained fetal distress at present.'
      }
    ],
    dx: 'Preeclampsia with severe features complicated by HELLP syndrome',
    conf: 0.96,
    ddx: [
      { id: 'aflp', t: 'Acute fatty liver of pregnancy (AFLP)' },
      { id: 'ttp', t: 'Thrombotic thrombocytopenic purpura (TTP)' },
      { id: 'chole', t: 'Acute cholecystitis' }
    ],
    watchFor: 'focal neurological deficit, intractable headache, capsular hematoma, pulmonary edema',
    plan: [
      { id: 'stabilise', own: ['em'], t: '<b>Resuscitation:</b> Left lateral tilt, two large-bore IV lines, seizure precautions, continuous fetal monitoring.' },
      { id: 'antihypertensive', own: ['ob', 'ca'], t: '<b>Severe BP Control:</b> IV labetalol 20 mg bolus, titrate every 10 min. Target BP 140–150 / 90–100 mmHg.' },
      { id: 'mgso4', own: ['ob', 'ne'], t: '<b>Eclampsia Prophylaxis:</b> Magnesium sulfate 4 g IV over 20 min, then 1 g/h continuous infusion.' },
      { id: 'surgical_eval', own: ['su'], t: '<b>Surgical Clearance:</b> Emergency bedside ultrasound ruled out subcapsular hepatic hematoma.' },
      { id: 'delivery', own: ['ob'], t: '<b>Expedited Delivery:</b> Maternal stabilization followed by urgent induction/cesarean section once platelet transfusion available.' }
    ],
    router: {
      routedAt: '14:17',
      primary: 'ob',
      consult: 'su',
      scores: { ob: 97, em: 92, im: 88, ca: 81, ne: 79, su: 64, gy: 18 },
      status: { ob: 'lead', em: 'assigned', im: 'assigned', ca: 'assigned', ne: 'assigned', su: 'assigned', gy: 'standby' },
      assigned: ['ob', 'em', 'im', 'ca', 'ne', 'su'],
      standby: ['gy'],
      rationale: 'Severe preeclampsia with HELLP features at 34 weeks gestation requires Obstetrics lead with multidisciplinary stabilization.'
    },
    events: [
      {
        who: 'ob',
        to: 'board',
        kind: 'assess',
        short: "Severe preeclampsia with HELLP criteria met; initiate MgSO4 and labetalol",
        detail: "Blood pressure 178/112 with platelets 62 ×10⁹/L and transaminitis meets criteria for HELLP syndrome per <em>Williams Obstetrics, Ch. 24</em>. Immediate magnesium sulfate neuroprotection and IV labetalol indicated.",
        voice: "Blood pressure 178 over 112 with low platelets confirms severe HELLP syndrome.",
        agreeWith: ['ob'],
        planAgrees: ['stabilise'],
        dxDelta: { aflp: 0.12, ttp: 0.08, chole: 0.05 }
      },
      {
        who: 'ca',
        to: 'ob',
        kind: 'assess',
        short: "Concur on urgent IV labetalol 20 mg bolus",
        detail: "Cerebrovascular and myocardial perfusion pressure must be preserved while lowering afterload safely (<em>Braunwald Heart Disease, Ch. 88</em>). Titrate IV labetalol 20 to 80 mg.",
        voice: "Start IV labetalol 20 mg immediately to protect maternal cerebral vasculature.",
        agreeWith: ['ob', 'ca'],
        planAgrees: ['antihypertensive'],
        dxDelta: { aflp: 0.08, ttp: 0.06 }
      },
      {
        who: 'ne',
        to: 'ob',
        kind: 'assess',
        short: "Magnesium sulfate 4 g bolus indicated for PRES prophylaxis",
        detail: "Persistent scotomas and frontal headache reflect severe cerebrovascular autoregulatory breakthrough. Magnesium sulfate provides NMDA receptor blockade and cerebral vasodilation (<em>Adams and Victor's Principles of Neurology, Ch. 34</em>).",
        voice: "Initiate 4-gram magnesium sulfate bolus for seizure and PRES prophylaxis.",
        agreeWith: ['ob', 'ca', 'ne'],
        planAgrees: ['mgso4'],
        dxDelta: { aflp: 0.06 }
      },
      {
        who: 'ob',
        to: 'su',
        kind: 'referral',
        short: "REFERRAL: Urgent General Surgery consult for sharp RUQ pain",
        detail: "Patient has severe RUQ pain and dropping platelets. Requesting urgent surgical evaluation to rule out hepatic capsular hematoma or rupture before operative delivery.",
        voice: "Requesting surgical consult: severe RUQ tenderness to rule out hepatic hematoma.",
        agreeWith: ['ob', 'ca', 'ne'],
        planAgrees: [],
        dxDelta: {}
      },
      {
        who: 'su',
        to: 'ob',
        kind: 'consult_reply',
        short: "Bedside ultrasound confirms intact liver capsule; cleared for delivery",
        detail: "Bedside POCUS confirms intact hepatic capsule with no subcapsular collection or Morison pouch free fluid (<em>Schwartz's Principles of Surgery, Ch. 31</em>). Cleared for obstetric intervention with surgical standby.",
        voice: "Bedside scan confirms intact liver capsule without hematoma. Surgical clearance granted.",
        agreeWith: ['ob', 'ca', 'ne', 'su'],
        planAgrees: ['surgical_eval'],
        dxDelta: { chole: 0.02 }
      },
      {
        who: 'im',
        to: 'ob',
        kind: 'assess',
        short: "Crossmatch 4 units platelets; normal fibrinogen rules out AFLP",
        detail: "Normal fibrinogen distinguishes HELLP from acute fatty liver of pregnancy or overt DIC (<em>Harrison's Principles of Internal Medicine, Ch. 142</em>). Crossmatching platelet pack for delivery.",
        voice: "Platelets crossmatched. Normal fibrinogen confirms HELLP over AFLP.",
        agreeWith: ['ob', 'ca', 'ne', 'su', 'im'],
        planAgrees: [],
        dxDelta: { aflp: 0.02, ttp: 0.02 }
      },
      {
        who: 'em',
        to: 'ob',
        kind: 'assess',
        short: "Two large-bore IV access secured; neonatal team alerted",
        detail: "Resuscitation bay prepared, two 16G lines placed, neonatal intensive care team alerted for 34-week preterm delivery (<em>Tintinalli's Emergency Medicine, Ch. 100</em>).",
        voice: "Resuscitation bay secured and neonatal ICU team alerted for delivery.",
        agreeWith: ['ob', 'ca', 'ne', 'su', 'im', 'em'],
        planAgrees: ['stabilise'],
        dxDelta: {}
      },
      {
        who: 'ob',
        to: 'board',
        kind: 'consensus',
        short: "Consensus reached: Maternal stabilization followed by expedited delivery",
        detail: "Obstetrics, Cardiology, Neurology, Surgery, Internal Medicine, and Emergency Medicine agree on definitive protocol: antihypertensive control, neuroprotection, and delivery upon maternal stabilization.",
        voice: "Consensus finalized: maternal stabilization followed by expedited delivery.",
        agreeWith: ['ob', 'ca', 'ne', 'su', 'im', 'em'],
        planAgrees: ['delivery'],
        dxDelta: { aflp: 0.01, ttp: 0.01, chole: 0.01 }
      }
    ]
  },

  septic_shock_mrsa: {
    id: 'septic_shock_mrsa',
    synthetic: true,
    name: 'Marcus Thorne',
    mrn: '#VH-4109-IM',
    demog: '58M · Post-TKR (Day 14)',
    esi: 1,
    acuity: 'ESI 1 · Resuscitation',
    acuityClass: 'esi1',
    chief_complaint: 'High spiking fever (39.4°C), severe shaking rigors, progressive lethargy, erythematous painful right knee.',
    hpi: '58-year-old male 2 weeks status-post right total knee arthroplasty presenting with acute septic shock: profound hypotension refractory to initial 1L fluid bolus, marked joint effusion, and spreading warm erythema.',
    vitals: [
      { label: 'BP', val: '82/48', unit: 'mmHg', status: 'abnormal' },
      { label: 'HR', val: '124', unit: 'bpm', status: 'abnormal' },
      { label: 'RR', val: '26', unit: '/min', status: 'abnormal' },
      { label: 'SpO₂', val: '93%', unit: 'RA', status: 'abnormal' },
      { label: 'Temp', val: '39.4', unit: '°C', status: 'abnormal' },
      { label: 'GCS', val: '13', unit: '/15', status: 'abnormal' }
    ],
    labs: [
      { name: 'Blood Cultures', val: 'Gram + Cocci in clusters', ref: 'Negative', flag: 'Critical', status: 'critical' },
      { name: 'Lactic Acid', val: '4.2 mmol/L', ref: '0.5-2.0', flag: 'High', status: 'high' },
      { name: 'WBC Count', val: '24.8 ×10⁹/L', ref: '4.5-11.0', flag: 'High', status: 'high' },
      { name: 'Procalcitonin', val: '18.5 µg/L', ref: '<0.1', flag: 'High', status: 'high' },
      { name: 'Creatinine', val: '186 µmol/L', ref: '62-106', flag: 'High', status: 'high' },
      { name: 'Platelets', val: '118 ×10⁹/L', ref: '150-400', flag: 'Low', status: 'low' },
      { name: 'Hemoglobin', val: '132 g/L', ref: '130-175', flag: 'Normal', status: 'normal' },
      { name: 'Bilirubin', val: '14 µmol/L', ref: '3-21', flag: 'Normal', status: 'normal' },
      { name: 'Sodium', val: '134 mmol/L', ref: '135-145', flag: 'Normal', status: 'normal' },
      { name: 'Potassium', val: '4.4 mmol/L', ref: '3.5-5.0', flag: 'Normal', status: 'normal' },
      { name: 'AST', val: '32 U/L', ref: '<35', flag: 'Normal', status: 'normal' },
      { name: 'ALT', val: '28 U/L', ref: '<35', flag: 'Normal', status: 'normal' }
    ],
    imaging: [
      {
        title: 'Right Knee Plain Radiograph & US',
        mod: 'Bedside POCUS',
        desc: 'Prosthetic hardware intact; large intra-articular effusion with echogenic debris',
        icon: 'scan',
        modalText: '<b>Findings:</b> Large intra-articular suprapatellar effusion with dense echogenic debris. Hardware intact without gross loosening; significant soft tissue inflammatory edema.'
      },
      {
        title: 'Portable Chest Radiograph',
        mod: 'Chest X-Ray',
        desc: 'Clear lung fields bilaterally without focal consolidation or septic emboli',
        icon: 'scan',
        modalText: '<b>Findings:</b> Clear lung fields bilaterally without focal consolidation, pneumothorax, or cavitary septic emboli.'
      }
    ],
    dx: 'Septic shock secondary to prosthetic joint MRSA bacteremia with multi-organ dysfunction',
    conf: 0.98,
    ddx: [
      { id: 'strep', t: 'Streptococcal toxic shock syndrome' },
      { id: 'gout', t: 'Acute polyarticular crystalline arthropathy' },
      { id: 'endocarditis', t: 'Acute MRSA infective endocarditis' }
    ],
    watchFor: 'refractory vasoplegic shock, ARDS, DIC, metastatic spinal epidural abscess',
    plan: [
      { id: 'pressors', own: ['em', 'ca'], t: '<b>Resuscitation:</b> 30 mL/kg balanced crystalloid plus norepinephrine infusion targeting MAP ≥ 65 mmHg.' },
      { id: 'antimicrobial', own: ['im'], t: '<b>Bactericidal Therapy:</b> Immediate IV Vancomycin (loading 25–30 mg/kg) plus Cefepime.' },
      { id: 'arthrocentesis', own: ['su'], t: '<b>Source Control:</b> Emergent joint aspiration followed by operative irrigation & debridement (DAIR).' },
      { id: 'tee_echo', own: ['ca'], t: '<b>Endocarditis Screen:</b> Transthoracic & transesophageal echocardiogram to rule out valvular vegetations.' },
      { id: 'renal_support', own: ['im'], t: '<b>AKI Monitoring:</b> Strict hourly urine output; dose-adjust antibiotics to renal clearance.' }
    ],
    router: {
      routedAt: '09:24',
      primary: 'im',
      consult: 'su',
      scores: { im: 96, em: 93, su: 89, ca: 78, ne: 65, ob: 12, gy: 12 },
      status: { im: 'lead', em: 'assigned', su: 'assigned', ca: 'assigned', ne: 'assigned', ob: 'standby', gy: 'standby' },
      assigned: ['im', 'em', 'su', 'ca', 'ne'],
      standby: ['ob', 'gy'],
      rationale: 'MRSA bacteremia with refractory septic shock and prosthetic joint infection requires Internal Medicine lead with immediate Surgery consult.'
    },
    events: [
      {
        who: 'im',
        to: 'board',
        kind: 'assess',
        short: "Septic shock from MRSA prosthetic joint infection",
        detail: "Blood cultures demonstrating Gram-positive cocci in clusters with lactate 4.2 mmol/L confirms fulminant MRSA septic shock (<em>Harrison's Principles of Internal Medicine, Ch. 138</em>). Load vancomycin 25-30 mg/kg immediately.",
        voice: "Gram-positive bacteremia and high lactate confirm severe MRSA septic shock.",
        agreeWith: ['im'],
        planAgrees: ['antimicrobial'],
        dxDelta: { strep: 0.15, gout: 0.05, endocarditis: 0.25 }
      },
      {
        who: 'em',
        to: 'im',
        kind: 'assess',
        short: "Norepinephrine started; MAP targeted at 65 mmHg",
        detail: "Crystalloid bolus running via pressure bag. Peripheral norepinephrine running via dedicated line while central venous catheter placed (<em>Tintinalli's Emergency Medicine, Ch. 151</em>).",
        voice: "Norepinephrine running to maintain mean arterial pressure above 65.",
        agreeWith: ['im', 'em'],
        planAgrees: ['pressors'],
        dxDelta: { gout: 0.02 }
      },
      {
        who: 'im',
        to: 'su',
        kind: 'referral',
        short: "REFERRAL: Urgent Orthopedic Surgery consult for arthrotomy & DAIR",
        detail: "Prosthetic joint biofilm cannot be sterilized with antibiotics alone in setting of septic shock. Requesting immediate surgical arthrocentesis and operative debridement.",
        voice: "Requesting urgent orthopedic surgery consult for joint aspiration and operative washout.",
        agreeWith: ['im', 'em'],
        planAgrees: [],
        dxDelta: {}
      },
      {
        who: 'su',
        to: 'im',
        kind: 'consult_reply',
        short: "OR activated for emergent knee arthrotomy & liner exchange",
        detail: "Joint aspiration yielded 60 mL purulent synovial fluid. OR team mobilized for debridement, antibiotics, and implant retention (DAIR) protocol (<em>Schwartz's Principles of Surgery, Ch. 42</em>).",
        voice: "OR team activated. Proceeding with urgent joint debridement and polyethylene exchange.",
        agreeWith: ['im', 'em', 'su'],
        planAgrees: ['arthrocentesis'],
        dxDelta: { gout: 0.01 }
      },
      {
        who: 'ca',
        to: 'im',
        kind: 'assess',
        short: "Echo ordered; troponin elevated secondary to septic demand",
        detail: "S. aureus bacteremia carries 25% incidence of infective endocarditis. Urgent echocardiography ordered once hemodynamically stabilized in ICU (<em>Braunwald's Heart Disease, Ch. 64</em>).",
        voice: "Urgent echocardiogram ordered to rule out septic valvular vegetations.",
        agreeWith: ['im', 'em', 'su', 'ca'],
        planAgrees: ['tee_echo'],
        dxDelta: { endocarditis: 0.12 }
      },
      {
        who: 'im',
        to: 'board',
        kind: 'consensus',
        short: "Consensus reached: Dual medical resuscitation and emergent surgical source control",
        detail: "Full agreement across Internal Medicine, Emergency Medicine, Surgery, and Cardiology. Protocol synchronized for OR transfer under continuous pressor support.",
        voice: "Consensus reached: aggressive antimicrobial coverage with immediate surgical source control.",
        agreeWith: ['im', 'em', 'su', 'ca', 'ne'],
        planAgrees: ['pressors', 'antimicrobial', 'arthrocentesis', 'tee_echo', 'renal_support'],
        dxDelta: { strep: 0.02, gout: 0.01, endocarditis: 0.08 }
      }
    ]
  },

  stemi_cardiogenic: {
    id: 'stemi_cardiogenic',
    synthetic: true,
    name: 'Arthur Pendelton',
    mrn: '#VH-7822-CA',
    demog: '67M · Hx CAD, T2DM',
    esi: 1,
    acuity: 'ESI 1 · Resuscitation',
    acuityClass: 'esi1',
    chief_complaint: 'Crushing substernal chest pressure, profuse diaphoresis, dyspnea, and near-syncope.',
    hpi: '67-year-old male presenting with acute severe substernal pressure radiating to jaw and left arm for 90 minutes. Exam shows mottled extremities, bibasilar rales, and profound cardiogenic shock.',
    vitals: [
      { label: 'BP', val: '84/52', unit: 'mmHg', status: 'abnormal' },
      { label: 'HR', val: '108', unit: 'bpm', status: 'abnormal' },
      { label: 'RR', val: '24', unit: '/min', status: 'abnormal' },
      { label: 'SpO₂', val: '91%', unit: 'RA', status: 'abnormal' },
      { label: 'Temp', val: '36.6', unit: '°C', status: 'normal' },
      { label: 'GCS', val: '14', unit: '/15', status: 'normal' }
    ],
    labs: [
      { name: 'hs-Troponin I', val: '4,200 ng/L', ref: '<14', flag: 'High', status: 'high' },
      { name: 'Lactate', val: '3.6 mmol/L', ref: '0.5-2.0', flag: 'High', status: 'high' },
      { name: 'NT-proBNP', val: '3,800 pg/mL', ref: '<300', flag: 'High', status: 'high' },
      { name: 'Arterial pH', val: '7.28', ref: '7.35-7.45', flag: 'Low', status: 'low' },
      { name: 'Potassium', val: '4.8 mmol/L', ref: '3.5-5.0', flag: 'Normal', status: 'normal' },
      { name: 'Hemoglobin', val: '138 g/L', ref: '135-175', flag: 'Normal', status: 'normal' },
      { name: 'Creatinine', val: '102 µmol/L', ref: '62-106', flag: 'Normal', status: 'normal' },
      { name: 'Sodium', val: '139 mmol/L', ref: '135-145', flag: 'Normal', status: 'normal' },
      { name: 'WBC Count', val: '9.2 ×10⁹/L', ref: '4.5-11.0', flag: 'Normal', status: 'normal' },
      { name: 'Platelets', val: '240 ×10⁹/L', ref: '150-400', flag: 'Normal', status: 'normal' },
      { name: 'Glucose', val: '8.4 mmol/L', ref: '4.0-7.0', flag: 'High', status: 'high' },
      { name: 'Bilirubin', val: '12 µmol/L', ref: '3-21', flag: 'Normal', status: 'normal' }
    ],
    imaging: [
      {
        title: '12-Lead Electrocardiogram',
        mod: 'Diagnostic ECG',
        desc: 'Sinus tachycardia 108 bpm; 4mm ST elevation V1-V4 with reciprocal inferior depression',
        icon: 'ecg',
        modalText: '<b>Findings:</b> Sinus tachycardia at 108 bpm with 4 mm ST-segment elevation in leads V1-V4, reciprocal ST depression in leads II, III, and aVF. Meets criteria for acute anterior STEMI.'
      },
      {
        title: 'Bedside Echocardiogram',
        mod: 'Focus Cardiac US',
        desc: 'LVEF 28%, extensive anterior and apical wall akinesis without pericardial effusion',
        icon: 'scan',
        modalText: '<b>Findings:</b> Severely reduced left ventricular ejection fraction (~28%) with large anterior, anteroseptal, and apical akinesis. No pericardial tamponade or acute severe mitral regurgitation.'
      }
    ],
    dx: 'Acute anterolateral STEMI complicated by cardiogenic shock (Killip Class IV)',
    conf: 0.99,
    ddx: [
      { id: 'dissection', t: 'Acute Stanford Type A aortic dissection' },
      { id: 'pe', t: 'Massive pulmonary embolism' },
      { id: 'tamponade', t: 'Acute cardiac tamponade' }
    ],
    watchFor: 'ventricular arrhythmias, mechanical papillary muscle rupture, refractory arrest',
    plan: [
      { id: 'cath_lab', own: ['ca'], t: '<b>Primary PCI:</b> Emergent cardiac catheterization for proximal LAD occlusion.' },
      { id: 'circulatory', own: ['ca', 'su'], t: '<b>Mechanical Support:</b> Pre-PCI placement of microaxial flow pump (Impella CP) for LV venting.' },
      { id: 'inotropes', own: ['em', 'ca'], t: '<b>Hemodynamics:</b> Norepinephrine titration with judicious inotrope (dobutamine) for cardiac index support.' },
      { id: 'antiplatelet', own: ['ca'], t: '<b>Antithrombotic:</b> Aspirin 325 mg chewed, unfractionated heparin bolus, deferred P2Y12 until anatomy defined.' },
      { id: 'airway', own: ['em'], t: '<b>Oxygenation:</b> High-flow nasal cannula; non-invasive positive pressure if pulmonary edema worsens.' }
    ],
    router: {
      routedAt: '11:05',
      primary: 'ca',
      consult: 'su',
      scores: { ca: 98, em: 94, su: 88, im: 82, ne: 60, ob: 10, gy: 10 },
      status: { ca: 'lead', em: 'assigned', su: 'assigned', im: 'assigned', ne: 'assigned', ob: 'standby', gy: 'standby' },
      assigned: ['ca', 'em', 'su', 'im', 'ne'],
      standby: ['ob', 'gy'],
      rationale: 'ECG ST elevation in V1-V4 with cardiogenic shock mandates immediate Cardiology lead with Cardiovascular Surgery/Cath lab activation.'
    },
    events: [
      {
        who: 'ca',
        to: 'board',
        kind: 'assess',
        short: "Anterolateral STEMI with Killip IV cardiogenic shock",
        detail: "ECG shows 4mm ST elevations V1-V4 with troponin 4,200 ng/L and cardiogenic shock (<em>Braunwald's Heart Disease, Ch. 58</em>). Cath lab activated with target door-to-balloon < 60 minutes.",
        voice: "Acute anterolateral STEMI with cardiogenic shock. Cath lab activated immediately.",
        agreeWith: ['ca'],
        planAgrees: ['cath_lab', 'antiplatelet'],
        dxDelta: { dissection: 0.08, pe: 0.05, tamponade: 0.02 }
      },
      {
        who: 'em',
        to: 'ca',
        kind: 'assess',
        short: "Norepinephrine running; aspirin administered",
        detail: "Aspirin 325 mg given. High-flow oxygen started for SpO₂ 91%. Norepinephrine initiated for MAP goal 65 mmHg (<em>Tintinalli's Emergency Medicine, Ch. 53</em>).",
        voice: "Aspirin given and norepinephrine titrated to support perfusion.",
        agreeWith: ['ca', 'em'],
        planAgrees: ['inotropes', 'airway'],
        dxDelta: { pe: 0.03 }
      },
      {
        who: 'ca',
        to: 'su',
        kind: 'referral',
        short: "REFERRAL: Surgical & Perfusion consult for Impella / ECMO standby",
        detail: "Given severe LV dysfunction (EF 28%) and rising lactate, patient requires upfront mechanical circulatory support. Requesting cardiovascular surgical team for femoral access and Impella CP standby.",
        voice: "Requesting cardiovascular surgical consult for Impella circulatory support placement.",
        agreeWith: ['ca', 'em'],
        planAgrees: [],
        dxDelta: {}
      },
      {
        who: 'su',
        to: 'ca',
        kind: 'consult_reply',
        short: "Surgical and perfusion teams assembled in hybrid cath lab",
        detail: "Vascular access equipment and Impella CP console prepped in Hybrid OR/Cath Lab. Standby for surgical revascularization if anatomy unsuitable for stenting (<em>Schwartz's Principles of Surgery, Ch. 22</em>).",
        voice: "Surgical team ready in hybrid lab with Impella console prepped.",
        agreeWith: ['ca', 'em', 'su'],
        planAgrees: ['circulatory'],
        dxDelta: { dissection: 0.02 }
      },
      {
        who: 'ca',
        to: 'board',
        kind: 'consensus',
        short: "Consensus reached: Immediate transfer to Cath Lab with mechanical support",
        detail: "Unanimous specialist agreement: Emergency stabilization, upfront Impella placement, and primary PCI to restore LAD patency.",
        voice: "Consensus finalized: immediate transfer to cath lab with mechanical circulatory support.",
        agreeWith: ['ca', 'em', 'su', 'im', 'ne'],
        planAgrees: ['cath_lab', 'circulatory', 'inotropes', 'antiplatelet', 'airway'],
        dxDelta: { dissection: 0.01, pe: 0.01, tamponade: 0.01 }
      }
    ]
  },

  ischemic_stroke_lvo: {
    id: 'ischemic_stroke_lvo',
    synthetic: true,
    name: 'Clara Oswald',
    mrn: '#VH-9013-NE',
    demog: '74F · Atrial Fibrillation',
    esi: 1,
    acuity: 'ESI 1 · Resuscitation',
    acuityClass: 'esi1',
    chief_complaint: 'Acute right-sided hemiplegia, global aphasia, forced leftward eye gaze deviation.',
    hpi: '74-year-old female with history of atrial fibrillation presenting with sudden onset right dense hemiparesis and complete inability to speak witnessed 45 minutes prior. NIH Stroke Scale score is 18.',
    vitals: [
      { label: 'BP', val: '186/102', unit: 'mmHg', status: 'abnormal' },
      { label: 'HR', val: '82', unit: 'bpm', status: 'normal' },
      { label: 'RR', val: '16', unit: '/min', status: 'normal' },
      { label: 'SpO₂', val: '97%', unit: 'RA', status: 'normal' },
      { label: 'Temp', val: '36.7', unit: '°C', status: 'normal' },
      { label: 'Blood Glucose', val: '6.5', unit: 'mmol/L', status: 'normal' }
    ],
    labs: [
      { name: 'INR', val: '1.1', ref: '0.8-1.2', flag: 'Normal', status: 'normal' },
      { name: 'Platelets', val: '220 ×10⁹/L', ref: '150-400', flag: 'Normal', status: 'normal' },
      { name: 'Troponin', val: '<6 ng/L', ref: '<14', flag: 'Normal', status: 'normal' },
      { name: 'Creatinine', val: '80 µmol/L', ref: '45-84', flag: 'Normal', status: 'normal' },
      { name: 'Hemoglobin', val: '128 g/L', ref: '115-160', flag: 'Normal', status: 'normal' },
      { name: 'WBC Count', val: '6.8 ×10⁹/L', ref: '4.5-11.0', flag: 'Normal', status: 'normal' },
      { name: 'Sodium', val: '139 mmol/L', ref: '135-145', flag: 'Normal', status: 'normal' },
      { name: 'Potassium', val: '4.0 mmol/L', ref: '3.5-5.0', flag: 'Normal', status: 'normal' },
      { name: 'aPTT', val: '28 s', ref: '25-35', flag: 'Normal', status: 'normal' },
      { name: 'Bilirubin', val: '10 µmol/L', ref: '3-21', flag: 'Normal', status: 'normal' },
      { name: 'AST', val: '22 U/L', ref: '<35', flag: 'Normal', status: 'normal' },
      { name: 'ALT', val: '19 U/L', ref: '<35', flag: 'Normal', status: 'normal' }
    ],
    imaging: [
      {
        title: 'Non-Contrast Head CT',
        mod: 'CT Neuro',
        desc: 'ASPECTS 9, hyperdense left MCA sign, no intracranial hemorrhage or mass effect',
        icon: 'scan',
        modalText: '<b>Findings:</b> No evidence of intracranial hemorrhage or significant mass effect. Hyperdense left MCA sign present. Alberta Stroke Program Early CT Score (ASPECTS) is 9/10, indicating minimal early ischemic core.'
      },
      {
        title: 'CT Angiography (Head & Neck)',
        mod: 'CTA Neuro',
        desc: 'Abrupt cutoff of left M1 segment MCA with robust collateral reconstitution',
        icon: 'scan',
        modalText: '<b>Findings:</b> Abrupt cutoff of the proximal left middle cerebral artery (M1 segment) with good collateral vessel reconstitution over the left cerebral convexity.'
      }
    ],
    dx: 'Acute ischemic stroke secondary to cardioembolic left M1 MCA large vessel occlusion (NIHSS 18)',
    conf: 0.99,
    ddx: [
      { id: 'ich', t: 'Acute intracerebral hemorrhage' },
      { id: 'todd', t: 'Todd paralysis post-focal seizure' },
      { id: 'migraine', t: 'Hemiplegic migraine' }
    ],
    watchFor: 'hemorrhagic transformation, malignant cerebral edema, acute herniation',
    plan: [
      { id: 'bp_target', own: ['ne', 'em'], t: '<b>BP Management:</b> IV labetalol bolus to maintain BP < 185/110 mmHg prior to thrombolysis.' },
      { id: 'thrombolysis', own: ['ne', 'em'], t: '<b>Intravenous Thrombolysis:</b> IV Tenecteplase 0.25 mg/kg bolus within 4.5h therapeutic window.' },
      { id: 'thrombectomy', own: ['su', 'ne'], t: '<b>Endovascular Thrombectomy:</b> Emergent groin puncture and stent-retriever thrombectomy for M1 occlusion.' },
      { id: 'neuro_checks', own: ['ne'], t: '<b>Neurological Monitoring:</b> NIHSS checks every 15 minutes during procedure and recovery.' }
    ],
    router: {
      routedAt: '08:12',
      primary: 'ne',
      consult: 'su',
      scores: { ne: 98, em: 93, su: 91, ca: 76, im: 72, ob: 10, gy: 10 },
      status: { ne: 'lead', em: 'assigned', su: 'assigned', ca: 'assigned', im: 'assigned', ob: 'standby', gy: 'standby' },
      assigned: ['ne', 'em', 'su', 'ca', 'im'],
      standby: ['ob', 'gy'],
      rationale: 'Acute focal neurological deficit with NIHSS 18 within thrombolytic window requires Neurology lead with Neurointerventional Surgery consult.'
    },
    events: [
      {
        who: 'ne',
        to: 'board',
        kind: 'assess',
        short: "Left M1 MCA occlusion; candidate for bridging IV TNK and EVT",
        detail: "Onset 45 min ago, non-contrast CT excludes hemorrhage (ASPECTS 9), CTA confirms left M1 cutoff (<em>Adams and Victor's Principles of Neurology, Ch. 34</em>). Eligible for immediate IV Tenecteplase and mechanical thrombectomy.",
        voice: "Left M1 occlusion with ASPECTS 9. Candidate for tenecteplase and thrombectomy.",
        agreeWith: ['ne'],
        planAgrees: ['neuro_checks'],
        dxDelta: { ich: 0.01, todd: 0.02, migraine: 0.01 }
      },
      {
        who: 'em',
        to: 'ne',
        kind: 'assess',
        short: "Labetalol administered; BP adjusted to 172/94 mmHg",
        detail: "BP successfully titrated under 185/110 mmHg. Tenecteplase 0.25 mg/kg mixed and ready for IV administration (<em>Tintinalli's Emergency Medicine, Ch. 165</em>).",
        voice: "Blood pressure optimized with labetalol. Tenecteplase ready to bolus.",
        agreeWith: ['ne', 'em'],
        planAgrees: ['bp_target', 'thrombolysis'],
        dxDelta: { ich: 0.01 }
      },
      {
        who: 'ne',
        to: 'su',
        kind: 'referral',
        short: "REFERRAL: Neurointerventional surgery consult for emergent EVT",
        detail: "Patient has large vessel occlusion with large salvageable penumbra. Requesting emergent neurointerventional surgical activation for endovascular mechanical thrombectomy.",
        voice: "Requesting neurointerventional consult: emergent endovascular thrombectomy indicated.",
        agreeWith: ['ne', 'em'],
        planAgrees: [],
        dxDelta: {}
      },
      {
        who: 'su',
        to: 'ne',
        kind: 'consult_reply',
        short: "Angio suite ready; proceeding to direct mechanical recanalization",
        detail: "Neurointerventional team in room. Transferring patient directly from CT scanner to Biplane Angiography suite for aspiration & stent-retriever thrombectomy (<em>Schwartz's Principles of Surgery, Ch. 41</em>).",
        voice: "Angiography suite prepped. Transferring directly for mechanical clot extraction.",
        agreeWith: ['ne', 'em', 'su'],
        planAgrees: ['thrombectomy'],
        dxDelta: { todd: 0.01 }
      },
      {
        who: 'ne',
        to: 'board',
        kind: 'consensus',
        short: "Consensus reached: Dual bridging thrombolysis and endovascular thrombectomy",
        detail: "Unanimous clinical consensus: IV TNK bolus followed immediately by groin puncture for mechanical recanalization.",
        voice: "Consensus finalized: immediate bridging tenecteplase and mechanical thrombectomy.",
        agreeWith: ['ne', 'em', 'su', 'ca', 'im'],
        planAgrees: ['bp_target', 'thrombolysis', 'thrombectomy', 'neuro_checks'],
        dxDelta: { ich: 0.00, todd: 0.01, migraine: 0.00 }
      }
    ]
  },

  acute_appendicitis: {
    id: 'acute_appendicitis',
    synthetic: true,
    name: 'Jordan Rivera',
    mrn: '#VH-6291-SU',
    demog: '24M · Previously Healthy',
    esi: 2,
    acuity: 'ESI 2 · Emergent',
    acuityClass: 'esi2',
    chief_complaint: 'Periumbilical pain migrating to right lower quadrant, nausea, anorexia, and fever.',
    hpi: '24-year-old male presenting with 18 hours of progressively worsening abdominal pain initially periumbilical, now localized to McBurney point with marked rebound tenderness and low-grade pyrexia.',
    vitals: [
      { label: 'BP', val: '124/78', unit: 'mmHg', status: 'normal' },
      { label: 'HR', val: '102', unit: 'bpm', status: 'normal' },
      { label: 'RR', val: '18', unit: '/min', status: 'normal' },
      { label: 'SpO₂', val: '99%', unit: 'RA', status: 'normal' },
      { label: 'Temp', val: '38.2', unit: '°C', status: 'abnormal' },
      { label: 'GCS', val: '15', unit: '/15', status: 'normal' }
    ],
    labs: [
      { name: 'WBC Count', val: '16.4 ×10⁹/L', ref: '4.5-11.0', flag: 'High', status: 'high' },
      { name: 'C-Reactive Protein', val: '48 mg/L', ref: '<5', flag: 'High', status: 'high' },
      { name: 'Serum Lipase', val: '24 U/L', ref: '10-60', flag: 'Normal', status: 'normal' },
      { name: 'Creatinine', val: '78 µmol/L', ref: '62-106', flag: 'Normal', status: 'normal' },
      { name: 'Hemoglobin', val: '148 g/L', ref: '130-175', flag: 'Normal', status: 'normal' },
      { name: 'Platelets', val: '260 ×10⁹/L', ref: '150-400', flag: 'Normal', status: 'normal' },
      { name: 'Bilirubin', val: '11 µmol/L', ref: '3-21', flag: 'Normal', status: 'normal' },
      { name: 'Sodium', val: '140 mmol/L', ref: '135-145', flag: 'Normal', status: 'normal' },
      { name: 'Potassium', val: '4.2 mmol/L', ref: '3.5-5.0', flag: 'Normal', status: 'normal' },
      { name: 'Glucose', val: '5.6 mmol/L', ref: '4.0-7.0', flag: 'Normal', status: 'normal' },
      { name: 'AST', val: '24 U/L', ref: '<35', flag: 'Normal', status: 'normal' },
      { name: 'ALT', val: '22 U/L', ref: '<35', flag: 'Normal', status: 'normal' }
    ],
    imaging: [
      {
        title: 'Abdominal & Pelvic CT with IV Contrast',
        mod: 'CT Scan',
        desc: 'Dilated appendix (9.5mm), prominent fat stranding, obstructing appendicolith at base',
        icon: 'scan',
        modalText: '<b>Findings:</b> Blind-ending, non-compressible tubular structure in the right lower quadrant measuring 9.5 mm in outer diameter with an obstructing appendicolith at the base. Prominent periappendiceal fat stranding and localized peritoneal thickening without generalized free air.'
      }
    ],
    dx: 'Acute gangrenous appendicitis with periappendiceal phlegmon',
    conf: 0.99,
    ddx: [
      { id: 'mesenteric', t: 'Acute mesenteric adenitis' },
      { id: 'crohn', t: 'Terminal ileitis / Crohn disease' },
      { id: 'colic', t: 'Right ureteral calculus' }
    ],
    watchFor: 'peritoneal sepsis, microperforation, intra-abdominal abscess formation',
    plan: [
      { id: 'npo', own: ['su', 'em'], t: '<b>Pre-Operative Care:</b> NPO status, IV crystalloid resuscitation, analgesia.' },
      { id: 'antibiotics', own: ['im', 'su'], t: '<b>Antimicrobial Prophylaxis:</b> IV Piperacillin-tazobactam or Cefoxitin 2 g within 60 min of incision.' },
      { id: 'lap_app', own: ['su'], t: '<b>Definitive Surgery:</b> Emergent laparoscopic appendectomy.' },
      { id: 'dvt_ppx', own: ['im'], t: '<b>Perioperative Care:</b> Sequential compression devices and early ambulation.' }
    ],
    router: {
      routedAt: '16:40',
      primary: 'su',
      consult: 'im',
      scores: { su: 98, em: 90, im: 84, ca: 52, ne: 40, ob: 10, gy: 10 },
      status: { su: 'lead', em: 'assigned', im: 'assigned', ca: 'assigned', ne: 'assigned', ob: 'standby', gy: 'standby' },
      assigned: ['su', 'em', 'im', 'ca', 'ne'],
      standby: ['ob', 'gy'],
      rationale: 'Migratory RLQ pain, leukocytosis, and CT imaging confirming dilated 9.5mm appendix with appendicolith requires Surgery lead with Internal Medicine antibiotic consultation.'
    },
    events: [
      {
        who: 'su',
        to: 'board',
        kind: 'assess',
        short: "Acute appendicitis confirmed on CT; laparoscopic surgery scheduled",
        detail: "Alvarado score 9/10 with CT confirming 9.5 mm obstructed appendix and appendicolith (<em>Schwartz's Principles of Surgery, Ch. 30</em>). Patient scheduled for emergent laparoscopic appendectomy.",
        voice: "CT confirms acute appendicitis. Scheduling emergent laparoscopic appendectomy.",
        agreeWith: ['su'],
        planAgrees: ['npo'],
        dxDelta: { mesenteric: 0.05, crohn: 0.04, colic: 0.01 }
      },
      {
        who: 'em',
        to: 'su',
        kind: 'assess',
        short: "IV fluids running; multimodal analgesia provided",
        detail: "Ringer lactate bolus initiated. Acetaminophen and fentanyl administered for pain control without compromising abdominal exam (<em>Tintinalli's Emergency Medicine, Ch. 73</em>).",
        voice: "IV hydration and analgesia administered; patient comfortable and NPO.",
        agreeWith: ['su', 'em'],
        planAgrees: ['npo'],
        dxDelta: { colic: 0.01 }
      },
      {
        who: 'su',
        to: 'im',
        kind: 'referral',
        short: "REFERRAL: Internal Medicine consult for antimicrobial prophylaxis",
        detail: "CT shows prominent fat stranding and appendicolith raising concern for micro-perforation. Requesting Internal Medicine recommendation for pre-operative coverage.",
        voice: "Requesting Internal Medicine consult: optimal antibiotic regimen for micro-perforation risk.",
        agreeWith: ['su', 'em'],
        planAgrees: [],
        dxDelta: {}
      },
      {
        who: 'im',
        to: 'su',
        kind: 'consult_reply',
        short: "Recommend IV Piperacillin-tazobactam for anaerobic & enteric coverage",
        detail: "Given localized peritonitis, recommend IV Piperacillin-tazobactam 3.375g to cover enteric gram-negatives and Bacteroides fragilis (<em>Harrison's Principles of Internal Medicine, Ch. 129</em>). Continue 24h post-op if uncomplicated.",
        voice: "Recommend intravenous piperacillin-tazobactam for anaerobic and enteric coverage.",
        agreeWith: ['su', 'em', 'im'],
        planAgrees: ['antibiotics'],
        dxDelta: { mesenteric: 0.02, crohn: 0.02 }
      },
      {
        who: 'su',
        to: 'board',
        kind: 'consensus',
        short: "Consensus reached: Proceed to OR for laparoscopic appendectomy",
        detail: "Surgery, Internal Medicine, and Emergency Medicine aligned. Patient prepped for laparoscopic intervention.",
        voice: "Consensus reached: proceeding directly to operating room for laparoscopic appendectomy.",
        agreeWith: ['su', 'em', 'im'],
        planAgrees: ['npo', 'antibiotics', 'lap_app', 'dvt_ppx'],
        dxDelta: { mesenteric: 0.01, crohn: 0.01, colic: 0.00 }
      }
    ]
  }
};
'''
