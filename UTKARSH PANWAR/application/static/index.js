// ── PRELOADER PARTICLES + LOAD PROGRESS ──
(function () {
  const canvas = document.getElementById("preloader-canvas");
  const ctx = canvas.getContext("2d");
  const pctEl = document.getElementById("preloader-pct");
  let W, H, particles = [], raf;
  let displayedPct = 0;   // smoothly animated value
  let targetPct    = 0;   // real tracked value
  let dismissed    = false;

  function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener("resize", resize);

  for (let i = 0; i < 80; i++) {
    particles.push({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      r: Math.random() * 1.5 + 0.3,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      a: Math.random(),
    });
  }

  function drawParticles() {
    ctx.clearRect(0, 0, W, H);
    particles.forEach((p) => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(232,98,42,${p.a * 0.6})`;
      ctx.fill();
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
      if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;
    });
    // Smoothly animate displayed percentage toward target
    if (displayedPct < targetPct) {
      displayedPct = Math.min(displayedPct + 1.2, targetPct);
      if (pctEl) pctEl.textContent = Math.floor(displayedPct) + "%";
    }
    raf = requestAnimationFrame(drawParticles);
  }
  drawParticles();

  // ── Track real resource loading ──
  const resources = performance.getEntriesByType
    ? performance.getEntriesByType("resource")
    : [];

  // Use PerformanceObserver to count resources as they finish
  let loaded = 0;
  let total  = Math.max(1, resources.length || 20); // initial estimate

  function setProgress(pct) {
    targetPct = Math.min(99, Math.max(targetPct, pct));
  }

  // Track resources landing via PerformanceObserver
  if (typeof PerformanceObserver !== "undefined") {
    try {
      const obs = new PerformanceObserver((list) => {
        loaded += list.getEntries().length;
        total   = Math.max(total, loaded + 2);
        setProgress(Math.round((loaded / total) * 92));
      });
      obs.observe({ type: "resource", buffered: true });
    } catch(e) {}
  }

  // Simulate smooth early progress so counter isn't stuck at 0
  let fake = 0;
  const fakeTimer = setInterval(() => {
    fake += Math.random() * 6;
    setProgress(Math.min(fake, 60));
    if (fake >= 60) clearInterval(fakeTimer);
  }, 180);

  // Preloader letter animation
  const letters = ["letter1", "letter2", "letter3"].map((id) => document.getElementById(id));
  letters.forEach((letter, i) => {
    setTimeout(() => {
      letter.style.animation = "thqPop 0.6s cubic-bezier(0.175,0.885,0.32,1.275) forwards";
      if (i === 2) {
        const ul = document.getElementById("underline");
        if (ul) ul.style.animation = "underlineGrow 0.6s ease forwards";
      }
    }, i * 500);
  });

  function dismissPreloader() {
    if (dismissed) return;
    dismissed = true;
    clearInterval(fakeTimer);
    // Snap to 100%
    targetPct = 100;
    // Wait for the counter to visually hit 100 before fading
    const waitFor100 = setInterval(() => {
      if (displayedPct >= 99) {
        clearInterval(waitFor100);
        if (pctEl) pctEl.textContent = "100%";
        const pre = document.getElementById("preloader");
        setTimeout(() => {
          pre.style.opacity = "0";
          setTimeout(() => {
            pre.style.display = "none";
            cancelAnimationFrame(raf);
            initHeroParticles();
            scrambleHeroName();
          }, 800);
        }, 300);
      }
    }, 30);
  }

  // Dismiss when page fully loaded AND minimum letter animation done (≥1.8s)
  const MIN_SHOW = 1800;
  const startTime = Date.now();
  window.addEventListener("load", () => {
    const elapsed = Date.now() - startTime;
    const wait    = Math.max(0, MIN_SHOW - elapsed);
    setTimeout(dismissPreloader, wait);
  });

  // Hard fallback: dismiss after 8s no matter what
  setTimeout(dismissPreloader, 8000);
})();

// ── HERO NAME LETTER REVEAL ──
function scrambleHeroName() {
  const el = document.getElementById("T1");
  if (!el) return;

  // Build: UTKARSH on line 1, PANWAR on line 2 (accent span)
  const word1 = "UTKARSH";
  const word2 = "PANWAR";
  const stagger = 80;   // ms between each letter
  const word2Delay = word1.length * stagger + 220; // gap between words

  // Wrap each letter in a span.char, word2 inside span.word
  el.innerHTML =
    word1.split("").map(ch => `<span class="char">${ch}</span>`).join("") +
    `<span class="word">` +
      word2.split("").map(ch => `<span class="char">${ch}</span>`).join("") +
    `</span>`;

  // Make T1 itself visible (override the fadeUp animation)
  el.style.opacity = "1";
  el.style.animation = "none";

  // Stagger word1 letters
  el.querySelectorAll(":scope > span.char").forEach((span, i) => {
    setTimeout(() => span.classList.add("in"), i * stagger);
  });

  // Stagger word2 letters
  el.querySelectorAll(".word span.char").forEach((span, i) => {
    setTimeout(() => span.classList.add("in"), word2Delay + i * stagger);
  });
}

// ── HERO PARTICLES ──
function initHeroParticles() {
  const canvas = document.getElementById("particle-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  let W, H, pts = [];

  function resize() {
    W = canvas.width = canvas.offsetWidth;
    H = canvas.height = canvas.offsetHeight;
  }
  resize();
  window.addEventListener("resize", resize);

  for (let i = 0; i < 60; i++) {
    pts.push({
      x: Math.random() * W, y: Math.random() * H,
      r: Math.random() * 1.2 + 0.2,
      vx: (Math.random() - 0.5) * 0.3,
      vy: -Math.random() * 0.5 - 0.1,
      a: Math.random() * 0.5 + 0.1,
    });
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    pts.forEach((p) => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(232,98,42,${p.a})`;
      ctx.fill();
      p.x += p.vx; p.y += p.vy;
      if (p.y < -5) { p.y = H + 5; p.x = Math.random() * W; }
      if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
    });
    requestAnimationFrame(draw);
  }
  draw();
}

