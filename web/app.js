"use strict";

const $ = (sel) => document.querySelector(sel);
const MAX = 280;

function ago(ts) {
  const s = Math.max(0, Math.floor(Date.now() / 1000 - ts));
  if (s < 60) return "just now";
  const m = Math.floor(s / 60);
  if (m < 60) return m + "m ago";
  const h = Math.floor(m / 60);
  if (h < 24) return h + "h ago";
  return Math.floor(h / 24) + "d ago";
}

function render(data) {
  $("#prompt").textContent = data.prompt;
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
  if (res.ok) await load();
}

async function load() {
  const res = await fetch("/entries");
  render(await res.json());
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
    await load();
  } else {
    const err = await res.json().catch(() => ({}));
    msg.textContent = err.error ? "hmm — " + err.error : "something went wrong.";
  }
}

window.addEventListener("DOMContentLoaded", () => {
  $("#text").addEventListener("input", updateCount);
  $("#leave").addEventListener("submit", leave);
  updateCount();
  load();
});
