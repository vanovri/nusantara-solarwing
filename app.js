/* Reproducible energy screening. All plotted observations come from cached NASA POWER data. */
(() => {
  'use strict';
  const data = window.NATUNA_DATA;
  const select = document.getElementById('daySelect');
  const slider = document.getElementById('loadSlider');
  const canvas = document.getElementById('powerChart');
  if (!data || !select || !slider || !canvas) return;

  const A = data.assumptions;
  const pack = A.pack_nominal_wh;
  const solarFactor = A.pv_area_m2 * A.pv_efficiency * A.mppt_efficiency;
  const byDate = new Map(data.days.map(day => [day.date, day]));
  const presets = [...document.querySelectorAll('[data-day]')];
  const fmt = (number, digits = 0) => Number(number).toLocaleString('en-US', {maximumFractionDigits: digits, minimumFractionDigits: digits});

  function mission(day, load) {
    let energy = pack * 0.9;
    let minimum = energy;
    let depleted = false;
    const states = [];
    for (let hour = 8; hour < 16; hour++) {
      const solar = Math.max(0, day.hours_wh_m2[hour]) * solarFactor;
      const balance = solar - load;
      energy = Math.max(0, Math.min(pack, energy + balance * (balance >= 0 ? 0.95 : 1 / 0.95)));
      depleted ||= energy === 0;
      minimum = Math.min(minimum, energy);
      states.push(energy / pack * 100);
    }
    return {min: minimum / pack * 100, end: energy / pack * 100, pass: minimum >= pack * 0.2, depleted, states};
  }

  for (const day of data.days) {
    const option = document.createElement('option');
    option.value = day.date;
    option.textContent = new Date(`${day.date}T12:00:00Z`).toLocaleDateString('en-US', {day: '2-digit', month: 'short', year: 'numeric'});
    select.append(option);
  }
  select.value = '2025-09-03';

  function set(id, value) { document.getElementById(id).textContent = value; }

  function render() {
    const day = byDate.get(select.value);
    const load = Number(slider.value);
    const result = mission(day, load);
    const passCount = data.days.filter(d => mission(d, load).pass).length;
    const margin = result.min - 20;
    set('loadOutput', `${fmt(load, 1)} W`);
    set('dateLabel', day.date.toUpperCase());
    set('resultTitle', result.pass ? 'Reserve held' : result.depleted ? 'Battery depleted' : 'Reserve breached');
    set('resultDetail', result.pass
      ? `Minimum battery margin is ${fmt(margin, 1)} percentage points above the 20% floor. This modeled sortie passes the reserve screen.`
      : result.depleted
        ? 'The battery reaches 0% before the sortie ends. Shorten, delay or cancel this modeled mission.'
        : `Battery falls ${fmt(Math.abs(margin), 1)} percentage points below the 20% floor. Shorten, delay or cancel the modeled sortie.`);
    set('minSoc', `${fmt(result.min, 1)}%`);
    set('endSoc', `${fmt(result.end, 1)}%`);
    set('ghiTotal', `${fmt(day.hours_wh_m2.slice(8, 16).reduce((sum, value) => sum + value, 0) / 1000, 2)} kWh/m²`);
    set('passCount', `${passCount}/30`);
    document.getElementById('statusDot').classList.toggle('fail', !result.pass);
    document.getElementById('powerChart').setAttribute('aria-label', `Hourly power for ${day.date}. ${result.pass ? 'Reserve held' : 'Reserve breached'}. Minimum state of charge ${fmt(result.min, 1)} percent.`);
    presets.forEach(button => button.classList.toggle('active', button.dataset.day === day.date));
    drawChart(day, load);
  }

  function drawChart(day, load) {
    const rect = canvas.getBoundingClientRect();
    const width = Math.max(300, rect.width);
    const height = 290;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    const ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);
    const left = 40, right = width - 8, top = 12, bottom = height - 24;
    const chartWidth = right - left, chartHeight = bottom - top;
    const maxSolar = Math.max(...day.hours_wh_m2.map(value => value * solarFactor));
    const maxW = Math.ceil(Math.max(300, maxSolar, load) / 100) * 100;
    const x = hour => left + hour / 24 * chartWidth;
    const y = watts => bottom - watts / maxW * chartHeight;

    ctx.fillStyle = 'rgba(223,170,98,.07)';
    ctx.fillRect(x(8), top, x(16) - x(8), chartHeight);
    ctx.font = '10px DM Mono, monospace';
    ctx.textAlign = 'right';
    for (let value = 0; value <= maxW; value += 100) {
      const py = y(value);
      ctx.strokeStyle = '#315257';
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(left, py); ctx.lineTo(right, py); ctx.stroke();
      ctx.fillStyle = '#9eb8af';
      ctx.fillText(`${value}`, left - 9, py + 3);
    }
    const barWidth = chartWidth / 24 * 0.62;
    day.hours_wh_m2.forEach((ghi, hour) => {
      const watts = Math.max(0, ghi) * solarFactor;
      ctx.fillStyle = '#dfaa62';
      ctx.fillRect(x(hour + .5) - barWidth / 2, y(watts), barWidth, bottom - y(watts));
    });
    ctx.strokeStyle = '#d68c74';
    ctx.lineWidth = 2;
    ctx.setLineDash([7, 5]);
    ctx.beginPath(); ctx.moveTo(x(8), y(load)); ctx.lineTo(x(16), y(load)); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = '#d68c74';
    ctx.textAlign = 'left';
    ctx.fillText(`${fmt(load, 1)} W load`, Math.min(x(16) + 7, width - 115), y(load) + 3);
    ctx.fillStyle = '#a4beb4';
    ctx.textAlign = 'center';
    ctx.fillText('MODELED SORTIE', (x(8) + x(16)) / 2, top + 13);
  }

  select.addEventListener('change', render);
  slider.addEventListener('input', render);
  presets.forEach(button => button.addEventListener('click', () => { select.value = button.dataset.day; render(); }));
  let resizeTimer;
  window.addEventListener('resize', () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(render, 100); });
  render();
})();