// ── CUSTOM CURSOR ──
const cursor = document.getElementById("cursor");
const follower = document.getElementById("cursor-follower");
let fx = 0, fy = 0, mx = 0, my = 0;

document.addEventListener("mousemove", (e) => {
  mx = e.clientX; my = e.clientY;
  cursor.style.left = mx + "px";
  cursor.style.top = my + "px";
});

(function animFollower() {
  fx += (mx - fx) * 0.12;
  fy += (my - fy) * 0.12;
  follower.style.left = fx + "px";
  follower.style.top = fy + "px";
  requestAnimationFrame(animFollower);
})();

// hide custom cursor on interactive elements, show native pointer
document.addEventListener("mouseover", (e) => {
  if (e.target.closest("a, button, [role='button']")) {
    cursor.style.opacity = "0";
    follower.style.opacity = "0";
    document.body.style.cursor = "pointer";
  }
});
document.addEventListener("mouseout", (e) => {
  if (e.target.closest("a, button, [role='button']")) {
    cursor.style.opacity = "1";
    follower.style.opacity = "1";
    document.body.style.cursor = "none";
  }
});

// ── HEADER SCROLL ──
const header = document.getElementById("header");
window.addEventListener("scroll", () => {
  header.classList.toggle("scrolled", window.scrollY > 60);
});

// ── MOBILE NAV ──
const hamMenu = document.getElementById("ham-menu");
const navBar = document.getElementById("nav-bar");

hamMenu.addEventListener("click", () => {
  navBar.classList.toggle("active");
  hamMenu.classList.toggle("fa-times");
  hamMenu.classList.toggle("fa-bars");
});

navBar.querySelectorAll(".nav-link").forEach((link) => {
  link.addEventListener("click", () => {
    navBar.classList.remove("active");
    hamMenu.classList.remove("fa-times");
    hamMenu.classList.add("fa-bars");
  });
});

// ── SCROLL REVEAL ──
const revealObserver = new IntersectionObserver(
  (entries) => entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("visible"); revealObserver.unobserve(e.target); } }),
  { threshold: 0.15 }
);
document.querySelectorAll("section").forEach((section) => {
  section.querySelectorAll(".reveal").forEach((el, i) => {
    el.style.transitionDelay = (i % 5) * 0.12 + "s";
    revealObserver.observe(el);
  });
});

// ── SHOWREEL BUTTON ──
const B1 = document.getElementById("B1");
const myVideo2 = document.getElementById("myVideo2");
const bgVideo = document.getElementById("myVideo");
const showreelModal = document.getElementById("showreel-modal");

function openShowreel() {
  myVideo2.src = myVideo2.dataset.src;
  showreelModal.classList.add("open");
  document.body.style.overflow = "hidden";
  bgVideo.pause();
}

function closeShowreel() {
  showreelModal.classList.remove("open");
  myVideo2.src = "";
  document.body.style.overflow = "";
  bgVideo.play();
}

