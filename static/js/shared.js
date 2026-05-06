/**
 * uzshop — Shared JavaScript Utilities
 * Used across all pages
 */

var ROUTES = window.NEXUS_ROUTES || {
  index: '/',
  shop: '/shop/',
  product: '/product/',
  checkout: '/checkout/',
  wishlist: '/wishlist/',
  profile: '/profile/',
  confirmation: '/confirmation/',
};

var PAGE_TRANSITION_KEY = 'uzshop_page_transition';
var PAGE_TRANSITION_MIN_MS = 1000;

function normalizePathname(value) {
  if (!value) return '/';
  return value.replace(/\/+$/, '') || '/';
}

function getPathnameFromUrl(url) {
  try {
    return normalizePathname(new URL(url, window.location.origin).pathname);
  } catch (e) {
    return normalizePathname(String(url || ''));
  }
}

function isPageEndpointChange(url) {
  var currentPath = normalizePathname(window.location.pathname);
  var nextPath = getPathnameFromUrl(url);
  return currentPath !== nextPath;
}

function ensurePageLoader() {
  var existing = document.getElementById('page-transition-loader');
  if (existing) return existing;
  var loader = document.createElement('div');
  loader.id = 'page-transition-loader';
  loader.className = 'page-loader';
  loader.setAttribute('aria-hidden', 'true');
  loader.innerHTML =
    '<div class="page-loader__backdrop"></div>' +
    '<div class="page-loader__panel">' +
      '<div class="page-loader__spinner"></div>' +
      '<div class="page-loader__copy">' +
        '<p class="page-loader__eyebrow">uzshop</p>' +
        '<h2>Sahifa tayyorlanmoqda</h2>' +
        '<p>Premium storefront yuklanmoqda...</p>' +
      '</div>' +
    '</div>';
  document.body.appendChild(loader);
  return loader;
}

function showPageLoader() {
  var loader = ensurePageLoader();
  loader.classList.add('is-visible');
  document.body.classList.add('page-loading');
}

function hidePageLoader() {
  var loader = document.getElementById('page-transition-loader');
  if (loader) loader.classList.remove('is-visible');
  document.body.classList.remove('page-loading');
}

function persistPageTransition(url) {
  try {
    sessionStorage.setItem(PAGE_TRANSITION_KEY, JSON.stringify({
      targetPath: getPathnameFromUrl(url),
      startedAt: Date.now(),
    }));
  } catch (e) {}
}

function clearPageTransition() {
  try { sessionStorage.removeItem(PAGE_TRANSITION_KEY); } catch (e) {}
}

function navigateWithLoader(url) {
  if (!url) return;
  if (!isPageEndpointChange(url)) {
    window.location.href = url;
    return;
  }
  persistPageTransition(url);
  showPageLoader();
  setTimeout(function() {
    window.location.href = url;
  }, 80);
}

function restorePendingPageTransition() {
  var raw = null;
  try { raw = sessionStorage.getItem(PAGE_TRANSITION_KEY); } catch (e) {}
  if (!raw) return;

  var payload = null;
  try { payload = JSON.parse(raw); } catch (e) {
    clearPageTransition();
    return;
  }

  if (!payload || payload.targetPath !== normalizePathname(window.location.pathname)) {
    clearPageTransition();
    return;
  }

  showPageLoader();
  var elapsed = Date.now() - Number(payload.startedAt || 0);
  var wait = Math.max(0, PAGE_TRANSITION_MIN_MS - elapsed);
  window.setTimeout(function() {
    hidePageLoader();
    clearPageTransition();
  }, wait);
}

function installPageTransitionLinks() {
  document.addEventListener('click', function(event) {
    if (event.defaultPrevented) return;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;

    var anchor = event.target.closest && event.target.closest('a[href]');
    if (!anchor) return;
    if (anchor.target && anchor.target !== '_self') return;
    if (anchor.hasAttribute('download')) return;

    var href = anchor.getAttribute('href');
    if (!href || href.charAt(0) === '#') return;

    var resolved = null;
    try {
      resolved = new URL(anchor.href, window.location.origin);
    } catch (e) {
      return;
    }

    if (resolved.origin !== window.location.origin) return;
    if (!isPageEndpointChange(resolved.href)) return;

    event.preventDefault();
    navigateWithLoader(resolved.href);
  }, true);
}

