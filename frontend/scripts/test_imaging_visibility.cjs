const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('http://localhost:5173/case-room.html');
  await page.waitForTimeout(2000);
  
  // Step 1: Check active case without imaging (e.g. Susan Jones)
  const step1 = await page.evaluate(() => {
    const sec = document.getElementById('dossier-sec-imaging');
    return {
      hidden: sec && sec.style.display === 'none',
      count: document.querySelectorAll('.imaging-card').length,
      name: document.getElementById('pt-name')?.textContent
    };
  });
  console.log('Step 1 (Admitted patient without imaging has hidden section):', step1);

  // Step 2: Populate a case with actual imaging data
  const step2 = await page.evaluate(() => {
    const elena = {
      name: 'Elena Vance',
      mrn: '#VH-8921-OB',
      demog: '32F · G2P1 (34+2 wks)',
      esi: 2,
      acuity: 'ESI 2 · Emergent',
      acuityClass: 'esi2',
      chief_complaint: 'Severe headache, blurred vision',
      hpi: 'Presenting with acute-onset severe headache.',
      vitals: [
        { label: 'BP', val: '178/112', unit: 'mmHg', status: 'abnormal' },
        { label: 'HR', val: '88', unit: 'bpm', status: 'normal' },
        { label: 'RR', val: '18', unit: '/min', status: 'normal' },
        { label: 'SpO₂', val: '98%', unit: 'RA', status: 'normal' },
        { label: 'Temp', val: '36.8', unit: '°C', status: 'normal' },
        { label: 'GCS', val: '15', unit: '/15', status: 'normal' }
      ],
      labs: [],
      imaging: [
        {
          title: 'Bedside RUQ Ultrasound',
          mod: 'POCUS Scan',
          desc: 'Liver capsule intact, no subcapsular haematoma; gallbladder normal',
          modalText: 'Normal gallbladder'
        }
      ]
    };
    window.__vhPopulateSidebar(elena);
    const sec = document.getElementById('dossier-sec-imaging');
    return {
      visible: sec && sec.style.display !== 'none',
      count: document.querySelectorAll('.imaging-card').length,
      name: document.getElementById('pt-name')?.textContent,
      title: document.querySelector('.imaging-title')?.textContent
    };
  });
  console.log('Step 2 (Case with imaging displays section and card):', step2);

  // Step 3: Populate back to empty imaging
  const step3 = await page.evaluate(() => {
    const noImgCase = {
      name: 'No Img Case',
      mrn: '#VH-0000',
      demog: '20M',
      esi: 3,
      acuity: 'ESI 3 · Urgent',
      acuityClass: 'esi3',
      chief_complaint: 'Anxiety',
      hpi: 'Mild symptoms.',
      vitals: [
        { label: 'BP', val: '120/80', unit: 'mmHg', status: 'normal' },
        { label: 'HR', val: '72', unit: 'bpm', status: 'normal' },
        { label: 'RR', val: '16', unit: '/min', status: 'normal' },
        { label: 'SpO₂', val: '99%', unit: 'RA', status: 'normal' },
        { label: 'Temp', val: '36.6', unit: '°C', status: 'normal' },
        { label: 'GCS', val: '15', unit: '/15', status: 'normal' }
      ],
      labs: [],
      imaging: []
    };
    window.__vhPopulateSidebar(noImgCase);
    const sec = document.getElementById('dossier-sec-imaging');
    return {
      hidden: sec && sec.style.display === 'none',
      count: document.querySelectorAll('.imaging-card').length,
      name: document.getElementById('pt-name')?.textContent
    };
  });
  console.log('Step 3 (Switching back hides section completely):', step3);

  await browser.close();

  if (step1.hidden && step2.visible && step2.count === 1 && step3.hidden) {
    console.log('>>> SUCCESS: All verification steps passed seamlessly!');
    process.exit(0);
  } else {
    process.exit(1);
  }
})();
