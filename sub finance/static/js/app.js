// Growmore IPO GMP - Frontend Controller (Open IPOs Only)

let allIpos = [];
let currentCategory = 'all';
let currentSearch = '';
let currentSort = 'gmp_pct_desc';
let currentView = 'table';
let activeCalcIpo = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  initIcons();
  fetchInitialData();
});

function initIcons() {
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

// Fetch live IPOs and stats
async function fetchInitialData() {
  showLoading(true);
  try {
    const [iposRes, statsRes] = await Promise.all([
      fetch('/api/ipos'),
      fetch('/api/stats')
    ]);

    const iposData = await iposRes.json();
    const statsData = await statsRes.json();

    // Ensure only Open IPOs are kept
    allIpos = (iposData.ipos || []).filter(i => i.status === 'Open');
    
    renderStats(statsData.stats || {});
    updateCategoryCounts(allIpos);
    applyFiltersAndRender();
  } catch (err) {
    console.error('Error loading IPO data:', err);
    showToast('Failed to load IPO data.', 'error');
  } finally {
    showLoading(false);
  }
}

// Render Stats Header Cards
function renderStats(stats) {
  const elOpen = document.getElementById('statOpenCount');
  const elHeaderOpen = document.getElementById('headerOpenCount');
  const elAvg = document.getElementById('statAvgGain');
  const elTopName = document.getElementById('statTopName');
  const elTopGain = document.getElementById('statTopGain');
  const elMain = document.getElementById('statMainboardCount');
  const elSme = document.getElementById('statSmeCount');

  const openCount = stats.open_count ?? allIpos.length;
  if (elOpen) elOpen.textContent = openCount;
  if (elHeaderOpen) elHeaderOpen.textContent = `${openCount} Open IPOs`;
  if (elAvg) elAvg.textContent = `+${stats.avg_gain_percentage ?? 0}%`;
  
  if (stats.top_gainer && stats.top_gainer.name) {
    if (elTopName) elTopName.textContent = stats.top_gainer.name;
    if (elTopGain) elTopGain.textContent = `+${stats.top_gainer.gmp_percentage}% (₹${stats.top_gainer.gmp} GMP)`;
  } else {
    if (elTopName) elTopName.textContent = 'None';
    if (elTopGain) elTopGain.textContent = 'No positive GMP';
  }

  if (elMain) elMain.textContent = stats.mainboard_count ?? 0;
  if (elSme) elSme.textContent = stats.sme_count ?? 0;
}

function updateCategoryCounts(items) {
  const countAll = items.length;
  const countMain = items.filter(i => i.category === 'Mainboard').length;
  const countSme = items.filter(i => i.category === 'SME').length;

  const elAll = document.getElementById('countAll');
  const elMain = document.getElementById('countMainboard');
  const elSme = document.getElementById('countSme');

  if (elAll) elAll.textContent = countAll;
  if (elMain) elMain.textContent = countMain;
  if (elSme) elSme.textContent = countSme;
}

// Filter and Sort Processing
function applyFiltersAndRender() {
  let filtered = [...allIpos];

  // Category filter
  if (currentCategory !== 'all') {
    filtered = filtered.filter(i => i.category.toLowerCase() === currentCategory);
  }

  // Search filter
  if (currentSearch.trim()) {
    const q = currentSearch.toLowerCase().trim();
    filtered = filtered.filter(i => i.name.toLowerCase().includes(q));
  }

  // Sorting
  if (currentSort === 'gmp_pct_desc') {
    filtered.sort((a, b) => b.gmp_percentage - a.gmp_percentage);
  } else if (currentSort === 'gmp_pct_asc') {
    filtered.sort((a, b) => a.gmp_percentage - b.gmp_percentage);
  } else if (currentSort === 'price_desc') {
    filtered.sort((a, b) => b.price - a.price);
  } else if (currentSort === 'price_asc') {
    filtered.sort((a, b) => a.price - b.price);
  } else if (currentSort === 'name') {
    filtered.sort((a, b) => a.name.localeCompare(b.name));
  }

  renderView(filtered);
}

// Render Table or Grid View
function renderView(items) {
  const tableContainer = document.getElementById('ipoTableView');
  const gridContainer = document.getElementById('ipoGridView');
  const emptyState = document.getElementById('emptyState');

  if (items.length === 0) {
    tableContainer.classList.add('hidden');
    gridContainer.classList.add('hidden');
    emptyState.classList.remove('hidden');
    initIcons();
    return;
  }

  emptyState.classList.add('hidden');

  if (currentView === 'table') {
    gridContainer.classList.add('hidden');
    tableContainer.classList.remove('hidden');
    const tbody = document.getElementById('ipoTableBody');
    tbody.innerHTML = items.map(ipo => createTableRow(ipo)).join('');
  } else {
    tableContainer.classList.add('hidden');
    gridContainer.classList.remove('hidden');
    gridContainer.innerHTML = items.map(ipo => createIpoCard(ipo)).join('');
  }

  initIcons();
}

// Table Row HTML for Open IPO
function createTableRow(ipo) {
  const isPositive = ipo.gmp > 0;
  const isZero = ipo.gmp === 0;

  const gmpBadge = isPositive 
    ? `<span class="inline-block bg-emerald-50 text-emerald-700 border border-emerald-300 font-extrabold px-2.5 py-1 rounded-md text-xs">+₹${ipo.gmp}</span>`
    : (isZero 
        ? `<span class="inline-block bg-slate-100 text-slate-500 border border-slate-200 font-semibold px-2 py-0.5 rounded text-xs">₹0</span>` 
        : `<span class="inline-block bg-rose-50 text-rose-700 border border-rose-300 font-bold px-2 py-0.5 rounded text-xs">-₹${Math.abs(ipo.gmp)}</span>`);

  const gainColor = isPositive ? 'text-emerald-600 font-bold' : (isZero ? 'text-slate-400' : 'text-rose-600 font-bold');

  const typeColor = ipo.category === 'SME' 
    ? 'bg-purple-100 text-purple-800 border-purple-200' 
    : 'bg-blue-100 text-blue-800 border-blue-200';

  const hotIcon = (ipo.gmp_percentage >= 30) ? `<span title="High Demand" class="text-xs ml-1">🔥</span>` : '';

  return `
    <tr class="transition border-b border-slate-200 hover:bg-emerald-50/40">
      
      <!-- Company Name -->
      <td class="px-4 py-3.5">
        <div class="font-bold text-slate-900 flex items-center text-xs sm:text-sm">
          ${ipo.name} ${hotIcon}
        </div>
        <div class="text-[11px] text-slate-500 mt-0.5 flex items-center gap-1.5">
          <span>Size: ${ipo.ipo_size}</span>
          <span>•</span>
          <span>Lot: ${ipo.lot_size.toLocaleString()} sh.</span>
        </div>
      </td>

      <!-- Type & Exchange -->
      <td class="px-3 py-3.5 text-center whitespace-nowrap">
        <span class="inline-block text-[10px] font-bold px-2 py-0.5 rounded border ${typeColor}">
          ${ipo.category}
        </span>
        <div class="text-[10px] text-slate-400 font-mono mt-0.5">${ipo.exchange}</div>
      </td>

      <!-- Price Band -->
      <td class="px-3 py-3.5 text-right font-bold text-slate-800 whitespace-nowrap">
        ${ipo.price_text}
      </td>

      <!-- GMP (₹) -->
      <td class="px-3 py-3.5 text-right whitespace-nowrap bg-emerald-50/50">
        ${gmpBadge}
      </td>

      <!-- Est. Listing Price -->
      <td class="px-3 py-3.5 text-right font-bold text-slate-900 whitespace-nowrap">
        ₹${ipo.est_listing_price}
      </td>

      <!-- Est. Gain % -->
      <td class="px-3 py-3.5 text-right whitespace-nowrap ${gainColor}">
        ${isPositive ? '+' : ''}${ipo.gmp_percentage}%
      </td>

      <!-- Open Date -->
      <td class="px-3 py-3.5 text-center text-slate-700 font-medium whitespace-nowrap">
        ${ipo.open_date}
      </td>

      <!-- Close Date -->
      <td class="px-3 py-3.5 text-center text-slate-700 font-medium whitespace-nowrap">
        ${ipo.close_date}
      </td>

      <!-- Prominent ALLOTMENT DATE Column -->
      <td class="px-3 py-3.5 text-center whitespace-nowrap bg-blue-50/60">
        <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-blue-100 text-blue-900 border border-blue-300 font-bold text-[11px] shadow-2xs">
          📅 ${ipo.allotment_date}
        </span>
      </td>

      <!-- Listing Date -->
      <td class="px-3 py-3.5 text-center text-slate-700 font-medium whitespace-nowrap">
        ${ipo.listing_date}
      </td>

      <!-- Status -->
      <td class="px-3 py-3.5 text-center whitespace-nowrap">
        <span class="text-[10px] font-bold px-2.5 py-1 rounded-full border bg-emerald-100 text-emerald-800 border-emerald-300 inline-flex items-center gap-1">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse"></span>
          Open
        </span>
      </td>

      <!-- Action -->
      <td class="px-4 py-3.5 text-center whitespace-nowrap">
        <button onclick="openCalculator('${ipo.id}')" class="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-[11px] font-bold transition shadow-xs cursor-pointer">
          Calculate
        </button>
      </td>
    </tr>
  `;
}

// Card View HTML
function createIpoCard(ipo) {
  const isPositive = ipo.gmp > 0;
  const isZero = ipo.gmp === 0;

  const gmpBg = isPositive 
    ? 'bg-emerald-50 text-emerald-800 border-emerald-200' 
    : (isZero ? 'bg-slate-100 text-slate-600 border-slate-200' : 'bg-rose-50 text-rose-800 border-rose-200');

  const typeColor = ipo.category === 'SME' 
    ? 'bg-purple-100 text-purple-800 border-purple-200' 
    : 'bg-blue-100 text-blue-800 border-blue-200';

  const hotBadge = (ipo.gmp_percentage >= 30) ? `<span class="text-xs ml-1" title="High Demand">🔥</span>` : '';

  return `
    <div class="ipo-card bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex flex-col justify-between relative group">
      
      <div>
        <div class="flex items-center justify-between gap-2 mb-2">
          <div class="flex items-center gap-1.5">
            <span class="text-[10px] font-bold px-2 py-0.5 rounded border ${typeColor}">
              ${ipo.category}
            </span>
            <span class="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
              ${ipo.exchange}
            </span>
          </div>

          <span class="text-[10px] font-bold px-2.5 py-0.5 rounded-full border bg-emerald-100 text-emerald-800 border-emerald-300 flex items-center gap-1">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse"></span>
            Open
          </span>
        </div>

        <h3 class="text-base font-extrabold text-slate-900 group-hover:text-emerald-600 transition-colors flex items-center">
          ${ipo.name} ${hotBadge}
        </h3>
        <p class="text-xs text-slate-500 mt-0.5">Issue Size: <strong class="text-slate-700">${ipo.ipo_size}</strong></p>

        <!-- Main GMP & Price Box -->
        <div class="my-3.5 p-3 rounded-lg bg-slate-50 border border-slate-200 grid grid-cols-3 gap-2 text-center">
          <div>
            <div class="text-[10px] uppercase font-bold text-slate-500">Price</div>
            <div class="text-sm font-extrabold text-slate-900 mt-0.5">${ipo.price_text}</div>
          </div>
          <div class="bg-emerald-50/80 rounded py-0.5 border border-emerald-200/60">
            <div class="text-[10px] uppercase font-bold text-emerald-800">GMP (₹)</div>
            <div class="text-sm font-extrabold ${isPositive ? 'text-emerald-700' : (isZero ? 'text-slate-500' : 'text-rose-600')} mt-0.5">
              ${isPositive ? '+' : ''}₹${ipo.gmp}
            </div>
          </div>
          <div>
            <div class="text-[10px] uppercase font-bold text-slate-500">Est. Listing</div>
            <div class="text-sm font-extrabold text-slate-900 mt-0.5">₹${ipo.est_listing_price}</div>
          </div>
        </div>

        <div class="flex items-center justify-between px-3 py-1.5 rounded-lg border ${gmpBg} text-xs font-bold mb-3">
          <span>Est. Listing Gain:</span>
          <span class="text-sm font-extrabold">${isPositive ? '+' : ''}${ipo.gmp_percentage}%</span>
        </div>

        <div class="space-y-1.5 text-xs text-slate-600 border-t border-slate-100 pt-3">
          <div class="flex justify-between">
            <span>Lot Size:</span>
            <strong class="text-slate-800">${ipo.lot_size.toLocaleString()} shares</strong>
          </div>
          <div class="flex justify-between">
            <span>Min. Investment:</span>
            <strong class="text-slate-800">₹${ipo.min_investment.toLocaleString()}</strong>
          </div>
          <div class="flex justify-between">
            <span>Est. Profit / Lot:</span>
            <strong class="${isPositive ? 'text-emerald-700 font-extrabold' : 'text-slate-600'}">
              ${isPositive ? '+' : ''}₹${ipo.est_profit_per_lot.toLocaleString()}
            </strong>
          </div>
        </div>

        <!-- Allotment Date Highlight Box -->
        <div class="mt-3 pt-2.5 border-t border-slate-100 text-xs">
          <div class="bg-blue-50 border border-blue-200 rounded-md p-2 flex items-center justify-between mb-2">
            <span class="text-blue-900 font-bold text-[11px] flex items-center gap-1">
              📅 Allotment Date:
            </span>
            <span class="text-blue-900 font-extrabold text-xs">
              ${ipo.allotment_date}
            </span>
          </div>

          <div class="grid grid-cols-3 gap-1 text-[10px] text-slate-500 text-center">
            <div class="bg-slate-50 p-1.5 rounded border border-slate-100">
              <div class="text-slate-400">Open</div>
              <div class="font-bold text-slate-700 mt-0.5">${ipo.open_date}</div>
            </div>
            <div class="bg-slate-50 p-1.5 rounded border border-slate-100">
              <div class="text-slate-400">Close</div>
              <div class="font-bold text-slate-700 mt-0.5">${ipo.close_date}</div>
            </div>
            <div class="bg-slate-50 p-1.5 rounded border border-slate-100">
              <div class="text-slate-400">Listing</div>
              <div class="font-bold text-slate-700 mt-0.5">${ipo.listing_date}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="mt-4 pt-2">
        <button onclick="openCalculator('${ipo.id}')" class="w-full flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition shadow-xs cursor-pointer">
          <i data-lucide="calculator" class="w-3.5 h-3.5"></i>
          <span>Calculate Profit</span>
        </button>
      </div>

    </div>
  `;
}

// Category Tabs
function setCategoryFilter(cat) {
  currentCategory = cat;
  ['all', 'mainboard', 'sme'].forEach(c => {
    const el = document.getElementById(`catTab-${c}`);
    if (el) {
      if (c === cat) {
        el.className = 'filter-tab-active px-3.5 py-1.5 rounded-md transition whitespace-nowrap';
      } else {
        el.className = 'filter-tab-inactive px-3.5 py-1.5 rounded-md transition whitespace-nowrap';
      }
    }
  });
  applyFiltersAndRender();
}

function handleSearch(val) {
  currentSearch = val;
  const clearBtn = document.getElementById('clearSearchBtn');
  if (val.trim()) {
    clearBtn.classList.remove('hidden');
  } else {
    clearBtn.classList.add('hidden');
  }
  applyFiltersAndRender();
}

function clearSearch() {
  const input = document.getElementById('searchInput');
  if (input) input.value = '';
  document.getElementById('clearSearchBtn').classList.add('hidden');
  currentSearch = '';
  applyFiltersAndRender();
}

function handleSort(val) {
  currentSort = val;
  applyFiltersAndRender();
}

function setViewMode(mode) {
  currentView = mode;
  const btnTable = document.getElementById('viewBtnTable');
  const btnGrid = document.getElementById('viewBtnGrid');

  if (mode === 'table') {
    btnTable.className = 'p-1.5 rounded bg-white text-emerald-700 shadow-xs font-semibold';
    btnGrid.className = 'p-1.5 rounded text-slate-500 hover:text-slate-900';
  } else {
    btnGrid.className = 'p-1.5 rounded bg-white text-emerald-700 shadow-xs font-semibold';
    btnTable.className = 'p-1.5 rounded text-slate-500 hover:text-slate-900';
  }
  applyFiltersAndRender();
}

function resetFilters() {
  currentCategory = 'all';
  clearSearch();
  setCategoryFilter('all');
}

// Calculator Logic
function openCalculator(ipoId) {
  const ipo = allIpos.find(i => i.id === ipoId);
  if (!ipo) return;
  activeCalcIpo = ipo;

  document.getElementById('calcIpoName').textContent = ipo.name;
  document.getElementById('calcIpoMeta').textContent = `${ipo.category} • Price: ${ipo.price_text} • Current GMP: ₹${ipo.gmp}`;
  document.getElementById('calcLotsInput').value = 1;

  recalcProfit();
  document.getElementById('calcModal').classList.remove('hidden');
  initIcons();
}

function closeCalculator() {
  document.getElementById('calcModal').classList.add('hidden');
  activeCalcIpo = null;
}

function changeCalcLots(delta) {
  const input = document.getElementById('calcLotsInput');
  let val = parseInt(input.value) || 1;
  val = Math.max(1, Math.min(100, val + delta));
  input.value = val;
  recalcProfit();
}

function setCalcLots(num) {
  document.getElementById('calcLotsInput').value = num;
  recalcProfit();
}

function recalcProfit() {
  if (!activeCalcIpo) return;
  const lots = parseInt(document.getElementById('calcLotsInput').value) || 1;
  const sharesPerLot = activeCalcIpo.lot_size || 1;
  const totalShares = lots * sharesPerLot;
  const price = activeCalcIpo.price || 0;
  const gmp = activeCalcIpo.gmp || 0;

  const totalInvestment = totalShares * price;
  const totalProfit = totalShares * gmp;
  const estListingPrice = price + gmp;
  const profitPct = price > 0 ? ((gmp / price) * 100).toFixed(2) : 0;

  document.getElementById('calcSharesPerLot').textContent = `${sharesPerLot.toLocaleString()} shares`;
  document.getElementById('calcTotalShares').textContent = `${totalShares.toLocaleString()} shares`;
  document.getElementById('calcIssuePrice').textContent = `₹${price}`;
  document.getElementById('calcTotalInvestment').textContent = `₹${totalInvestment.toLocaleString()}`;
  document.getElementById('calcGmpValue').textContent = `+₹${gmp}`;
  document.getElementById('calcEstPrice').textContent = `₹${estListingPrice}`;
  document.getElementById('calcTotalProfit').textContent = `+₹${totalProfit.toLocaleString()}`;
  document.getElementById('calcProfitPct').textContent = `+${profitPct}% Expected Gain`;
}

function showLoading(show) {
  const loading = document.getElementById('loadingState');
  if (loading) {
    if (show) loading.classList.remove('hidden');
    else loading.classList.add('hidden');
  }
}

function showToast(msg) {
  const toast = document.getElementById('toast');
  const toastMsg = document.getElementById('toastMsg');
  if (toastMsg) toastMsg.textContent = msg;
  if (toast) {
    toast.classList.remove('hidden');
    toast.classList.add('flex');
    setTimeout(() => {
      toast.classList.add('hidden');
      toast.classList.remove('flex');
    }, 4000);
  }
}
