// Presentation finish, applied after every render: numbers count up and
// sections rise into view as they are reached. Pure decoration: the final text
// is always what the data says, and nothing runs under reduced motion or
// automated browsers (tests and screenshots read the final state at once).

const quiet = () =>
  navigator.webdriver || window.matchMedia("(prefers-reduced-motion: reduce)").matches || !("IntersectionObserver" in window);

// "78.5%", "£48.65m", "$0.07–$0.11", "1,280", "2 of 31": animate the first number only.
const NUM = /(-?\d[\d,]*\.?\d*)/;

function countUp(el) {
  const node = [...el.childNodes].find((n) => n.nodeType === 3 && NUM.test(n.textContent));
  if (!node) return;
  const text = node.textContent;
  const m = text.match(NUM);
  const raw = m[1];
  const target = parseFloat(raw.replace(/,/g, ""));
  if (!isFinite(target) || target === 0) return;
  const decimals = (raw.split(".")[1] || "").length;
  const commas = raw.includes(",");
  const fmt = (v) => {
    const s = v.toFixed(decimals);
    return commas ? Number(s).toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals }) : s;
  };
  const t0 = performance.now(), dur = 900;
  const step = (t) => {
    const k = Math.min(1, (t - t0) / dur);
    const e = 1 - Math.pow(1 - k, 3);
    node.textContent = text.replace(raw, fmt(target * e));
    if (k < 1) requestAnimationFrame(step);
    else node.textContent = text; // always end on the exact original text
  };
  requestAnimationFrame(step);
}

const COUNT = ".figure .big, .dec-hl .big, .ov-v, .goal .g-v, .h-fact > b, .ov-cost b, .cl-tile b, .vc > em";
const RISE = ".h-sec .h-wrap > *, .card, .goal, .dr, .vc, .h-fact, .ov-m > div, .ov-cost > div, .rp-card, .pane > section, .option";

export function enhance(root) {
  if (quiet()) return;
  const seen = new WeakSet();
  const io = new IntersectionObserver(
    (entries) => {
      for (const en of entries) {
        if (!en.isIntersecting) continue;
        const el = en.target;
        io.unobserve(el);
        if (el.matches(COUNT)) countUp(el);
        if (el.classList.contains("rise")) el.classList.add("in");
      }
    },
    { rootMargin: "0px 0px -8% 0px", threshold: 0.08 }
  );
  root.querySelectorAll(RISE).forEach((el, i) => {
    if (seen.has(el)) return;
    seen.add(el);
    el.classList.add("rise");
    el.style.setProperty("--rise-d", `${Math.min(i % 6, 5) * 45}ms`);
    io.observe(el);
  });
  root.querySelectorAll(COUNT).forEach((el) => io.observe(el));
}
