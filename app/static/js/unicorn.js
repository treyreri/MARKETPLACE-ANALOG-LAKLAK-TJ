// Original pixel-art unicorn: a 16x16 grid of <rect>s on Midnight Navy.
// Brand element only: logo, hero, empty states, loading.

const COLORS = {
  W: "#F4F8FB", // coat
  S: "#D1E7F1", // coat shade (Alice Blue)
  A: "#70C9B1", // horn / mane (Pearl Aqua)
  P: "#D5CAF5", // mane (Periwinkle)
  C: "#3A879D", // mane shadow (Pacific Cyan)
  T: "#0C423F", // eye, nostril (Pine Teal)
};
const NAVY = "#0B062F";

// Head and neck facing right, horn up, mane flowing on the left.
const GRID = [
  "................",
  "..........A.....",
  ".........AW.....",
  "....PP..AAW.....",
  "...PCPPWWWW.....",
  "..PCAPWWWWWW....",
  "..PCPWWWTWWWW...",
  ".PCAPWWWWWWWWW..",
  ".PCPWWWWWWWWWWW.",
  ".PAPWWWWWWWWWTW.",
  "PCPWWWWWSSSSSSS.",
  "PCAWWWWWS.......",
  "PCPWWWWWS.......",
  ".PCWWWWWWS......",
  ".PAWWWWWWWS.....",
  "..CWWWWWWWWS....",
];

// A few sparkle pixels for the hero only (x, y, color) in the 24x24 frame
const SPARKLES = [[3, 4, "P"], [20, 3, "A"], [21, 16, "P"], [2, 18, "A"], [18, 21, "S"]];

const SVG_NS = "http://www.w3.org/2000/svg";

function rectsFor(grid, offset) {
  const parts = [];
  grid.forEach((row, y) => {
    // merge horizontal runs of the same color into one rect
    let x = 0;
    while (x < row.length) {
      const color = row[x];
      let end = x;
      while (end + 1 < row.length && row[end + 1] === color) end += 1;
      if (color !== ".") {
        parts.push(`<rect x="${x + offset}" y="${y + offset}" width="${end - x + 1}" height="1" fill="${COLORS[color]}"/>`);
      }
      x = end + 1;
    }
  });
  return parts.join("");
}

/**
 * @param {{ frame?: number, radius?: number, sparkles?: boolean, title?: string }} options
 */
export function unicornSVG({ frame = 20, radius = 3, sparkles = false, title = "Pixel Unicorn" } = {}) {
  const offset = (frame - 16) / 2;
  const sparkleRects = sparkles
    ? SPARKLES.map(([x, y, c]) => `<rect class="sparkle" x="${x}" y="${y}" width="1" height="1" fill="${COLORS[c]}"/>`).join("")
    : "";
  return `<svg xmlns="${SVG_NS}" viewBox="0 0 ${frame} ${frame}" shape-rendering="crispEdges" role="img" aria-label="${title}">`
    + `<rect width="${frame}" height="${frame}" rx="${radius}" fill="${NAVY}"/>`
    + sparkleRects + rectsFor(GRID, offset) + "</svg>";
}

const VARIANTS = {
  logo: { frame: 20, radius: 4 },
  hero: { frame: 24, radius: 3, sparkles: true },
  empty: { frame: 22, radius: 5 },
  loading: { frame: 20, radius: 5 },
};

export function renderUnicorns(root = document) {
  root.querySelectorAll("[data-unicorn]").forEach((el) => {
    if (el.dataset.rendered) return;
    el.innerHTML = unicornSVG(VARIANTS[el.dataset.unicorn] ?? VARIANTS.logo);
    el.classList.add("unicorn", `unicorn-${el.dataset.unicorn}`);
    el.dataset.rendered = "1";
  });
}

/** Empty state block: unicorn + message. */
export function emptyState(message) {
  const el = document.createElement("div");
  el.className = "empty-state";
  el.innerHTML = '<span data-unicorn="empty"></span><p></p>';
  el.querySelector("p").textContent = message;
  renderUnicorns(el);
  return el;
}

/** Loading block: bobbing unicorn + label. */
export function loadingState(label) {
  const el = document.createElement("div");
  el.className = "loading-state";
  el.setAttribute("role", "status");
  el.innerHTML = '<span data-unicorn="loading"></span><p></p>';
  el.querySelector("p").textContent = label;
  renderUnicorns(el);
  return el;
}