function initPageTransitions() {
  if (!document.body) return;
  ensurePageLoader();
  installPageTransitionLinks();
  restorePendingPageTransition();
  window.addEventListener('pageshow', function() {
    if (!sessionStorage.getItem(PAGE_TRANSITION_KEY)) hidePageLoader();
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initPageTransitions, { once: true });
} else {
  initPageTransitions();
}

function buildShopUrl(category, query) {
  var params = new URLSearchParams();
  if (category && category !== 'Hammasi') params.set('cat', category);
  if (query) params.set('q', query);
  var suffix = params.toString();
  return ROUTES.shop + (suffix ? '?' + suffix : '');
}

// ── Store (localStorage-backed) ───────────────────────────────────────────

const Store = {
  get: function(key, fallback) {
    if (fallback === undefined) fallback = null;
    try { var v = localStorage.getItem('nexus_' + key); return v ? JSON.parse(v) : fallback; }
    catch(e) { return fallback; }
  },
  set: function(key, val) {
    try { localStorage.setItem('nexus_' + key, JSON.stringify(val)); } catch(e) {}
  },
};

// ── Cart ─────────────────────────────────────────────────────────────────

var Cart = {
  getItems: function()      { return Store.get('cart', []); },
  setItems: function(items) { Store.set('cart', items); Cart._dispatch(); },
  getCount: function()      { return Cart.getItems().reduce(function(s,it){ return s + (it.qty||1); }, 0); },
  getTotal: function()      { return Cart.getItems().reduce(function(s,it){ return s + it.price * (it.qty||1); }, 0); },

  add: function(product, qty) {
    if (!qty) qty = 1;
    var items = Cart.getItems();
    var idx = items.findIndex(function(it){ return it.id === product.id; });
    if (idx >= 0) {
      items[idx].qty = (items[idx].qty || 1) + qty;
    } else {
      var item = Object.assign({}, product, { qty: qty });
      items.push(item);
    }
    Cart.setItems(items);
  },

  remove: function(idx) {
    var items = Cart.getItems();
    items.splice(idx, 1);
    Cart.setItems(items);
  },

  updateQty: function(idx, qty) {
    if (qty < 1) { Cart.remove(idx); return; }
    var items = Cart.getItems();
    if (items[idx]) { items[idx].qty = qty; Cart.setItems(items); }
  },

  clear: function() { Cart.setItems([]); },

  _dispatch: function() {
    window.dispatchEvent(new CustomEvent('cart-updated', { detail: Cart.getItems() }));
  },
};

// ── Wishlist ──────────────────────────────────────────────────────────────

var Wishlist = {
  getIds: function() { return Store.get('wishlist', []); },
  has: function(id)  { return Wishlist.getIds().indexOf(id) !== -1; },
  toggle: function(id) {
    var ids = Wishlist.getIds();
    var has = ids.indexOf(id) !== -1;
    var next = has ? ids.filter(function(x){ return x !== id; }) : ids.concat([id]);
    Store.set('wishlist', next);
    window.dispatchEvent(new CustomEvent('wishlist-updated', { detail: next }));
    return !has;
  },
};

// ── Toast ─────────────────────────────────────────────────────────────────

function showToast(msg, type, duration) {
  type = type || 'default';
  duration = duration || 2800;
  var container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }
  var toast = document.createElement('div');
  toast.className = 'toast' + (type !== 'default' ? ' ' + type : '');
  var icon = '';
  if (type === 'success') icon = '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 8l3.5 3.5 6.5-7" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  if (type === 'error')   icon = '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M4 4l8 8M12 4L4 12" stroke="#fff" stroke-width="2" stroke-linecap="round"/></svg>';
  toast.innerHTML = icon + ' ' + msg;
  container.appendChild(toast);
  setTimeout(function() {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s';
    setTimeout(function(){ if (toast.parentNode) toast.remove(); }, 300);
  }, duration);
}

