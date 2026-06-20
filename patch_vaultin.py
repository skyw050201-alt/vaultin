#!/usr/bin/env python3
# Patch Vaultin: tambah transaksi berulang (recurring) + kelola kategori (tambah/hapus)
import sys, io

target = sys.argv[1] if len(sys.argv) > 1 else 'index.html'

with io.open(target, 'r', encoding='utf-8') as f:
    c = f.read()

if 'function loadCategories' in c or "objectStore('recurring'" in c.replace('createObjectStore','objectStore') or 'function applyRecurring' in c:
    print('  > File sepertinya sudah dipatch sebelumnya. Tidak ada perubahan.')
    sys.exit(0)

edits = []

# 1) DB version 2 -> 3
edits.append(('DB version',
    "indexedDB.open('VaultinDB', 2)",
    "indexedDB.open('VaultinDB', 3)"))

# 2) tambah object store 'recurring'
edits.append(('recurring store',
    "if (!d.objectStoreNames.contains('assets')) { d.createObjectStore('assets', { keyPath: 'id', autoIncrement: true }); } };",
    "if (!d.objectStoreNames.contains('assets')) { d.createObjectStore('assets', { keyPath: 'id', autoIncrement: true }); } if (!d.objectStoreNames.contains('recurring')) { d.createObjectStore('recurring', { keyPath: 'id', autoIncrement: true }); } };"))

# 3) kategori jadi dinamis (DEFAULT_CATS + let arrays)
CAT_OLD = (
    "const INCOME_CATS = ['Paycheck','Business','Side Hustle','Dividends','Interest Income','Commission'];\n"
    "const EXPENSE_CATS = ['Food','Social Life','Transportation','Household','Apparel','Beauty','Health','Education','Gift','Pet','Self-development','Electronics'];\n"
    "const BILL_CATS = ['Internet','Netflix','Subscription','House Rent','Listrik'];\n"
    "const DEBT_CATS = ['BCA'];\n"
    "const SAVINGS_CATS = ['Travel Fund','Wedding Fund','Car Fund','Stocks','Mutual Funds','Cryptocurrency'];\n"
    "const ALL_CATS = { income: INCOME_CATS, expense: EXPENSE_CATS, bill: BILL_CATS, debt: DEBT_CATS, savings: SAVINGS_CATS };"
)
CAT_NEW = (
    "const DEFAULT_CATS = { income: ['Paycheck','Business','Side Hustle','Dividends','Interest Income','Commission'], expense: ['Food','Social Life','Transportation','Household','Apparel','Beauty','Health','Education','Gift','Pet','Self-development','Electronics'], bill: ['Internet','Netflix','Subscription','House Rent','Listrik'], debt: ['BCA'], savings: ['Travel Fund','Wedding Fund','Car Fund','Stocks','Mutual Funds','Cryptocurrency'] };\n"
    "let INCOME_CATS = [...DEFAULT_CATS.income];\n"
    "let EXPENSE_CATS = [...DEFAULT_CATS.expense];\n"
    "let BILL_CATS = [...DEFAULT_CATS.bill];\n"
    "let DEBT_CATS = [...DEFAULT_CATS.debt];\n"
    "let SAVINGS_CATS = [...DEFAULT_CATS.savings];\n"
    "let ALL_CATS = { income: INCOME_CATS, expense: EXPENSE_CATS, bill: BILL_CATS, debt: DEBT_CATS, savings: SAVINGS_CATS };"
)
edits.append(('kategori dinamis', CAT_OLD, CAT_NEW))

