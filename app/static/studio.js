const parcel = document.querySelector('#parcel');
const order = document.querySelector('#job-form');
const note = document.querySelector('#studio-feedback');
function target(sample, key) {
  const url = new URL(location.href);
  url.searchParams.set('sample', sample);
  if (key) url.searchParams.set('key', key);
  else url.searchParams.delete('key');
  return url;
}
parcel.addEventListener('change', () => location.assign(target(parcel.value)));
document.querySelector('#print-receipt').addEventListener('click', () => window.print());
order.addEventListener('submit', async event => {
  event.preventDefault();
  const button = order.querySelector('[type=submit]');
  button.disabled = true;
  note.hidden = false;
  note.textContent = '正在封存秤单';
  try {
    const response = await fetch('/api/books', {method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({sample: parcel.value})});
    const saved = await response.json();
    if (!response.ok) throw new Error(saved.message);
    const next = target(parcel.value, saved.key);
    if (next.href === location.href) note.textContent = '同一收据留档已复用';
    else location.assign(next);
  } catch (error) {
    note.textContent = error.message || '封存失败，请重试';
  } finally {
    button.disabled = false;
  }
});
const pots = document.querySelector('#pot-filter');
pots?.addEventListener('change', () => {
  for (const row of document.querySelectorAll('#pot-lines tr')) {
    row.hidden = pots.value !== 'all' && row.dataset.pot !== pots.value;
  }
});
