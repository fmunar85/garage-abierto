/* ── Sidebar toggle ── */
document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.getElementById('sidebarToggle');
  const sidebar = document.querySelector('.sidebar');
  if (toggle && sidebar) {
    toggle.addEventListener('click', () => sidebar.classList.toggle('open'));
  }

  // Auto-dismiss alerts after 5s
  document.querySelectorAll('.alert').forEach(el => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      bsAlert.close();
    }, 5000);
  });

  // Delete confirm
  document.querySelectorAll('[data-confirm]').forEach(btn => {
    btn.addEventListener('click', e => {
      if (!confirm(btn.dataset.confirm || '¿Estás seguro?')) e.preventDefault();
    });
  });
});

/* ══════════════════════════════════════════════
   POS — Point of Sale
══════════════════════════════════════════════ */
const POS = (() => {
  let cart = {};   // { productId: { id, name, price, qty, stock } }

  function formatCurrency(n) {
    return '$' + Number(n).toLocaleString('es-AR', { maximumFractionDigits: 0 });
  }

  function addToCart(product) {
    const id = product.id;
    if (cart[id]) {
      if (cart[id].qty < cart[id].stock) {
        cart[id].qty++;
      } else {
        showToast(`Stock máximo: ${cart[id].stock}`, 'warning');
        return;
      }
    } else {
      cart[id] = { ...product, qty: 1 };
    }
    renderCart();
    showToast(`${product.name} agregado`, 'success');
  }

  function removeFromCart(id) {
    delete cart[id];
    renderCart();
  }

  function setQty(id, qty) {
    qty = parseInt(qty);
    if (isNaN(qty) || qty <= 0) { removeFromCart(id); return; }
    if (qty > cart[id].stock) qty = cart[id].stock;
    cart[id].qty = qty;
    renderCart();
  }

  function renderCart() {
    const container = document.getElementById('cartItems');
    const emptyMsg  = document.getElementById('cartEmpty');
    if (!container) return;

    const ids = Object.keys(cart);
    if (ids.length === 0) {
      container.innerHTML = '';
      if (emptyMsg) emptyMsg.style.display = 'block';
      updateTotals(0);
      updateHiddenInput();
      return;
    }
    if (emptyMsg) emptyMsg.style.display = 'none';

    container.innerHTML = ids.map(id => {
      const item = cart[id];
      const sub = item.price * item.qty;
      return `
      <div class="cart-item" data-id="${id}">
        <div>
          <div class="cart-item-name">${item.name}</div>
          <div class="cart-item-price">${formatCurrency(item.price)} c/u</div>
        </div>
        <div class="cart-item-qty">
          <button type="button" onclick="POS.setQty(${id}, ${item.qty - 1})">−</button>
          <input type="number" value="${item.qty}" min="1" max="${item.stock}"
                 onchange="POS.setQty(${id}, this.value)" />
          <button type="button" onclick="POS.setQty(${id}, ${item.qty + 1})">+</button>
        </div>
        <div class="cart-item-sub">${formatCurrency(sub)}</div>
        <i class="bi bi-x-circle cart-item-remove" onclick="POS.remove(${id})"></i>
      </div>`;
    }).join('');

    const subtotal = ids.reduce((s, id) => s + cart[id].price * cart[id].qty, 0);
    updateTotals(subtotal);
    updateHiddenInput();
  }

  function updateTotals(subtotal) {
    const discountEl = document.getElementById('discountInput');
    const discount = discountEl ? parseFloat(discountEl.value) || 0 : 0;
    const total = subtotal * (1 - discount / 100);

    const el = (id) => document.getElementById(id);
    if (el('subtotalDisplay'))  el('subtotalDisplay').textContent  = formatCurrency(subtotal);
    if (el('discountDisplay'))  el('discountDisplay').textContent  = formatCurrency(subtotal * discount / 100);
    if (el('totalDisplay'))     el('totalDisplay').textContent     = formatCurrency(total);
  }

  function updateHiddenInput() {
    const input = document.getElementById('itemsJson');
    if (!input) return;
    const data = Object.values(cart).map(i => ({ id: i.id, qty: i.qty, price: i.price }));
    input.value = JSON.stringify(data);
  }

  function submitSale() {
    if (Object.keys(cart).length === 0) {
      showToast('Agregá al menos un artículo al carrito.', 'danger');
      return;
    }
    updateHiddenInput();
    document.getElementById('saleForm').submit();
  }

  return { add: addToCart, remove: removeFromCart, setQty, submit: submitSale };
})();

/* ── Product search in POS ── */
let searchTimer;
function posSearch(query) {
  clearTimeout(searchTimer);
  if (query.length < 2) {
    document.getElementById('posProductGrid').innerHTML = '';
    return;
  }
  searchTimer = setTimeout(async () => {
    const res = await fetch(`/ventas/buscar-productos?q=${encodeURIComponent(query)}`);
    const products = await res.json();
    renderPosGrid(products);
  }, 250);
}

function renderPosGrid(products) {
  const grid = document.getElementById('posProductGrid');
  if (!grid) return;
  if (!products.length) {
    grid.innerHTML = `<div class="col-12 text-center py-4 text-muted"><i class="bi bi-search fs-2 d-block mb-2"></i>Sin resultados</div>`;
    return;
  }
  grid.innerHTML = products.map(p => `
    <div class="col-6 col-lg-4 col-xl-3">
      <div class="product-card" onclick='POS.add(${JSON.stringify(p)})'>
        ${p.image
          ? `<img src="${p.image}" class="product-card-img" alt="">`
          : `<div class="product-card-img-placeholder"><i class="bi bi-droplet-half"></i></div>`}
        <div class="product-card-body">
          <div class="product-card-sku">${p.sku}</div>
          <div class="product-card-name">${p.name}</div>
          <div class="product-card-brand">${p.brand}</div>
          <div class="product-card-price">$${Number(p.price).toLocaleString('es-AR', {maximumFractionDigits:0})}</div>
          <div class="product-card-stock">
            <span class="badge ${p.stock > 5 ? 'badge-stock-ok' : p.stock > 0 ? 'badge-stock-low' : 'badge-stock-out'}">
              Stock: ${p.stock}
            </span>
          </div>
        </div>
      </div>
    </div>
  `).join('');
}

/* ── Toast notification ── */
function showToast(message, type = 'info') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.style.cssText = 'position:fixed;bottom:20px;right:20px;z-index:9999;display:flex;flex-direction:column;gap:8px;';
    document.body.appendChild(container);
  }
  const colors = { success: '#3fb950', danger: '#f85149', warning: '#e3b341', info: '#58a6ff' };
  const toast = document.createElement('div');
  toast.style.cssText = `background:#161b22;color:#f0f6fc;border:1px solid ${colors[type] || colors.info};
    border-radius:10px;padding:12px 18px;font-size:14px;font-family:'Poppins',sans-serif;
    box-shadow:0 4px 16px rgba(0,0,0,0.3);display:flex;align-items:center;gap:8px;min-width:240px;`;
  toast.innerHTML = `<span style="color:${colors[type]};font-size:16px;">${
    type === 'success' ? '✓' : type === 'danger' ? '✕' : type === 'warning' ? '⚠' : 'ℹ'}</span>${message}`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}