// ── Stars renderer ────────────────────────────────────────────────────────

function renderStars(rating, size) {
  size = size || 12;
  var html = '';
  for (var i = 0; i < 5; i++) {
    html += '<svg class="star ' + (i < Math.round(rating) ? 'filled' : 'empty') + '" width="' + size + '" height="' + size + '" viewBox="0 0 12 12"><path d="M6 1l1.3 2.7 3 .4-2.2 2.1.5 3L6 7.8 3.4 9.2l.5-3L1.7 4.1l3-.4z"/></svg>';
  }
  return html;
}

// ── Placeholder image SVG ─────────────────────────────────────────────────

var IMG_CONFIGS = {
  'electronics-airpods': { bg:'#f0f0ec', stripe:'#e0e0da', label:'AirPods Pro' },
  'sport-shoes':         { bg:'#eef2ff', stripe:'#dde4ff', label:'Sneaker' },
  'clothing-tee':        { bg:'#faf5f0', stripe:'#f0e8e0', label:'T-Shirt' },
  'electronics-phone':   { bg:'#1a1a24', stripe:'#22222e', label:'Smartphone', dark:true },
  'home-sofa':           { bg:'#f5f0e8', stripe:'#ece5d8', label:'Sofa Set' },
  'beauty-cream':        { bg:'#fdf8f4', stripe:'#f5ede4', label:'Night Cream' },
  'electronics-laptop':  { bg:'#f2f2ef', stripe:'#e5e5e0', label:'Laptop' },
  'sport-mat':           { bg:'#f0faf5', stripe:'#e0f5ea', label:'Yoga Mat' },
};

