/* ============================================================
   Happy Birthday website — interactive features
   ============================================================ */

/* ---------- 1. Configuration (edit these!) ---------- */
const CONFIG = {
  name: "Alex",                       // Birthday star's name
  birthday: { month: 8, day: 14 },    // Next birthday (month & day, 1-based)
  gallery: [
    { label: "Sweet moments", seed: "cake1" },
    { label: "Party time", seed: "party2" },
    { label: "Birthday smiles", seed: "smile3" },
    { label: "Cake & candles", seed: "candles4" },
    { label: "Best friends", seed: "friends5" },
    { label: "Good times", seed: "good6" }
  ]
};

const WISHES_KEY = "birthday-wishes";

// ---------- 2. Element shortcuts ----------
const $ = (id) => document.getElementById(id);
const nameEl = $("birthday-name");
const footerNameEl = $("footer-name");

// ---------- 3. Load saved name ----------
let birthdayName = localStorage.getItem("birthday-name") || CONFIG.name;
function applyName() {
  nameEl.textContent = birthdayName + "!";
  footerNameEl.textContent = birthdayName;
}
applyName();

$("edit-name-btn").addEventListener("click", () => {
  const name = prompt("Who are we celebrating?", birthdayName);
  if (name && name.trim()) {
    birthdayName = name.trim();
    localStorage.setItem("birthday-name", birthdayName);
    applyName();
    burstConfetti(140);
  }
});

// ---------- 4. Animated balloons ----------
(function makeBalloons() {
  const holder = $("balloons");
  const colors = ["#ff6b9d", "#f9a03f", "#8f6bff", "#4ecdc4", "#ffd166", "#ef476f"];
  for (let i = 0; i < 14; i++) {
    const b = document.createElement("div");
    b.className = "balloon";
    const size = 30 + Math.random() * 30;
    b.style.width = size + "px";
    b.style.height = size * 1.3 + "px";
    b.style.left = Math.random() * 100 + "%";
    b.style.background =
      "radial-gradient(circle at 30% 30%, rgba(255,255,255,0.5), " +
      colors[Math.floor(Math.random() * colors.length)] + ")";
    b.style.animationDuration = 12 + Math.random() * 14 + "s";
    b.style.animationDelay = -Math.random() * 20 + "s";
    holder.appendChild(b);
  }
})();

// ---------- 5. Confetti ----------
const canvas = $("confetti-canvas");
const ctx = canvas.getContext("2d");
let confettiPieces = [];
let confettiAnimating = false;

function resizeCanvas() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}
resizeCanvas();
window.addEventListener("resize", resizeCanvas);

const CONFETTI_COLORS = ["#ff6b9d", "#8f6bff", "#f9a03f", "#4ecdc4", "#ffd166", "#ef476f", "#ffffff"];

function burstConfetti(count) {
  for (let i = 0; i < count; i++) {
    confettiPieces.push({
      x: Math.random() * canvas.width,
      y: -20 - Math.random() * canvas.height * 0.3,
      w: 6 + Math.random() * 8,
      h: 8 + Math.random() * 12,
      color: CONFETTI_COLORS[Math.floor(Math.random() * CONFETTI_COLORS.length)],
      vy: 1.5 + Math.random() * 3,
      vx: (Math.random() - 0.5) * 1.4,
      rot: Math.random() * Math.PI,
      vrot: (Math.random() - 0.5) * 0.12,
      shape: Math.random() > 0.5 ? "rect" : "circle"
    });
  }
  if (!confettiAnimating) {
    confettiAnimating = true;
    requestAnimationFrame(drawConfetti);
  }
}

