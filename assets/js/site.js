const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");
const saveData = navigator.connection?.saveData === true;
const IN_VIEW = 0.6;
const MAIL = ["moc.liamg", "lk80drahnoel"];
const STRINGS = {
  en: { play: "Play clip", pause: "Pause clip", count: (i, n) => `${i} of ${n}`, showPlay: "Play the slideshow", showPause: "Pause the slideshow" },
  de: { play: "Clip abspielen", pause: "Clip anhalten", count: (i, n) => `${i} von ${n}`, showPlay: "Diashow abspielen", showPause: "Diashow anhalten" },
};
const TEXT = STRINGS[document.documentElement.lang] ?? STRINGS.en;

const mayAutoplay = () => !reducedMotion.matches && !saveData;

function setUpMail() {
  const address = MAIL.map((part) => [...part].reverse().join("")).reverse().join("@");
  for (const link of document.querySelectorAll("a[data-mail]")) {
    const subject = link.dataset.mail ? `?subject=${encodeURIComponent(link.dataset.mail)}` : "";
    link.href = `mailto:${address}${subject}`;
  }
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

function setUpClips() {
  const clips = [...document.querySelectorAll("[data-clip]")];
  const pausedByUser = new WeakSet();

  for (const clip of clips) {
    const video = clip.querySelector("video");
    const toggle = clip.querySelector(".clip__toggle");
    const heading = clip.querySelector("h3") ?? clip.closest("section")?.querySelector("h2");
    const label = (action) => (heading ? `${action}: ${heading.textContent}` : action);
    toggle.setAttribute("aria-label", label(TEXT.play));
    video.addEventListener("playing", () => clip.classList.add("is-live", "is-playing"));
    video.addEventListener("pause", () => clip.classList.remove("is-playing"));
    video.addEventListener("play", () => toggle.setAttribute("aria-label", label(TEXT.pause)));
    video.addEventListener("pause", () => toggle.setAttribute("aria-label", label(TEXT.play)));
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

function setUpShowcase() {
  const showcase = document.querySelector("[data-showcase]");
  if (!showcase) return;
  const slides = [...showcase.querySelectorAll("[data-slide]")];
  const picks = [...showcase.querySelectorAll("[data-pick]")];
  const pause = showcase.querySelector("[data-pause]");
  const icon = pause.querySelector("use");
  const videos = slides.map((slide) => slide.querySelector("video"));
  const wide = matchMedia("(min-width: 721px)");
  let index = 0;

  videos.forEach((video, i) => video.addEventListener("playing", () => slides[i].classList.add("is-playing")));
  const playFromStart = (video) => {
    video.currentTime = 0;
    play(video);
  };

  const stopped = () => showcase.classList.contains("is-stopped");
  const setStopped = (stop) => {
    showcase.classList.toggle("is-stopped", stop);
    icon.setAttribute("href", icon.getAttribute("href").replace(/#.*/, stop ? "#play" : "#pause"));
    pause.setAttribute("aria-label", stop ? TEXT.showPlay : TEXT.showPause);
  };
  const show = (next) => {
    index = (next + slides.length) % slides.length;
    slides.forEach((slide, i) => {
      slide.classList.toggle("is-active", i === index);
      slide.inert = wide.matches && i !== index;
      if (!wide.matches) return;
      if (i === index && mayAutoplay()) playFromStart(videos[i]);
      else videos[i].pause();
    });
    picks.forEach((pick, i) => {
      pick.setAttribute("aria-selected", String(i === index));
      pick.tabIndex = i === index ? 0 : -1;
    });
  };

  picks.forEach((pick, i) => {
    pick.addEventListener("click", () => {
      setStopped(true);
      show(i);
    });
    pick.addEventListener("keydown", (event) => {
      const step = { ArrowRight: 1, ArrowLeft: -1 }[event.key];
      if (!step) return;
      event.preventDefault();
      setStopped(true);
      show(index + step);
      picks[index].focus();
    });
    pick.querySelector(".pick__bar").addEventListener("animationend", () => {
      if (!stopped()) show(index + 1);
    });
  });
  pause.addEventListener("click", () => {
    const stop = !stopped();
    setStopped(stop);
    if (stop) videos[index].pause();
    else play(videos[index]);
  });
  wide.addEventListener("change", () => show(index));
  watchVisibility(
    slides,
    (slide) => !wide.matches && mayAutoplay() && play(slide.querySelector("video")),
    (slide) => !wide.matches && slide.querySelector("video").pause(),
  );

  pause.hidden = !mayAutoplay();
  setStopped(!mayAutoplay());
  showcase.classList.add("is-ready");
  show(0);
}

function setUpHeader() {
  const header = document.querySelector(".site-header");
  if (!header) return;
  const update = () => header.classList.toggle("is-top", window.scrollY < 8);
  update();
  window.addEventListener("scroll", update, { passive: true });
}

setUpMail();
setUpHeader();
setUpShowcase();
setUpClips();
setUpLightbox();
