"use strict";

const $ = (sel) => document.querySelector(sel);
const KEY_STORE = "stoop_keeper_key";

function getKey() {
  return $("#key").value.trim();
}

function authHeaders() {
  // The key goes only to this box, in a header, over the local link. Never stored
  // server-side; only here, in this browser session, if you ask it to be.
  return { "Content-Type": "application/json", "X-Keeper-Key": getKey() };
}

function rememberMaybe() {
  if ($("#remember").checked && getKey()) sessionStorage.setItem(KEY_STORE, getKey());
  else sessionStorage.removeItem(KEY_STORE);
}

function fillSelect(sel, names, current) {
  sel.innerHTML = "";
  for (const name of names) {
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = name;
    if (name === current) opt.selected = true;
    sel.appendChild(opt);
  }
}

async function loadOptions() {
  const data = await (await fetch("/admin/options")).json();
  fillSelect($("#theme"), data.themes, data.current.theme);
  fillSelect($("#skin"), data.skins, data.current.skin);
  $("#prompt").value = data.current.prompt || "";
}

async function loadEntries() {
  const { entries } = await (await fetch("/entries")).json();
  const wrap = $("#admin-entries");
  wrap.innerHTML = "";
  if (!entries.length) {
    wrap.textContent = "nothing on the stoop right now.";
    return;
  }
  for (const e of entries) {
    const card = document.createElement("article");
    card.className = "entry";

    const body = document.createElement("p");
    body.className = "body";
    body.textContent = e.text; // untrusted — textContent only

    const meta = document.createElement("div");
    meta.className = "meta";
    const when = document.createElement("span");
    when.textContent = new Date(e.ts * 1000).toLocaleString() + (e.seconds ? ` · kept ${e.seconds}×` : "");
    const rm = document.createElement("button");
    rm.className = "keep";
    rm.type = "button";
    rm.textContent = "remove";
    rm.addEventListener("click", () => removeEntry(e.id));
    meta.append(when, rm);

    card.append(body, meta);
    wrap.appendChild(card);
  }
}

function badKey(msgEl) {
  msgEl.textContent = "that key didn't open the box.";
}

async function saveSettings() {
  const body = JSON.stringify({
    theme: $("#theme").value,
    skin: $("#skin").value,
    prompt: $("#prompt").value,
  });
  const res = await fetch("/admin/settings", { method: "POST", headers: authHeaders(), body });
  const msg = $("#save-msg");
  if (res.ok) {
    rememberMaybe();
    msg.textContent = "saved. the box is wearing it now.";
  } else if (res.status === 403) {
    badKey(msg);
  } else {
    const err = await res.json().catch(() => ({}));
    msg.textContent = "hmm — " + (err.error || "couldn't save");
  }
}

async function removeEntry(id) {
  const res = await fetch("/admin/remove", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ id }),
  });
  if (res.ok) {
    rememberMaybe();
    await loadEntries();
  } else if (res.status === 403) {
    badKey($("#save-msg"));
  }
}

window.addEventListener("DOMContentLoaded", () => {
  const saved = sessionStorage.getItem(KEY_STORE);
  if (saved) {
    $("#key").value = saved;
    $("#remember").checked = true;
  }
  $("#save").addEventListener("click", saveSettings);
  loadOptions();
  loadEntries();
});
