"use strict";

const $ = (id) => document.getElementById(id);
const labels = {
  door_knock: ["Door knock", "KNOCK"],
  alarm_beep: ["Alarm or timer beep", "BEEP"],
  dog_bark: ["Dog bark", "BARK"],
  attention_call: ["Call for attention", "CALL"],
};
let currentEvent = null;
let toastTimer = null;

function humanize(value) {
  return labels[value]?.[0] || value?.replaceAll("_", " ") || "No confirmed event";
}

function showToast(message) {
  const toast = $("toast");
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 2600);
}

async function request(path, options = {}) {
  const response = await fetch(path, options);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || `Request failed: ${response.status}`);
  return payload;
}

function updateStatus(status) {
  const online = status.connection === "connected";
  $("connection-badge").textContent = online ? "Pod connected" : "Pod offline";
  $("connection-badge").className = `badge ${online ? "online" : "offline"}`;
  $("health-dot").className = `health-dot ${online ? "online" : ""}`;
  $("location").textContent = status.location;
  $("mode-badge").textContent = status.input_mode === "physical" ? "Physical input" : `${status.input_mode.replace("-", " ")} input`;
  $("mode-badge").className = `badge ${status.input_mode === "physical" ? "online" : "simulated"}`;

  const decision = status.decision;
  const event = status.current_event;
  currentEvent = event;
  const confidence = Math.round((event?.confidence ?? decision.confidence ?? 0) * 100);
  const candidate = event?.class_name || decision.candidate;
  const active = decision.state === "alerting" && event?.user_action === "pending";
  $("cue-orbit").className = `cue-orbit ${active ? "alerting" : "idle"}`;
  $("cue-symbol").textContent = active ? labels[candidate]?.[1] || "CUE" : "···";
  $("decision-state").textContent = {
    idle: "Listening locally",
    observing: "New evidence observed",
    confirming: `Confirming across ${decision.evidence_windows} windows`,
    alerting: event?.user_action === "pending" ? "Confirmed cue" : event?.user_action,
    cooldown: "Cooldown · duplicate cue suppressed",
    muted: `Muted · ${decision.muted_seconds_remaining}s remaining`,
  }[decision.state] || decision.state;
  $("cue-title").textContent = active ? humanize(candidate) : decision.candidate ? `Checking ${humanize(decision.candidate)}` : "No confirmed event";
  $("cue-detail").textContent = active
    ? `Confirmed from ${event.evidence_windows} model windows at priority ${event.priority}. Raw audio was discarded.`
    : "Ambiguous sounds stay in a confirmation window instead of interrupting immediately.";
  $("confidence-text").textContent = `${confidence}%`;
  $("confidence-meter").style.width = `${confidence}%`;
  $("confidence-meter").parentElement.setAttribute("aria-valuenow", confidence);
  $("detected-time").textContent = event ? new Date(event.detected_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }) : "Waiting for evidence";
  $("acknowledge").disabled = !active;
  $("dismiss").disabled = !active;

  const d = status.diagnostics;
  $("packet-loss").textContent = `${(d.loss_rate * 100).toFixed(1)}%`;
  $("jitter").textContent = `${d.jitter_ms.toFixed(1)} ms`;
  $("inference").textContent = d.inference_ms == null ? "—" : `${d.inference_ms.toFixed(1)} ms`;
  $("battery").textContent = status.battery_mv == null ? "—" : `${(status.battery_mv / 1000).toFixed(2)} V`;
  $("pod-id").textContent = status.pod_id == null ? "—" : `0x${status.pod_id.toString(16).toUpperCase()}`;
  $("frames-received").textContent = d.datagrams_received.toLocaleString();
  $("frames-missing").textContent = d.missing_frames.toLocaleString();
  $("rssi").textContent = status.rssi_dbm == null ? "—" : `${status.rssi_dbm} dBm`;
  $("model").textContent = d.model;
}

function updateHistory(events) {
  const history = $("history");
  if (!events.length) {
    history.innerHTML = '<p class="empty">No confirmed events yet.</p>';
    return;
  }
  history.replaceChildren(...events.map((event) => {
    const card = document.createElement("article");
    card.className = "history-item";
    const title = document.createElement("strong");
    title.textContent = humanize(event.class_name);
    const time = document.createElement("p");
    time.textContent = `${new Date(event.detected_at).toLocaleString()} · ${Math.round(event.confidence * 100)}% confidence`;
    const detail = document.createElement("p");
    detail.textContent = `${event.location} · ${event.evidence_tier} · ${event.user_action}`;
    card.append(title, time, detail);
    return card;
  }));
}

async function refresh() {
  try {
    const [status, history] = await Promise.all([
      request("/api/status"),
      request("/api/events?limit=12"),
    ]);
    updateStatus(status);
    updateHistory(history.events);
  } catch (error) {
    $("connection-badge").textContent = "Service offline";
    $("connection-badge").className = "badge offline";
  }
}

async function loadConfig() {
  const config = await request("/api/config");
  const root = $("class-controls");
  root.replaceChildren(...Object.entries(config.classes).map(([label, policy]) => {
    const row = document.createElement("label");
    row.className = "class-row";
    const input = document.createElement("input");
    input.type = "checkbox";
    input.checked = policy.enabled;
    input.addEventListener("change", async () => {
      try {
        await request(`/api/config/${label}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ enabled: input.checked }),
        });
        showToast(`${humanize(label)} ${input.checked ? "enabled" : "disabled"}`);
      } catch (error) {
        input.checked = !input.checked;
        showToast(error.message);
      }
    });
    const name = document.createElement("span");
    name.className = "class-name";
    name.textContent = humanize(label);
    const priority = document.createElement("span");
    priority.className = "priority";
    priority.textContent = `Priority ${policy.priority}`;
    row.append(input, name, priority);
    return row;
  }));
}

async function eventAction(action) {
  if (!currentEvent) return;
  try {
    await request(`/api/events/${currentEvent.id}/${action}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    showToast(action === "acknowledge" ? "Cue acknowledged" : "Cue dismissed and saved as feedback");
    await refresh();
  } catch (error) { showToast(error.message); }
}

$("acknowledge").addEventListener("click", () => eventAction("acknowledge"));
$("dismiss").addEventListener("click", () => eventAction("dismiss"));
$("mute").addEventListener("click", async () => {
  try {
    await request("/api/mute", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ seconds: 300 }) });
    showToast("Cues muted for 5 minutes");
    await refresh();
  } catch (error) { showToast(error.message); }
});
$("clear-history").addEventListener("click", async () => {
  if (!window.confirm("Clear local event metadata and feedback? Raw audio is never stored.")) return;
  try {
    await request("/api/history/clear", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ confirm: true }) });
    showToast("Local history cleared");
    await refresh();
  } catch (error) { showToast(error.message); }
});

loadConfig().catch((error) => showToast(error.message));
refresh();
setInterval(refresh, 700);