B1.addEventListener("click", openShowreel);
showreelModal.addEventListener("click", (e) => { if (e.target === showreelModal) closeShowreel(); });

// ── STILLS LIGHTBOX ── (wired dynamically by syncStills in index.html)
const lightbox = document.getElementById("lightbox");
const lightboxImg = document.getElementById("lightbox-img");
lightbox.addEventListener("click", (e) => {
  if (e.target === lightbox) {
    lightbox.classList.remove("open");
    document.body.style.overflow = "";
  }
});

// ── STILLS MOBILE DOTS INDICATOR ──
(function () {
  const grid = document.getElementById("stills-grid");
  if (!grid || window.innerWidth > 767) return;

  // inject dots container after grid
  const dotsWrap = document.createElement("div");
  dotsWrap.id = "stills-dots";
  dotsWrap.style.cssText = "display:flex;justify-content:center;gap:6px;margin-top:1.4rem;";
  grid.parentElement.insertBefore(dotsWrap, grid.nextSibling);

  const items = [...grid.querySelectorAll(".still-item")];
  const dots = items.map((_, i) => {
    const d = document.createElement("span");
    d.style.cssText = `width:6px;height:6px;border-radius:50%;background:${i === 0 ? "var(--accent)" : "rgba(255,255,255,0.25)"};transition:background 0.3s,transform 0.3s;display:inline-block;`;
    dotsWrap.appendChild(d);
    return d;
  });

  function updateDots() {
    const scrollLeft = grid.scrollLeft;
    const itemW = items[0].offsetWidth + 12; // width + gap
    const active = Math.round(scrollLeft / itemW);
    dots.forEach((d, i) => {
      d.style.background = i === active ? "var(--accent)" : "rgba(255,255,255,0.25)";
      d.style.transform = i === active ? "scale(1.4)" : "scale(1)";
    });
  }

  grid.addEventListener("scroll", updateDots, { passive: true });
})();


document.querySelectorAll(".wc-play-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const card = btn.closest(".work-card");
    if (card.classList.contains("playing")) return;
    const id = card.dataset.vimeo;
    const [base, hash] = id.split("?");
    const src = `https://player.vimeo.com/video/${base}${hash ? "?" + hash + "&" : "?"}autoplay=1&title=0&byline=0&portrait=0`;
    const iframe = document.createElement("iframe");
    iframe.src = src;
    iframe.className = "wc-iframe";
    iframe.setAttribute("frameborder", "0");
    iframe.setAttribute("allow", "autoplay; picture-in-picture");
    card.querySelector(".wc-media").appendChild(iframe);
    card.classList.add("playing");
  });
});

document.querySelectorAll(".wc-close").forEach((btn) => {
  btn.addEventListener("click", () => {
    const card = btn.closest(".work-card");
    const iframe = card.querySelector(".wc-iframe");
    if (iframe) iframe.remove();
    card.classList.remove("playing");
  });
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    if (showreelModal.classList.contains("open")) closeShowreel();
    else if (lightbox.classList.contains("open")) {
      lightbox.classList.remove("open");
      document.body.style.overflow = "";
    }
  }
  if (lightbox.classList.contains("open") && window._stillsSrcs) {
    const img = document.getElementById("lightbox-img");
    if (e.key === "ArrowRight") {
      window._stillsIndex = (window._stillsIndex + 1) % window._stillsSrcs.length;
      img.src = window._stillsSrcs[window._stillsIndex];
    }
    if (e.key === "ArrowLeft") {
      window._stillsIndex = (window._stillsIndex - 1 + window._stillsSrcs.length) % window._stillsSrcs.length;
      img.src = window._stillsSrcs[window._stillsIndex];
    }
  }
  if (e.key === "f" || e.key === "F") {
    if (!document.fullscreenElement) document.documentElement.requestFullscreen?.();
    else document.exitFullscreen?.();
  }
});

// ── EXPERIENCE COUNTER ──
// target is set by data.js from the DB (data-target attr), fallback to 7000
const expNum = document.getElementById("exp-num");
if (expNum) {
  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const target = parseInt(expNum.dataset.target) || 7000;
        let count = 0;
        const step = target / 80;
        const interval = setInterval(() => {
          count = Math.min(count + step, target);
          expNum.innerHTML = Math.ceil(count).toLocaleString() + "<span>+</span>";
          if (count >= target) clearInterval(interval);
        }, 20);
        counterObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });
  counterObserver.observe(expNum);
}

// ── DEVELOPER CREDIT ──
document.getElementById("developer-credit")?.addEventListener("click", () => {
  window.open("https://abhinavpanwar.netlify.app", "_blank");
});
