(function () {
  'use strict';

  /* ---------- Header scroll ---------- */
  var header = document.getElementById('header');
  var scrollTopBtn = document.getElementById('scrollTop');

  if (header) {
    window.addEventListener('scroll', function () {
      var y = window.pageYOffset || document.documentElement.scrollTop;
      header.classList.toggle('scrolled', y > 80);
      if (scrollTopBtn) scrollTopBtn.classList.toggle('show', y > 400);
    }, { passive: true });
  }

  if (scrollTopBtn) {
    scrollTopBtn.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  /* ---------- Mobile menu ---------- */
  var burger = document.getElementById('burger');
  var mobileMenu = document.getElementById('mobileMenu');
  var mobileLinks = document.querySelectorAll('[data-mobile-link]');
  var isMenuOpen = false;

  function openMenu() {
    isMenuOpen = true;
    if (burger) burger.classList.add('active');
    if (mobileMenu) mobileMenu.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeMenu() {
    isMenuOpen = false;
    if (burger) burger.classList.remove('active');
    if (mobileMenu) mobileMenu.classList.remove('open');
    document.body.style.overflow = '';
  }

  function toggleMenu() {
    isMenuOpen ? closeMenu() : openMenu();
  }

  if (burger) {
    burger.addEventListener('click', toggleMenu);
  }

  mobileLinks.forEach(function (link) {
    link.addEventListener('click', closeMenu);
  });

  if (mobileMenu) {
    mobileMenu.addEventListener('click', function (e) {
      if (e.target === mobileMenu) closeMenu();
    });
  }

  /* Swipe to close mobile menu */
  var touchStartY = 0;
  var touchMoveY = 0;
  var touchMoved = false;

  if (mobileMenu) {
    mobileMenu.addEventListener('touchstart', function (e) {
      touchStartY = e.touches[0].clientY;
      touchMoveY = touchStartY;
      touchMoved = false;
    }, { passive: true });

    mobileMenu.addEventListener('touchmove', function (e) {
      touchMoveY = e.touches[0].clientY;
      touchMoved = true;
    }, { passive: true });

    mobileMenu.addEventListener('touchend', function () {
      if (touchMoved) {
        var diff = touchStartY - touchMoveY;
        if (diff > 50 && isMenuOpen) closeMenu();
      }
      touchStartY = 0;
      touchMoveY = 0;
      touchMoved = false;
    }, { passive: true });
  }

  /* ---------- Reveal on scroll ---------- */
  var revealObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

  document.querySelectorAll('.reveal').forEach(function (el) {
    revealObserver.observe(el);
  });

  /* ---------- Smooth scroll for anchors ---------- */
  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener('click', function (e) {
      var target = document.querySelector(this.getAttribute('href'));
      if (!target) return;
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });

  /* ---------- Gallery & Lightbox ---------- */
  var galleryGrid = document.getElementById('galleryGrid');
  var lightbox = document.getElementById('lightbox');
  var lightboxImg = document.getElementById('lightboxImg');
  var lightboxCounter = document.getElementById('lightboxCounter');
  var lightboxClose = document.getElementById('lightboxClose');
  var lightboxPrev = document.getElementById('lightboxPrev');
  var lightboxNext = document.getElementById('lightboxNext');
  var currentLightboxIndex = 0;
  window.BB = window.BB || {};
  window.BB.GALLERY = window.BB.GALLERY || [];

  function getGalleryItems() {
    return window.BB.GALLERY;
  }

  function openLightbox(id) {
    var items = getGalleryItems();
    var idx = items.findIndex(function (g) { return g.id === id; });
    if (idx === -1) return;
    currentLightboxIndex = idx;
    showLightboxImage();
    if (lightbox) lightbox.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function showLightboxImage() {
    var items = getGalleryItems();
    var item = items[currentLightboxIndex];
    if (!item || !lightboxImg || !lightboxCounter) return;
    lightboxImg.src = item.src;
    lightboxImg.alt = item.alt;
    lightboxCounter.textContent = (currentLightboxIndex + 1) + ' / ' + items.length;
  }

  function closeLightbox() {
    if (lightbox) lightbox.classList.remove('open');
    document.body.style.overflow = '';
  }

  function prevLightbox() {
    var items = getGalleryItems();
    currentLightboxIndex = (currentLightboxIndex - 1 + items.length) % items.length;
    showLightboxImage();
  }

  function nextLightbox() {
    var items = getGalleryItems();
    currentLightboxIndex = (currentLightboxIndex + 1) % items.length;
    showLightboxImage();
  }

  if (lightboxClose) lightboxClose.addEventListener('click', closeLightbox);
  if (lightboxPrev) lightboxPrev.addEventListener('click', prevLightbox);
  if (lightboxNext) lightboxNext.addEventListener('click', nextLightbox);

  if (lightbox) {
    lightbox.addEventListener('click', function (e) {
      if (e.target === lightbox) closeLightbox();
    });
  }

  document.addEventListener('keydown', function (e) {
    if (!lightbox || !lightbox.classList.contains('open')) return;
    if (e.key === 'Escape') closeLightbox();
    if (e.key === 'ArrowLeft') prevLightbox();
    if (e.key === 'ArrowRight') nextLightbox();
  });

  /* Lightbox swipe */
  var lbTouchStartX = 0;
  var lbTouchEndX = 0;

  if (lightbox) {
    lightbox.addEventListener('touchstart', function (e) {
      lbTouchStartX = e.changedTouches[0].screenX;
    }, { passive: true });

    lightbox.addEventListener('touchend', function (e) {
      lbTouchEndX = e.changedTouches[0].screenX;
      var diff = lbTouchStartX - lbTouchEndX;
      if (Math.abs(diff) > 50) {
        if (diff > 0) nextLightbox();
        else prevLightbox();
      }
    }, { passive: true });
  }

  /* ---------- Expose for page-specific JS ---------- */
  window.BB = {
    GALLERY: window.BB.GALLERY,
    openLightbox: openLightbox,
    closeLightbox: closeLightbox,
    revealObserver: revealObserver
  };

})();