function escapeHtml(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function isRemoteImage(imgKey) {
  return typeof imgKey === 'string' && /^https?:\/\//i.test(imgKey);
}

function productImageSVG(imgKey, size, altText) {
  size = size || 300;
  if (isRemoteImage(imgKey)) {
    return '<img src="' + escapeHtml(imgKey) + '" alt="' + escapeHtml(altText || 'Product image') + '" loading="lazy" style="width:100%;height:100%;object-fit:cover;display:block"/>';
  }
  var c = IMG_CONFIGS[imgKey] || { bg:'#f0f0f0', stripe:'#e0e0e0', label: imgKey || '?' };
  var textFill = c.dark ? '#666' : '#aaa';
  var stripes = '';
  for (var i = 0; i < 10; i++) {
    stripes += '<rect x="' + (-300 + i*60) + '" y="-10" width="30" height="' + (size+20) + '" fill="' + c.stripe + '" transform="rotate(-15 ' + (size/2) + ' ' + (size/2) + ')"/>';
  }
  return '<svg viewBox="0 0 ' + size + ' ' + size + '" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg"><rect width="' + size + '" height="' + size + '" fill="' + c.bg + '"/>' + stripes + '<text x="' + (size/2) + '" y="' + (size/2+5) + '" text-anchor="middle" font-family="DM Mono,monospace" font-size="13" fill="' + textFill + '" letter-spacing="0.5">' + c.label + '</text></svg>';
}

function renderProductImageMarkup(imgKey, size, altText) {
  return productImageSVG(imgKey, size, altText);
}

// ── Format helpers ────────────────────────────────────────────────────────

function fmtPrice(val) {
  var amount = Math.round(Number(val) || 0);
  return amount.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.') + " so'm";
}

function fmtDate(isoStr) {
  var d = new Date(isoStr);
  return d.toLocaleDateString('ru-RU', { day:'numeric', month:'long', year:'numeric' });
}

// ── Navbar builder ────────────────────────────────────────────────────────

function buildNavbar(activePage) {
  activePage = activePage || (document.body && document.body.dataset ? document.body.dataset.page : '') || '';
  var count = Cart.getCount();

  var navLinks = [
    { key: 'index',    label: 'Bosh',      href: ROUTES.index },
    { key: 'shop',     label: "Do'kon",    href: ROUTES.shop },
    { key: 'featured', label: 'Tavsiyalar', href: ROUTES.index + '#featured' },
    { key: 'wishlist', label: 'Istaklar',  href: ROUTES.wishlist },
  ];

  var catsHTML = navLinks.map(function(link) {
    return '<a href="' + link.href + '" class="' + (activePage === link.key ? 'active' : '') + '">' + link.label + '</a>';
  }).join('');

  // Mobile drawer still shows categories (handy on small screens)
  var mobileNavHTML = navLinks.map(function(link) {
    return '<a href="' + link.href + '" class="mobile-menu-cat' + (activePage === link.key ? ' active' : '') + '">'
      + '<span style="font-size:18px;width:28px;text-align:center">›</span>' + link.label + '</a>';
  }).join('');

  var emojiByCat = {};
  (CATEGORIES || []).forEach(function(c) { emojiByCat[c.name] = c.emoji || '🛍'; });
  var mobileCatsHTML = (CATEGORIES || []).map(function(category) {
    return '<a href="' + buildShopUrl(category.name) + '" class="mobile-menu-cat">'
      + '<span style="font-size:18px;width:28px;text-align:center">' + (emojiByCat[category.name] || '🛍') + '</span>'
      + category.name + '</a>';
  }).join('');

  var cartBadgeStyle = count > 0 ? '' : 'display:none';

  var html = '<header class="navbar">'
    + '<nav class="navbar-inner">'
    + '<button class="navbar-hamburger" id="hamburger-btn" aria-label="Menu">'
    + '<svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M2 4h14M2 9h14M2 14h14" stroke="var(--ink)" stroke-width="1.8" stroke-linecap="round"/></svg>'
    + '</button>'
    + '<a href="' + ROUTES.index + '" class="navbar-logo">uz<span>shop</span></a>'
    + '<div class="navbar-cats">' + catsHTML + '</div>'
    + '<div class="navbar-spacer"></div>'
    + '<div class="navbar-search">'
    + '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="7" cy="7" r="4.5" stroke="var(--ink-3)" stroke-width="1.5"/><path d="M10.5 10.5L14 14" stroke="var(--ink-3)" stroke-width="1.5" stroke-linecap="round"/></svg>'
    + '<input type="text" placeholder="Qidirish..." id="nav-search"/>'
    + '</div>'
    + '<button class="navbar-btn" onclick="navigateWithLoader(\'' + ROUTES.wishlist + '\')" title="Wishlist">'
    + '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M10 16s-7-4.5-7-9a4 4 0 0 1 7-2.65A4 4 0 0 1 17 7c0 4.5-7 9-7 9z" stroke="var(--ink)" stroke-width="1.5" stroke-linejoin="round"/></svg>'
    + '</button>'
    + '<button class="navbar-btn" id="nav-cart-btn" onclick="navigateWithLoader(\'' + ROUTES.checkout + '\')" title="Savat">'
    + '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M3 3h1.5l2.5 9h7l2-6H6.5" stroke="var(--ink)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><circle cx="9" cy="16" r="1.2" fill="var(--ink)"/><circle cx="14" cy="16" r="1.2" fill="var(--ink)"/></svg>'
    + '<span class="cart-badge" id="nav-cart-badge" style="' + cartBadgeStyle + '">' + count + '</span>'
    + '</button>'
    + '<button class="navbar-btn dark" onclick="navigateWithLoader(\'' + ROUTES.profile + '\')" title="Profil">'
    + '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><circle cx="10" cy="7" r="3" stroke="#fff" stroke-width="1.5"/><path d="M3 17c0-3.3 3.1-6 7-6s7 2.7 7 6" stroke="#fff" stroke-width="1.5" stroke-linecap="round"/></svg>'
    + '</button>'
    + '</nav>'
    + '</header>'

    // Mobile Menu Drawer
    + '<div class="mobile-menu" id="mobile-menu">'
    + '<div class="mobile-menu-backdrop" id="menu-backdrop"></div>'
    + '<div class="mobile-menu-panel">'
    + '<div class="mobile-menu-header">'
    + '<span style="font-family:var(--font-mono);font-weight:600;font-size:18px">uz<span style="color:var(--accent)">shop</span></span>'
    + '<button onclick="closeMobileMenu()" style="width:32px;height:32px;border-radius:16px;background:var(--bg);display:flex;align-items:center;justify-content:center;border:none;cursor:pointer">'
    + '<svg width="14" height="14" viewBox="0 0 14 14"><path d="M2 2l10 10M12 2L2 12" stroke="var(--ink-2)" stroke-width="1.5" stroke-linecap="round"/></svg>'
    + '</button>'
    + '</div>'
    + '<div class="mobile-menu-search">'
    + '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="7" cy="7" r="4.5" stroke="var(--ink-3)" stroke-width="1.5"/><path d="M10.5 10.5L14 14" stroke="var(--ink-3)" stroke-width="1.5" stroke-linecap="round"/></svg>'
    + '<input type="text" placeholder="Mahsulot qidirish..." id="mobile-search"/>'
    + '</div>'
    + '<div class="mobile-menu-cats">'
    + '<p style="font-size:11px;font-weight:600;letter-spacing:1px;color:var(--ink-3);text-transform:uppercase;padding:4px 12px 8px">Menyu</p>'
    + mobileNavHTML
    + '<p style="font-size:11px;font-weight:600;letter-spacing:1px;color:var(--ink-3);text-transform:uppercase;padding:14px 12px 8px">Kategoriyalar</p>'
    + mobileCatsHTML
    + '</div>'
    + '<div class="mobile-menu-footer">'
    + '<a href="' + ROUTES.profile + '" style="display:flex;align-items:center;gap:12px;padding:12px;border-radius:var(--r-md);color:var(--ink-2);font-size:15px;font-weight:500">'
    + '<svg width="18" height="18" viewBox="0 0 18 18" fill="none"><circle cx="9" cy="6" r="3" stroke="currentColor" stroke-width="1.4"/><path d="M2 16c0-3.3 3.1-5 7-5s7 1.7 7 5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>'
    + 'Profil</a>'
    + '<a href="' + ROUTES.wishlist + '" style="display:flex;align-items:center;gap:12px;padding:12px;border-radius:var(--r-md);color:var(--ink-2);font-size:15px;font-weight:500">'
    + '<svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M9 14.5S2 10.5 2 6a3.5 3.5 0 0 1 7-0.7A3.5 3.5 0 0 1 16 6c0 4.5-7 8.5-7 8.5z" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/></svg>'
    + 'Istaklar</a>'
    + '</div>'
    + '</div>'
    + '</div>';

  document.body.insertAdjacentHTML('afterbegin', html);

  // Bottom nav
  var page = document.body && document.body.dataset ? document.body.dataset.page : '';
  var bottomNav = '<nav class="bottom-nav" id="bottom-nav">'
    + '<div class="bottom-nav-items">'
    + _bnItem(ROUTES.index, 'index', page, 'Bosh', '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M3 9l7-6 7 6v9H13v-5H7v5H3V9z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>')
    + _bnItem(ROUTES.shop, 'shop', page, 'Do\'kon', '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><rect x="2" y="5" width="16" height="12" rx="2" stroke="currentColor" stroke-width="1.5"/><path d="M2 9h16" stroke="currentColor" stroke-width="1.5"/><path d="M6 3l2 2M14 3l-2 2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>')
    + '<button class="bottom-nav-item' + (page === 'checkout' ? ' active' : '') + '" onclick="navigateWithLoader(\'' + ROUTES.checkout + '\')" style="position:relative">'
    + '<div style="width:48px;height:48px;border-radius:24px;background:var(--ink);display:flex;align-items:center;justify-content:center;margin-top:-20px;box-shadow:0 4px 16px rgba(0,0,0,0.2)">'
    + '<svg width="22" height="22" viewBox="0 0 20 20" fill="none"><path d="M3 3h1.5l2.5 9h7l2-6H6.5" stroke="#fff" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><circle cx="9" cy="16" r="1.2" fill="#fff"/><circle cx="14" cy="16" r="1.2" fill="#fff"/></svg>'
    + '</div>'
    + '<span id="bn-cart-badge" class="bottom-nav-badge" style="' + (count > 0 ? '' : 'display:none') + '">' + count + '</span>'
    + '<span style="margin-top:2px">Savat</span>'
    + '</button>'
    + _bnItem(ROUTES.wishlist, 'wishlist', page, 'Istaklar', '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M10 16s-7-4.5-7-9a4 4 0 0 1 7-2.65A4 4 0 0 1 17 7c0 4.5-7 9-7 9z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>')
    + _bnItem(ROUTES.profile, 'profile', page, 'Profil', '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><circle cx="10" cy="7" r="3" stroke="currentColor" stroke-width="1.5"/><path d="M3 17c0-3.3 3.1-6 7-6s7 2.7 7 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>')
    + '</div>'
    + '</nav>';
  document.body.insertAdjacentHTML('beforeend', bottomNav);

  // Cart badge live update
  window.addEventListener('cart-updated', function() {
    var n = Cart.getCount();
    ['nav-cart-badge','bn-cart-badge'].forEach(function(id) {
      var el = document.getElementById(id);
      if (!el) return;
      el.textContent = n;
      el.style.display = n > 0 ? 'flex' : 'none';
    });
  });

  // Hamburger toggle
  var hamburger = document.getElementById('hamburger-btn');
  if (hamburger) hamburger.addEventListener('click', openMobileMenu);
  var backdrop = document.getElementById('menu-backdrop');
  if (backdrop) backdrop.addEventListener('click', closeMobileMenu);

  // Mobile search
  var mobileSearch = document.getElementById('mobile-search');
  if (mobileSearch) {
    mobileSearch.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' && mobileSearch.value.trim()) {
        navigateWithLoader(buildShopUrl(null, mobileSearch.value.trim()));
      }
    });
  }

  // Desktop search
  var searchInput = document.getElementById('nav-search');
  if (searchInput) {
    searchInput.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' && searchInput.value.trim()) {
        navigateWithLoader(buildShopUrl(null, searchInput.value.trim()));
      }
    });
  }

  buildScrollFab();
}