# 4) form-group Kategori -> tambah tombol + Baru / Kelola
CATFORM_OLD = (
    '      <div class="form-group">\n'
    '        <label class="form-label">Kategori</label>\n'
    '        <select class="form-select" id="txnCategory"></select>\n'
    '      </div>'
)
CATFORM_NEW = (
    '      <div class="form-group">\n'
    '        <div class="flex justify-between items-center">\n'
    '          <label class="form-label" style="margin:0">Kategori</label>\n'
    '          <div class="flex gap-2">\n'
    '            <button type="button" class="btn btn-sm btn-secondary" id="addCatBtn">+ Baru</button>\n'
    '            <button type="button" class="btn btn-sm btn-secondary" id="manageCatBtn">Kelola</button>\n'
    '          </div>\n'
    '        </div>\n'
    '        <select class="form-select" id="txnCategory" style="margin-top:var(--sp-2)"></select>\n'
    '      </div>'
)
edits.append(('form kategori', CATFORM_OLD, CATFORM_NEW))

# 5) form-group Transaksi Berulang (sisipkan sebelum hidden txnId)
TXNID_OLD = '      <input type="hidden" id="txnId">'
RECUR_FORM = (
    '      <div class="form-group">\n'
    '        <div class="flex justify-between items-center">\n'
    '          <label class="form-label" style="margin:0">Transaksi Berulang</label>\n'
    '          <button type="button" class="btn btn-sm btn-secondary" id="manageRecurBtn">Kelola</button>\n'
    '        </div>\n'
    '        <label class="flex items-center gap-2" style="cursor:pointer;margin-top:var(--sp-2)">\n'
    '          <input type="checkbox" id="txnRecurring" style="width:18px;height:18px;flex-shrink:0">\n'
    '          <span class="text-muted" style="font-size:var(--fs-sm)">Ulangi otomatis sesuai jadwal</span>\n'
    '        </label>\n'
    '        <div class="form-row" id="recurringFields" style="display:none;margin-top:var(--sp-2)">\n'
    '          <div class="form-group" style="margin:0">\n'
    '            <label class="form-label">Setiap</label>\n'
    '            <input type="number" class="form-input" id="recurInterval" value="1" min="1" step="1">\n'
    '          </div>\n'
    '          <div class="form-group" style="margin:0">\n'
    '            <label class="form-label">Satuan</label>\n'
    '            <select class="form-select" id="recurUnit"><option value="day">Hari</option><option value="week">Minggu</option><option value="month" selected>Bulan</option><option value="year">Tahun</option></select>\n'
    '          </div>\n'
    '        </div>\n'
    '      </div>\n'
)
edits.append(('form berulang', TXNID_OLD, RECUR_FORM + TXNID_OLD))

# 6) reset recurring di openTxnModal
edits.append(('reset openTxnModal',
    "document.getElementById('deleteTxnBtn').style.display = 'none';\n  if (presetType) { selectedTxnType = presetType; } else { selectedTxnType = 'expense'; }",
    "document.getElementById('deleteTxnBtn').style.display = 'none'; var _rc0 = document.getElementById('txnRecurring'); if (_rc0) _rc0.checked = false; var _rf0 = document.getElementById('recurringFields'); if (_rf0) _rf0.style.display = 'none';\n  if (presetType) { selectedTxnType = presetType; } else { selectedTxnType = 'expense'; }"))

# 7) buat aturan recurring di saveTxn
edits.append(('saveTxn recurring',
    "    else { await dbAdd('transactions', txn); }\n",
    "    else { await dbAdd('transactions', txn); }\n    if (!editingTxnId) { var _rc1 = document.getElementById('txnRecurring'); if (_rc1 && _rc1.checked) { var _unit = document.getElementById('recurUnit').value; var _iv = Math.max(1, parseInt(document.getElementById('recurInterval').value, 10) || 1); try { await dbAdd('recurring', { type: selectedTxnType, category: category, amount: amount, description: desc, unit: _unit, intervalN: _iv, startDate: date, nextDate: addInterval(date, _unit, _iv), active: true, createdAt: new Date().toISOString() }); } catch (_) {} } }\n"))

