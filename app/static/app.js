'use strict';
const byId = id => document.getElementById(id);

function cell(text) {
  const el = document.createElement('td');
  el.textContent = String(text);
  return el;
}
async function requestJson(url, options = undefined) {
  const response = await fetch(url, options);
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try { detail += ': ' + JSON.stringify(await response.json()); } catch (_) { /* ответ мог быть не JSON */ }
    throw new Error(detail);
  }
  return await response.json();
}
async function showProduct(id) {
  const url = `/api/products/${id}`;
  byId('request').textContent = `GET ${url}`;
  byId('status').textContent = 'Получение данных…';
  byId('status').className = 'muted';
  try {
    const result = await requestJson(url);
    byId('result').textContent = JSON.stringify(result, null, 2);
    byId('status').textContent = 'Ответ получен: HTTP 200 OK';
  } catch (err) {
    byId('result').textContent = '—';
    byId('status').className = 'error';
    byId('status').textContent = String(err.message);
  }
}
async function loadCatalog() {
  byId('counter').textContent = 'Загрузка данных…';
  try {
    const {data, meta} = await requestJson('/api/products');
    const body = byId('items');
    body.replaceChildren();
    for (const product of data) {
      const row = document.createElement('tr');
      const idCell = document.createElement('td');
      const link = document.createElement('a');
      link.href = `/api/products/${product.id}`;
      link.className = 'idlink';
      link.textContent = String(product.id);
      link.title = `Получить устройство с ID ${product.id}`;
      link.addEventListener('click', event => {event.preventDefault();void showProduct(product.id);});
      idCell.append(link);
      row.append(idCell, cell(product.name), cell(product.type), cell(product.status), cell(product.price));
      const raw = document.createElement('td');
      const jsonLink = document.createElement('a');
      jsonLink.href = `/api/products/${product.id}`;
      jsonLink.textContent = 'Открыть';
      jsonLink.target = '_blank';
      jsonLink.rel = 'noopener';
      raw.append(jsonLink); row.append(raw); body.append(row);
    }
    if (!data.length) {const row=document.createElement('tr');const td=cell('В каталоге нет устройств');td.colSpan=6;row.append(td);body.append(row);}
    byId('counter').textContent = `Показано: ${meta.count} · Всего: ${meta.total}`;
  } catch (err) {
    const row=document.createElement('tr');const td=cell('Не удалось загрузить каталог');td.colSpan=6;row.append(td);byId('items').replaceChildren(row);
    byId('counter').textContent = err.message;
  }
}
byId('reload').addEventListener('click', () => void loadCatalog());
byId('reset').addEventListener('click', async () => {
  if (!confirm('Восстановить исходные 5 устройств? Все изменения будут потеряны.')) return;
  try {
    await requestJson('/api/reset', {method: 'POST'});
    byId('request').textContent='Выберите ID из таблицы';
    byId('result').textContent='—';
    byId('status').textContent='Исходные данные восстановлены';
    byId('status').className='muted';
    await loadCatalog();
  } catch(err) {byId('status').textContent=err.message;byId('status').className='error';}
});
void loadCatalog();