function _bnItem(href, itemKey, currentPage, label, icon) {
  var isActive = currentPage === itemKey;
  return '<a href="' + href + '" class="bottom-nav-item' + (isActive ? ' active' : '') + '">'
    + icon + '<span>' + label + '</span></a>';
}

function buildScrollFab() {
  if (document.getElementById('scroll-fab')) return;
  var fab = document.createElement('button');
  fab.id = 'scroll-fab';
  fab.className = 'scroll-fab';
  fab.setAttribute('aria-label', 'Scroll');
  fab.innerHTML = scrollFabIcon('down');
  document.body.appendChild(fab);

  var mode = 'down';

  function setMode(next) {
    if (next === mode) return;
    mode = next;
    fab.innerHTML = scrollFabIcon(mode);
    fab.setAttribute('aria-label', mode === 'up' ? 'Tepaga' : 'Pastga');
  }

  function update() {
    var doc = document.documentElement;
    var max = Math.max(0, doc.scrollHeight - window.innerHeight);
    var scrolled = window.scrollY || window.pageYOffset || 0;
    if (max < 240) {
      fab.classList.remove('visible');
      return;
    }
    fab.classList.add('visible');
    setMode(scrolled > max - 120 ? 'up' : 'down');
  }

  fab.addEventListener('click', function() {
    if (mode === 'up') {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
      window.scrollTo({ top: document.documentElement.scrollHeight, behavior: 'smooth' });
    }
  });

  window.addEventListener('scroll', update, { passive: true });
  window.addEventListener('resize', update);
  // Re-check after layout settles (React mounts, late-loaded images, etc.)
  setTimeout(update, 200);
  setTimeout(update, 800);
  update();
}

