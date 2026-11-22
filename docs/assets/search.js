'use strict';
(() => {
  const form = document.querySelector('#search-form');
  if (!form) return;
  const query = document.querySelector('#query');
  const year = document.querySelector('#year');
  const volume = document.querySelector('#volume');
  const records = [...document.querySelectorAll('[data-search]')];
  const norm = text => text.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const params = new URLSearchParams(location.search);
  query.value = params.get('q') || '';
  year.value = params.get('year') || '';
  volume.value = params.get('volume') || '';
  function filter(updateURL = true) {
    const words = norm(query.value.trim()).split(/\s+/).filter(Boolean);
    let count = 0;
    for (const record of records) {
      const show = words.every(w => norm(record.dataset.search).includes(w)) && (!year.value || record.dataset.year === year.value) && (!volume.value || record.dataset.volume === volume.value);
      record.hidden = !show;
      if (show) count++;
    }
    document.querySelector('#result-count').textContent = `${count} of ${records.length} articles`;
    document.querySelector('#empty').hidden = count !== 0;
    if (updateURL) {
      const p = new URLSearchParams();
      if (query.value.trim()) p.set('q', query.value.trim());
      if (year.value) p.set('year', year.value);
      if (volume.value) p.set('volume', volume.value);
      history.replaceState(null, '', location.pathname + (p.size ? '?' + p : ''));
    }
  }
  form.addEventListener('submit', e => { e.preventDefault(); filter(); });
  form.addEventListener('input', () => filter());
  form.addEventListener('change', () => filter());
  form.addEventListener('reset', () => { query.value = ''; year.value = ''; volume.value = ''; filter(); });
  filter(false);
})();