function drawConfetti() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  confettiPieces.forEach((p) => {
    p.x += p.vx;
    p.y += p.vy;
    p.rot += p.vrot;
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.rotate(p.rot);
    ctx.fillStyle = p.color;
    if (p.shape === "rect") {
      ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
    } else {
      ctx.beginPath();
      ctx.arc(0, 0, p.w / 2, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
  });

  confettiPieces = confettiPieces.filter((p) => p.y < canvas.height + 40);

  if (confettiPieces.length > 0) {
    requestAnimationFrame(drawConfetti);
  } else {
    confettiAnimating = false;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }
}

$("confetti-btn").addEventListener("click", () => burstConfetti(130));
window.addEventListener("load", () => {
  setTimeout(() => burstConfetti(90), 600);
});

// ---------- 6. Countdown ----------
function nextBirthday(month, day) {
  const now = new Date();
  let target = new Date(now.getFullYear(), month - 1, day, 0, 0, 0, 0);
  if (target.getTime() <= now.getTime()) {
    target = new Date(now.getFullYear() + 1, month - 1, day, 0, 0, 0, 0);
  }
  return target;
}

const countEls = {
  days: $("cd-days"),
  hours: $("cd-hours"),
  minutes: $("cd-minutes"),
  seconds: $("cd-seconds")
};

function pad(n) {
  return String(n).padStart(2, "0");
}

function updateCountdown() {
  const diff = nextBirthday(CONFIG.birthday.month, CONFIG.birthday.day) - new Date();
  if (diff <= 0) return;
  countEls.days.textContent = pad(Math.floor(diff / 86400000));
  countEls.hours.textContent = pad(Math.floor(diff / 3600000) % 24);
  countEls.minutes.textContent = pad(Math.floor(diff / 60000) % 60);
  countEls.seconds.textContent = pad(Math.floor(diff / 1000) % 60);
}
updateCountdown();
setInterval(updateCountdown, 1000);

// ---------- 7. Gallery (placeholder images) ----------
(function buildGallery() {
  const grid = $("gallery-grid");
  CONFIG.gallery.forEach((item) => {
    const fig = document.createElement("figure");
    fig.className = "gallery-card";

    const img = document.createElement("img");
    img.src = "https://picsum.photos/seed/" + item.seed + "/400/280";
    img.alt = item.label;
    img.loading = "lazy";

    const cap = document.createElement("figcaption");
    cap.textContent = item.label;

    fig.appendChild(img);
    fig.appendChild(cap);
    grid.appendChild(fig);
  });
})();

// ---------- 8. Wish wall ----------
const wishForm = $("wish-form");
const wishName = $("wish-name");
const wishMessage = $("wish-message");
const wishGrid = $("wish-grid");

function loadWishes() {
  try {
    return JSON.parse(localStorage.getItem(WISHES_KEY)) || [];
  } catch {
    return [];
  }
}

function saveWishes(wishes) {
  localStorage.setItem(WISHES_KEY, JSON.stringify(wishes));
}

function renderWishes() {
  wishGrid.innerHTML = "";
  const wishes = loadWishes();
  if (wishes.length === 0) {
    const empty = document.createElement("p");
    empty.textContent = "No wishes yet — be the first to leave one! 🎈";
    empty.style.color = "var(--soft)";
    wishGrid.appendChild(empty);
    return;
  }
  wishes.forEach((w) => {
    const card = document.createElement("div");
    card.className = "wish-card";

    const name = document.createElement("div");
    name.className = "wish-card-name";
    name.textContent = w.name;

    const text = document.createElement("div");
    text.className = "wish-card-text";
    text.textContent = w.message;

    const time = document.createElement("div");
    time.className = "wish-card-time";
    time.textContent = new Date(w.time).toLocaleString();

    card.appendChild(name);
    card.appendChild(text);
    card.appendChild(time);
    wishGrid.appendChild(card);
  });
}

wishForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const wishes = loadWishes();
  wishes.unshift({
    name: wishName.value.trim(),
    message: wishMessage.value.trim(),
    time: Date.now()
  });
  saveWishes(wishes.slice(0, 50)); // keep newest 50
  wishName.value = "";
  wishMessage.value = "";
  renderWishes();
  burstConfetti(70);
});

renderWishes();