# 8) wiring di initEvents
edits.append(('wiring initEvents',
    "  document.getElementById('saveTxnBtn').addEventListener('click', saveTxn);\n",
    "  document.getElementById('saveTxnBtn').addEventListener('click', saveTxn);\n  (function(){ var rc = document.getElementById('txnRecurring'); if (rc) rc.addEventListener('change', function(){ var f = document.getElementById('recurringFields'); if (f) f.style.display = rc.checked ? 'flex' : 'none'; }); var mrb = document.getElementById('manageRecurBtn'); if (mrb) mrb.addEventListener('click', openManageRecurring); var acb = document.getElementById('addCatBtn'); if (acb) acb.addEventListener('click', async function(){ var n = prompt('Nama kategori baru:'); if (n && n.trim()) { var ok = await addCategory(selectedTxnType, n.trim()); populateCategoryDropdown(); if (ok) { var sel = document.getElementById('txnCategory'); if (sel) sel.value = n.trim(); } } }); var mcb = document.getElementById('manageCatBtn'); if (mcb) mcb.addEventListener('click', openManageCats); })();\n"))

# 9) exportData incl recurring
edits.append(('exportData',
    "const [txns, budgets, goals, assets, settings] = await Promise.all([dbGetAll('transactions'), dbGetAll('budgets'), dbGetAll('savingsGoals'), dbGetAll('assets'), dbGetAll('settings')]); const data = { version: 3, app: 'Vaultin', exportedAt: new Date().toISOString(), transactions: txns, budgets, savingsGoals: goals, assets, settings };",
    "const [txns, budgets, goals, assets, settings, recurring] = await Promise.all([dbGetAll('transactions'), dbGetAll('budgets'), dbGetAll('savingsGoals'), dbGetAll('assets'), dbGetAll('settings'), dbGetAll('recurring').catch(function(){return [];})]); const data = { version: 4, app: 'Vaultin', exportedAt: new Date().toISOString(), transactions: txns, budgets, savingsGoals: goals, assets, settings, recurring: recurring };"))

# 10) importData incl recurring
edits.append(('importData',
    "for (const s of data.settings||[]) { await dbPut('settings', s); } alert('Data berhasil diimport!');",
    "for (const s of data.settings||[]) { await dbPut('settings', s); } for (const r of data.recurring||[]) { await dbPut('recurring', r); } alert('Data berhasil diimport!');"))

