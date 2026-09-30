const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");
const finePointer = matchMedia("(hover: hover) and (pointer: fine)");
const saveData = navigator.connection?.saveData === true;
const IN_VIEW = 0.6;
const TOUCH_PREVIEW_MS = 5000;
const MAIL = ["moc.liamg", "lk80drahnoel"];
const STRINGS = {
  en: { play: "Play clip", pause: "Pause clip", count: (i, n) => `${i} of ${n}` },
  de: { play: "Clip abspielen", pause: "Clip anhalten", count: (i, n) => `${i} von ${n}` },
};
const TEXT = STRINGS[document.documentElement.lang] ?? STRINGS.en;

const mayAutoplay = () => !reducedMotion.matches && !saveData;

function setUpMail() {
  const address = MAIL.map((part) => [...part].reverse().join("")).reverse().join("@");
  for (const link of document.querySelectorAll("a[data-mail]")) link.href = `mailto:${address}`;
  for (const text of document.querySelectorAll("[data-mail-show]")) text.textContent = address;
}

function play(video) {
  if (!video.getAttribute("src")) video.src = video.dataset.src;
  video.play().catch(() => {});
}

function watchVisibility(items, onEnter, onLeave) {
  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (entry.intersectionRatio >= IN_VIEW) onEnter(entry.target);
      else onLeave(entry.target);
    }
  }, { threshold: [0, IN_VIEW] });
  for (const item of items) observer.observe(item);
}

function setUpCards() {
  const cards = [...document.querySelectorAll("[data-card]")];
  for (const card of cards) {
    const video = card.querySelector("video");
    video.addEventListener("playing", () => card.classList.add("is-live"));
    video.addEventListener("pause", () => card.classList.remove("is-live"));
    card.addEventListener("pointerenter", () => finePointer.matches && mayAutoplay() && play(video));
    card.addEventListener("pointerleave", () => finePointer.matches && video.pause());
    card.addEventListener("focus", () => mayAutoplay() && play(video));
    card.addEventListener("blur", () => video.pause());
  }

  if (finePointer.matches) return;
  const timers = new WeakMap();
  watchVisibility(
    cards,
    (card) => {
      if (!mayAutoplay()) return;
      const video = card.querySelector("video");
      play(video);
      timers.set(card, setTimeout(() => video.pause(), TOUCH_PREVIEW_MS));
    },
    (card) => {
      clearTimeout(timers.get(card));
      card.querySelector("video").pause();
    },
  );
}

function setUpClips() {
  const clips = [...document.querySelectorAll("[data-clip]")];
  const pausedByUser = new WeakSet();

  for (const clip of clips) {
    const video = clip.querySelector("video");
    const toggle = clip.querySelector(".clip__toggle");
    video.addEventListener("playing", () => clip.classList.add("is-live", "is-playing"));
    video.addEventListener("pause", () => clip.classList.remove("is-playing"));
    video.addEventListener("play", () => toggle.setAttribute("aria-label", TEXT.pause));
    video.addEventListener("pause", () => toggle.setAttribute("aria-label", TEXT.play));
    toggle.addEventListener("click", () => {
      if (video.paused) {
        pausedByUser.delete(clip);
        play(video);
      } else {
        pausedByUser.add(clip);
        video.pause();
      }
    });
  }

  watchVisibility(
    clips,
    (clip) => mayAutoplay() && !pausedByUser.has(clip) && play(clip.querySelector("video")),
    (clip) => clip.querySelector("video").pause(),
  );
}

function setUpLightbox() {
  const dialog = document.querySelector("[data-lightbox]");
  if (!dialog) return;
  const links = [...document.querySelectorAll("[data-shot]")];
  const image = dialog.querySelector("img");
  const caption = dialog.querySelector("figcaption");
  let index = 0;

  const show = (next) => {
    index = (next + links.length) % links.length;
    image.src = links[index].href;
    image.alt = links[index].querySelector("img").alt;
    caption.textContent = TEXT.count(index + 1, links.length);
  };
  const open = (at) => {
    show(at);
    dialog.showModal();
  };

  links.forEach((link, i) => {
    link.addEventListener("click", (event) => {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.button !== 0) return;
      event.preventDefault();
      open(i);
    });
  });
  document.querySelector("[data-shots-all]")?.addEventListener("click", () => open(0));
  dialog.querySelector("[data-prev]").addEventListener("click", () => show(index - 1));
  dialog.querySelector("[data-next]").addEventListener("click", () => show(index + 1));
  dialog.querySelector("[data-close]").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (event) => event.target === dialog && dialog.close());
  dialog.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft") show(index - 1);
    if (event.key === "ArrowRight") show(index + 1);
  });
}

setUpMail();
setUpCards();
setUpClips();
setUpLightbox();