function scrollFabIcon(mode) {
  if (mode === 'up') {
    return '<svg width="20" height="20" viewBox="0 0 20 20" fill="none">'
      + '<path d="M10 15V5M5 10l5-5 5 5" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
      + '</svg>';
  }
  return '<svg width="20" height="20" viewBox="0 0 20 20" fill="none">'
    + '<path d="M10 5v10M5 10l5 5 5-5" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
    + '</svg>';
}

function openMobileMenu() {
  var menu = document.getElementById('mobile-menu');
  if (menu) { menu.classList.add('open'); document.body.style.overflow = 'hidden'; }
}

function closeMobileMenu() {
  var menu = document.getElementById('mobile-menu');
  if (menu) { menu.classList.remove('open'); document.body.style.overflow = ''; }
}

// ── Footer builder ────────────────────────────────────────────────────────

function buildFooter() {
  var links1 = [
    { label: 'Mahsulotlar', href: ROUTES.shop },
    { label: 'Trend kolleksiya', href: ROUTES.index + '#featured' },
    { label: 'Istaklar', href: ROUTES.wishlist },
    { label: 'Profil', href: ROUTES.profile }
  ];
  var links2 = [
    { label: 'Global yetkazish', href: ROUTES.shop },
    { label: 'Premium brendlar', href: ROUTES.shop },
    { label: 'Yangi kelganlar', href: ROUTES.index + '#featured' },
    { label: 'Checkout', href: ROUTES.checkout }
  ];
  var links3 = [
    { label: 'Savol-javob', href: ROUTES.profile },
    { label: 'Buyurtma kuzatish', href: ROUTES.confirmation },
    { label: 'Qaytarish', href: ROUTES.checkout },
    { label: 'Bog‘lanish', href: ROUTES.profile }
  ];

  function linkList(arr) {
    return arr.map(function(link){
      return '<a href="' + link.href + '" style="font-size:14px;color:var(--ink-2);">' + link.label + '</a>';
    }).join('');
  }

  document.body.insertAdjacentHTML('beforeend',
    '<footer style="border-top:1px solid var(--border);margin-top:auto;">'
    + '<div class="page-wrap footer-grid" style="padding-top:40px;padding-bottom:40px;display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:40px;">'
    + '<div><div style="font-family:var(--font-mono);font-size:20px;font-weight:500;margin-bottom:12px;">uz<span style="color:var(--accent)">shop</span></div>'
    + '<p style="font-size:14px;color:var(--ink-3);line-height:1.7;max-width:320px;">uzshop global did, ishonchli servis va tezkor xarid oqimini birlashtirgan zamonaviy online do\'kon.</p></div>'
    + '<div><p style="font-size:11px;font-weight:600;letter-spacing:1px;color:var(--ink-3);text-transform:uppercase;margin-bottom:14px;">Havolalar</p>'
    + '<div style="display:flex;flex-direction:column;gap:8px;">' + linkList(links1) + '</div></div>'
    + '<div><p style="font-size:11px;font-weight:600;letter-spacing:1px;color:var(--ink-3);text-transform:uppercase;margin-bottom:14px;">Savdo</p>'
    + '<div style="display:flex;flex-direction:column;gap:8px;">' + linkList(links2) + '</div></div>'
    + '<div><p style="font-size:11px;font-weight:600;letter-spacing:1px;color:var(--ink-3);text-transform:uppercase;margin-bottom:14px;">Yordam</p>'
    + '<div style="display:flex;flex-direction:column;gap:8px;">' + linkList(links3) + '</div></div>'
    + '</div>'
    + '<div class="divider"></div>'
    + '<div class="page-wrap" style="padding-top:20px;padding-bottom:20px;display:flex;justify-content:space-between;align-items:center;font-size:13px;color:var(--ink-3);">'
    + '<span>&#169; ' + new Date().getFullYear() + ' uzshop. Barcha huquqlar himoyalangan.</span>'
    + '<span style="font-family:var(--font-mono)">Copywriter Asilbek Mirolimov</span>'
    + '</div>'
    + '</footer>'
  );
}
