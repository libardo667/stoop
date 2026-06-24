"use strict";

const $ = (sel) => document.querySelector(sel);
const MAX = 280;

// --- time formatting ---

function formatDuration(seconds) {
  const s = Math.max(0, Math.floor(seconds));
  if (s < 60) return "just now";
  const m = Math.floor(s / 60);
  if (m < 60) return m + "m ago";
  const h = Math.floor(m / 60);
  if (h < 24) return h + "h ago";
  return Math.floor(h / 24) + "d ago";
}

function ago(ts) {
  return formatDuration(Date.now() / 1000 - ts);
}

function formatSpan(seconds) {
  const s = Math.max(0, Math.floor(seconds));
  if (s < 60) return "moments";
  const m = Math.floor(s / 60);
  if (m < 60) return m + (m === 1 ? " minute" : " minutes");
  const h = Math.floor(m / 60);
  if (h < 24) return h + (h === 1 ? " hour" : " hours");
  const d = Math.floor(h / 24);
  return d + (d === 1 ? " day" : " days");
}

// --- theme (the prompt makes the box) ---

let THEME = {
  noun_singular: "story",
  noun_plural: "stories",
};

async function applyConfig() {
  const res = await fetch("/config");
  THEME = await res.json();
  document.title = THEME.title;
  $("#title").textContent = THEME.title;
  $("#prompt").textContent = THEME.prompt;
  $("#text").placeholder = THEME.placeholder;
  $("#leave-btn").textContent = THEME.leave_label;
  $("#nudge").textContent = THEME.nudge;
  $("#hint-exchange").textContent = THEME.hint_exchange;
  $("#hint-murmur").textContent = THEME.hint_murmur;
  $("#tab-exchange").textContent = THEME.tab_exchange;
  $("#tab-murmur").textContent = THEME.tab_murmur;
  $("#footer").textContent = THEME.footer;
  document.body.dataset.skin = THEME.skin; // CSS keys the look off this
}

// --- the exchange ---

function renderEntries(data) {
  const wrap = $("#entries");
  wrap.innerHTML = "";

  if (!data.entries.length) {
    const p = document.createElement("p");
    p.className = "empty";
    p.textContent = "The stoop is empty. Be the first to leave something.";
    wrap.appendChild(p);
    return;
  }

  for (const e of data.entries) {
    const card = document.createElement("article");
    card.className = "entry";

    const body = document.createElement("p");
    body.className = "body";
    body.textContent = e.text; // textContent, never innerHTML — entries are untrusted

    const meta = document.createElement("div");
    meta.className = "meta";
    const when = document.createElement("span");
    when.textContent = ago(e.ts);
    const keep = document.createElement("button");
    keep.className = "keep";
    keep.type = "button";
    keep.textContent = e.seconds ? "kept · " + e.seconds : "keep";
    keep.title = "buy this one more life on the stoop";
    keep.addEventListener("click", () => second(e.id));
    meta.append(when, keep);

    card.append(body, meta);
    wrap.appendChild(card);
  }
}

async function second(id) {
  const res = await fetch("/second", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id }),
  });
  if (res.ok) await loadExchange();
}

async function loadExchange() {
  const res = await fetch("/entries");
  renderEntries(await res.json());
}

function updateCount() {
  $("#count").textContent = $("#text").value.length + "/" + MAX;
}

async function leave(ev) {
  ev.preventDefault();
  const ta = $("#text");
  const msg = $("#msg");
  const text = ta.value.trim();
  if (!text) {
    msg.textContent = "say something first :)";
    return;
  }
  const res = await fetch("/entries", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (res.ok) {
    ta.value = "";
    updateCount();
    msg.textContent = "left on the stoop. thanks for feeding the block ✨";
    $("#nudge").textContent = "the block thanks you.";
    await loadExchange();
  } else {
    const err = await res.json().catch(() => ({}));
    msg.textContent = err.error ? "hmm — " + err.error : "something went wrong.";
  }
}

// --- the murmur ---

function murmurHeadline(d) {
  if (!d.count) return "The stoop is empty. Be the first to leave something.";
  let mood;
  if (d.newest_age < 3600) mood = "The block is lively";
  else if (d.newest_age < 86400) mood = "The block is stirring";
  else mood = "The block is quiet";
  const n = d.count === 1 ? "one " + THEME.noun_singular : d.count + " " + THEME.noun_plural;
  return `${mood} — ${n} on the stoop, the newest left ${formatDuration(d.newest_age)}.`;
}

function renderMurmur(d) {
  const el = $("#murmur");
  el.innerHTML = "";

  const headline = document.createElement("p");
  headline.className = "murmur-headline";
  headline.textContent = murmurHeadline(d);
  el.appendChild(headline);

  if (d.threads && d.threads.length) {
    const p = document.createElement("p");
    p.className = "murmur-threads";
    const label = document.createElement("span");
    label.className = "murmur-label";
    label.textContent = "on the block's mind: ";
    p.appendChild(label);
    p.appendChild(document.createTextNode(d.threads.map((t) => t[0]).join(" · ")));
    el.appendChild(p);
  }

  if (d.holding) {
    const p = document.createElement("p");
    p.className = "murmur-holding";
    const label = document.createElement("span");
    label.className = "murmur-label";
    label.textContent = "the block is holding onto: ";
    const quote = document.createElement("em");
    quote.textContent = "“" + d.holding.text + "”"; // textContent — untrusted
    const kept = document.createElement("span");
    kept.className = "murmur-keep";
    kept.textContent = ` · kept ${d.holding.seconds}×`;
    p.append(label, quote, kept);
    el.appendChild(p);
  }

  if (d.oldest_age != null) {
    const p = document.createElement("p");
    p.className = "murmur-since";
    p.textContent = `Something has rested here for ${formatSpan(d.oldest_age)}.`;
    el.appendChild(p);
  }
}

async function loadMurmur() {
  const res = await fetch("/murmur");
  renderMurmur(await res.json());
}

// --- tabs ---

function showView(name) {
  document.querySelectorAll(".view").forEach((v) => {
    v.hidden = v.id !== "view-" + name;
  });
  document.querySelectorAll(".tab").forEach((t) => {
    t.classList.toggle("is-active", t.dataset.view === name);
  });
  if (name === "murmur") loadMurmur();
  else loadExchange();
}

window.addEventListener("DOMContentLoaded", async () => {
  $("#text").addEventListener("input", updateCount);
  $("#leave").addEventListener("submit", leave);
  document.querySelectorAll(".tab").forEach((t) => {
    t.addEventListener("click", () => showView(t.dataset.view));
  });
  updateCount();
  await applyConfig(); // dress the box before showing it
  loadExchange();
});