# 11) fungsi baru + init
NEW_FUNCS = r"""/* ====== KATEGORI DINAMIS ====== */
async function loadCategories() {
  const custom = (await getSetting('catCustom')) || {};
  const deleted = (await getSetting('catDeleted')) || {};
  for (const type of Object.keys(DEFAULT_CATS)) {
    const del = deleted[type] || [];
    const base = DEFAULT_CATS[type].filter(c => !del.includes(c));
    const add = (custom[type] || []).filter(c => !base.includes(c));
    ALL_CATS[type].length = 0;
    ALL_CATS[type].push(...base, ...add);
  }
}
async function addCategory(type, name) {
  name = (name || '').trim(); if (!name) return false;
  if ((ALL_CATS[type] || []).includes(name)) { alert('Kategori sudah ada.'); return false; }
  const custom = (await getSetting('catCustom')) || {};
  custom[type] = custom[type] || []; if (!custom[type].includes(name)) custom[type].push(name);
  const deleted = (await getSetting('catDeleted')) || {};
  if (deleted[type]) deleted[type] = deleted[type].filter(c => c !== name);
  await dbPut('settings', { key: 'catCustom', value: custom });
  await dbPut('settings', { key: 'catDeleted', value: deleted });
  await loadCategories(); return true;
}
async function deleteCategory(type, name) {
  const custom = (await getSetting('catCustom')) || {};
  if (custom[type] && custom[type].includes(name)) { custom[type] = custom[type].filter(c => c !== name); }
  else { const deleted = (await getSetting('catDeleted')) || {}; deleted[type] = deleted[type] || []; if (!deleted[type].includes(name)) deleted[type].push(name); await dbPut('settings', { key: 'catDeleted', value: deleted }); }
  await dbPut('settings', { key: 'catCustom', value: custom });
  await loadCategories();
}
function openManageCats() {
  const type = selectedTxnType; const label = type.charAt(0).toUpperCase() + type.slice(1);
  let ov = document.getElementById('manageCatsOverlay'); if (ov) ov.remove();
  ov = document.createElement('div'); ov.id = 'manageCatsOverlay'; ov.className = 'modal-overlay active';
  ov.innerHTML = '<div class="modal"><div class="modal-header"><div class="modal-title">Kelola Kategori ' + label + '</div><button class="icon-btn" id="closeManageCats" aria-label="Tutup">\u2715</button></div><div class="modal-body" id="manageCatsBody"></div><div class="modal-footer"><button class="btn btn-primary" id="addCatInManage" style="flex:1">+ Tambah Kategori</button></div></div>';
  document.body.appendChild(ov);
  renderManageCatsBody(type);
  ov.addEventListener('click', e => { if (e.target === ov) ov.remove(); });
  document.getElementById('closeManageCats').addEventListener('click', () => ov.remove());
  document.getElementById('addCatInManage').addEventListener('click', async () => { const n = prompt('Nama kategori baru:'); if (n && n.trim()) { await addCategory(type, n.trim()); renderManageCatsBody(type); populateCategoryDropdown(); } });
}
function renderManageCatsBody(type) {
  const body = document.getElementById('manageCatsBody'); if (!body) return;
  const cats = ALL_CATS[type] || [];
  body.innerHTML = cats.length ? cats.map(c => '<div class="flex justify-between items-center" style="padding:var(--sp-2) 0;border-bottom:1px solid var(--border)"><span>' + escapeHtml(c) + '</span><button class="btn btn-danger btn-sm" data-del-cat="' + escapeHtml(c) + '">Hapus</button></div>').join('') : '<div class="text-muted">Belum ada kategori.</div>';
  body.querySelectorAll('[data-del-cat]').forEach(b => b.addEventListener('click', async () => { const name = b.getAttribute('data-del-cat'); if (confirm('Hapus kategori "' + name + '"? Transaksi lama tidak ikut terhapus.')) { await deleteCategory(type, name); renderManageCatsBody(type); populateCategoryDropdown(); } }));
}
/* ====== TRANSAKSI BERULANG ====== */
function addInterval(dateStr, unit, n) {
  const d = new Date(dateStr + 'T00:00:00'); n = Math.max(1, n || 1);
  if (unit === 'day') d.setDate(d.getDate() + n);
  else if (unit === 'week') d.setDate(d.getDate() + 7 * n);
  else if (unit === 'month') d.setMonth(d.getMonth() + n);
  else if (unit === 'year') d.setFullYear(d.getFullYear() + n);
  return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
}
async function applyRecurring() {
  let rules; try { rules = await dbGetAll('recurring'); } catch (_) { return 0; }
  if (!rules || !rules.length) return 0;
  const now = new Date(); const today = now.getFullYear() + '-' + String(now.getMonth() + 1).padStart(2, '0') + '-' + String(now.getDate()).padStart(2, '0');
  let created = 0;
  for (const r of rules) {
    if (r.active === false || !r.nextDate) continue;
    let guard = 0;
    while (r.nextDate <= today && guard < 600) {
      const d = new Date(r.nextDate + 'T00:00:00'); const mk = monthKey(d.getFullYear(), d.getMonth());
      await dbAdd('transactions', { type: r.type, category: r.category, amount: r.amount, date: r.nextDate, description: (r.description ? r.description + ' ' : '') + '(berulang)', monthKey: mk, createdAt: new Date().toISOString(), recurringId: r.id });
      if (r.type === 'savings') { try { const goals = await getSavingsGoals(); const goal = goals.find(g => g.name === r.category); if (goal) { goal.totalSaved = (goal.totalSaved || 0) + r.amount; await dbPut('savingsGoals', goal); } } catch (_) {} }
      r.nextDate = addInterval(r.nextDate, r.unit, r.intervalN); created++; guard++;
    }
    await dbPut('recurring', r);
  }
  return created;
}
function openManageRecurring() {
  let ov = document.getElementById('manageRecurOverlay'); if (ov) ov.remove();
  ov = document.createElement('div'); ov.id = 'manageRecurOverlay'; ov.className = 'modal-overlay active';
  ov.innerHTML = '<div class="modal"><div class="modal-header"><div class="modal-title">Transaksi Berulang</div><button class="icon-btn" id="closeManageRecur" aria-label="Tutup">\u2715</button></div><div class="modal-body" id="manageRecurBody"></div></div>';
  document.body.appendChild(ov);
  renderManageRecurBody();
  ov.addEventListener('click', e => { if (e.target === ov) ov.remove(); });
  document.getElementById('closeManageRecur').addEventListener('click', () => ov.remove());
}
async function renderManageRecurBody() {
  const body = document.getElementById('manageRecurBody'); if (!body) return;
  let rules = []; try { rules = await dbGetAll('recurring'); } catch (_) {}
  if (!rules.length) { body.innerHTML = '<div class="text-muted" style="padding:var(--sp-2) 0">Belum ada transaksi berulang. Aktifkan lewat toggle Ulangi saat menambah transaksi.</div>'; return; }
  const ul = { day: 'hari', week: 'minggu', month: 'bulan', year: 'tahun' };
  body.innerHTML = rules.map(r => '<div style="padding:var(--sp-3) 0;border-bottom:1px solid var(--border)"><div class="flex justify-between items-center"><div><div class="fw-bold">' + escapeHtml(r.category || '-') + ' \u00b7 ' + formatRupiah(r.amount || 0) + '</div><div class="text-muted" style="font-size:var(--fs-xs);margin-top:2px">' + escapeHtml(r.type || '') + ' \u00b7 setiap ' + (r.intervalN || 1) + ' ' + (ul[r.unit] || r.unit || '') + ' \u00b7 berikutnya ' + (r.nextDate || '-') + (r.active === false ? ' \u00b7 DIJEDA' : '') + '</div></div><div class="flex gap-2"><button class="btn btn-sm btn-secondary" data-toggle-recur="' + r.id + '">' + (r.active === false ? 'Aktifkan' : 'Jeda') + '</button><button class="btn btn-sm btn-danger" data-del-recur="' + r.id + '">Hapus</button></div></div></div>').join('');
  body.querySelectorAll('[data-del-recur]').forEach(b => b.addEventListener('click', async () => { if (confirm('Hapus aturan berulang ini? Transaksi yang sudah tercatat tetap ada.')) { await dbDelete('recurring', Number(b.getAttribute('data-del-recur'))); renderManageRecurBody(); } }));
  body.querySelectorAll('[data-toggle-recur]').forEach(b => b.addEventListener('click', async () => { const r = await dbGet('recurring', Number(b.getAttribute('data-toggle-recur'))); if (r) { r.active = (r.active === false); await dbPut('recurring', r); renderManageRecurBody(); } }));
}
"""
INIT_OLD = "async function init() { await openDB(); await loadTheme(); await seedData(); initEvents(); await renderMonthLabel(); await switchTab('dashboard'); }"
INIT_NEW = NEW_FUNCS + "async function init() { await openDB(); await loadCategories(); await loadTheme(); await seedData(); await applyRecurring(); initEvents(); await renderMonthLabel(); await switchTab('dashboard'); }"
edits.append(('fungsi baru + init', INIT_OLD, INIT_NEW))

# terapkan
for name, old, new in edits:
    cnt = c.count(old)
    if cnt != 1:
        print('  ! GAGAL pada langkah: ' + name + ' (ditemukan ' + str(cnt) + ' kecocokan, harus tepat 1). Tidak ada file yang diubah.')
        sys.exit(1)
    c = c.replace(old, new, 1)

with io.open(target, 'w', encoding='utf-8') as f:
    f.write(c)

print('  > Sukses! ' + str(len(edits)) + ' bagian ditambal di ' + target + '.')
print('  > Fitur baru: transaksi berulang (toggle Ulangi) + kelola kategori (tambah/hapus).')
