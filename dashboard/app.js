let socket = null;

let isRecording = false;
let isReplaying = false;
let recordedFrames = [];

let measuringZeroToSixty = false;
let zeroToSixtyStartTime = null;
let lastZeroToSixty = null;

const RECONNECT_DELAY_MS = 2000;
const SAFE_TEXT_COLOR = "#e7edf5";

const recordBtn = document.getElementById("record-btn");
const stopBtn = document.getElementById("stop-btn");
const replayBtn = document.getElementById("replay-btn");
const sessionStatusEl = document.getElementById("session-status");
const connectionStatusEl = document.getElementById("connection-status");
const connectionChipEl = document.getElementById("connection-chip");
const sourceIndicatorEl = document.getElementById("source-indicator");
const alertListEl = document.getElementById("alert-list");

function connectSocket() {
  const host = window.location.hostname || "localhost";
  const url = `ws://${host}:8765`;
  console.log("Connecting to:", url);

  setConnectionState("Disconnected");
  socket = new WebSocket(url);

  socket.onopen = () => {
    console.log("Connected to telemetry server");
    setConnectionState("Connected");
    if (!isReplaying) {
      setSessionStatus("Live");
    }
  };

  socket.onerror = (err) => {
    console.error("WebSocket error:", err);
    setConnectionState("Disconnected");
    if (!isReplaying) {
      setSessionStatus("Connection Error");
    }
  };

  socket.onclose = () => {
    console.warn("WebSocket connection closed");
    setConnectionState("Disconnected");
    if (!isReplaying) {
      setSessionStatus("Disconnected");
    }
    window.setTimeout(connectSocket, RECONNECT_DELAY_MS);
  };

  socket.onmessage = (event) => {
    if (isReplaying) {
      return;
    }

    const data = JSON.parse(event.data);
    renderData(data);

    if (isRecording) {
      recordedFrames.push({
        timestamp: Date.now(),
        data,
      });
    }
  };
}

function clamp(val, min, max) {
  return Math.min(Math.max(val, min), max);
}

function computeDerivedMetrics(data) {
  const rpm = Number(data.rpm) || 0;
  const speed = Number(data.speed) || 0;
  const boost = Number(data.boost) || 0;
  const coolant = Number(data.coolant) || 0;

  let boostTarget;
  if (rpm < 1500) boostTarget = 3;
  else if (rpm < 2500) boostTarget = 8;
  else if (rpm < 3500) boostTarget = 12;
  else boostTarget = 15;

  const boostActual = boost;
  const tq = clamp(220 + boost * 10, 150, 600);
  const hp = clamp((tq * rpm) / 5252, 0, 700);
  const iat = clamp(coolant - 20, 5, 120);

  let trans = coolant - 5;
  if (speed > 20) trans = coolant + 5;
  if (speed > 60) trans = coolant + 10;
  trans = clamp(trans, 40, 140);

  const timingCorrections = [];
  for (let i = 0; i < 6; i += 1) {
    let value = 0;
    if (boost > 8) {
      value = -Number((Math.random() * 3).toFixed(1));
    }
    timingCorrections.push(value);
  }

  return {
    boost_target: boostTarget,
    boost_actual: boostActual,
    boost_error: boostTarget - boostActual,
    hp,
    tq,
    iat,
    trans_temp: trans,
    timing_corrections: timingCorrections,
  };
}

function computeTurboHealth(derived, data) {
  const error = derived.boost_error || 0;
  const rpm = Number(data.rpm) || 0;
  const speed = Number(data.speed) || 0;

  if (speed < 5 || rpm < 1500) return "No boost (cruise/idle)";
  if (error > 4) return "Underboost / check leaks";
  if (error > 2) return "Slight underboost";
  if (error < -3) return "Overboost / WG issue";
  return "Healthy";
}

function renderData(data) {
  clearAlertStates();

  setNumeric("rpm", data.rpm, 0);
  setNumeric("speed", data.speed, 0);
  setNumeric("coolant", data.coolant, 1);
  setNumeric("oil", data.oil, 1);
  setNumeric("boost", data.boost, 1);
  setNumeric("voltage", data.voltage, 2);

  updateSourceIndicator(data);

  const derived = computeDerivedMetrics(data);
  setNumeric("boost_target", derived.boost_target, 1);
  setNumeric("boost_actual", derived.boost_actual, 1);
  setNumeric("boost_error", derived.boost_error, 1);
  setNumeric("hp", derived.hp, 0);
  setNumeric("tq", derived.tq, 0);
  setNumeric("iat", derived.iat, 1);
  setNumeric("trans_temp", derived.trans_temp, 1);

  const turboStatus = computeTurboHealth(derived, data);
  setTextValue("turbo_health", turboStatus);

  const timingText = Array.isArray(derived.timing_corrections)
    ? derived.timing_corrections.map((value) => value.toFixed(1)).join(", ")
    : "--";
  setTextValue("timing_corrections", timingText);

  const alerts = buildAlertMessages(data, derived, turboStatus);
  renderAlertList(alerts);
  applyAlerts(data, derived, turboStatus);
  updateZeroToSixty(data);
}

function setNumeric(id, value, decimals) {
  const el = document.getElementById(id);
  if (!el) return;

  const num = Number(value);
  if (Number.isNaN(num)) {
    el.textContent = "--";
    el.style.color = SAFE_TEXT_COLOR;
    return;
  }

  el.textContent = num.toFixed(decimals);
  el.style.color = SAFE_TEXT_COLOR;
}

function setTextValue(id, value) {
  const el = document.getElementById(id);
  if (!el) return;

  el.textContent = value || "--";
  el.style.color = SAFE_TEXT_COLOR;
}

function setConnectionState(state) {
  if (connectionStatusEl) {
    connectionStatusEl.textContent = state;
  }

  if (!connectionChipEl) return;

  connectionChipEl.classList.remove("is-connected", "is-disconnected");
  if (state === "Connected") {
    connectionChipEl.classList.add("is-connected");
  } else {
    connectionChipEl.classList.add("is-disconnected");
  }
}

function setSessionStatus(text) {
  if (sessionStatusEl) {
    sessionStatusEl.textContent = text;
  }
}

function updateSourceIndicator(data) {
  if (!sourceIndicatorEl) return;

  const source = (data.mode || data.source || "--").toString().toUpperCase();
  sourceIndicatorEl.textContent = source;
}

function clearAlertStates() {
  document.querySelectorAll(".metric-card.is-alert").forEach((card) => {
    card.classList.remove("is-alert");
  });
}

function highlight(metricId) {
  const card = document.querySelector(`[data-metric-card="${metricId}"]`);
  if (card) {
    card.classList.add("is-alert");
  }
}

function applyAlerts(data, derived, turboStatus) {
  const backendAlerts = data.alerts || {};
  const coolant = Number(data.coolant) || 0;
  const oil = Number(data.oil) || 0;
  const rpm = Number(data.rpm) || 0;
  const boost = Number(data.boost) || 0;
  const voltage = Number(data.voltage) || 0;
  const boostError = Math.abs(derived.boost_error || 0);
  const timing = derived.timing_corrections || [];

  if (backendAlerts.coolant_high || coolant > 105) highlight("coolant");
  if (backendAlerts.oil_high || oil > 115) highlight("oil");
  if (backendAlerts.rpm_high || rpm > 6500) highlight("rpm");
  if (backendAlerts.boost_high || boost > 18) highlight("boost");
  if (backendAlerts.voltage_low || voltage < 12.2) highlight("voltage");
  if (boostError > 5) highlight("boost_error");
  if (turboStatus.includes("Underboost") || turboStatus.includes("Overboost")) {
    highlight("turbo_health");
  }
  if (timing.some((value) => value < -3)) {
    highlight("timing_corrections");
  }
}

function buildAlertMessages(data, derived, turboStatus) {
  const items = [];
  const backendAlerts = data.alerts || {};
  const coolant = Number(data.coolant) || 0;
  const oil = Number(data.oil) || 0;
  const rpm = Number(data.rpm) || 0;
  const boost = Number(data.boost) || 0;
  const voltage = Number(data.voltage) || 0;
  const boostError = derived.boost_error || 0;

  if (Array.isArray(backendAlerts.active) && backendAlerts.active.length > 0) {
    backendAlerts.active.forEach((alert) => {
      items.push({
        level: alert.level || "warn",
        text: alert.message || "Telemetry warning",
      });
    });
  }

  if (data.status && data.status !== "ok") {
    items.push({ level: "warn", text: `Source status: ${String(data.status).replace(/_/g, " ")}.` });
  }

  if (!Array.isArray(backendAlerts.active) || backendAlerts.active.length === 0) {
    if (coolant > 105) {
      items.push({ level: "danger", text: "Overheating warning" });
    }
    if (oil > 115) {
      items.push({ level: "danger", text: "Oil temperature warning" });
    }
    if (voltage < 12.2) {
      items.push({ level: "warn", text: "Low voltage warning" });
    }
    if (boost > 18) {
      items.push({ level: "danger", text: "Overboost warning" });
    }
    if (rpm > 6500) {
      items.push({ level: "warn", text: "High RPM warning" });
    }
  }

  if (Math.abs(boostError) > 5 && items.length === 0) {
    items.push({ level: "warn", text: `Boost error is ${boostError.toFixed(1)} psi.` });
  }
  if ((turboStatus.includes("Underboost") || turboStatus.includes("Overboost")) && items.length === 0) {
    items.push({ level: "warn", text: `Turbo health flag: ${turboStatus}.` });
  }

  if (items.length === 0) {
    items.push({ level: "clear", text: "Systems normal." });
  }

  return items;
}

function renderAlertList(items) {
  if (!alertListEl) return;

  alertListEl.innerHTML = "";

  items.forEach((item) => {
    const li = document.createElement("li");
    li.className = `alert-item ${item.level === "danger" ? "is-danger" : ""} ${item.level === "clear" ? "is-clear" : ""}`.trim();
    li.textContent = item.text;
    alertListEl.appendChild(li);
  });
}

function updateZeroToSixty(data) {
  const speedMph = Number(data.speed) || 0;

  if (speedMph < 1) {
    measuringZeroToSixty = false;
    zeroToSixtyStartTime = null;
    return;
  }

  if (!measuringZeroToSixty && speedMph >= 1 && speedMph < 5) {
    measuringZeroToSixty = true;
    zeroToSixtyStartTime = performance.now();
    lastZeroToSixty = null;
  }

  if (measuringZeroToSixty && speedMph >= 60) {
    const elapsedMs = performance.now() - zeroToSixtyStartTime;
    lastZeroToSixty = elapsedMs / 1000.0;
    measuringZeroToSixty = false;
  }

  const el = document.getElementById("zeroToSixty");
  if (!el) return;

  el.textContent = lastZeroToSixty != null ? lastZeroToSixty.toFixed(2) : "--";
}

function replaySession() {
  isReplaying = true;
  setSessionStatus("Replay");

  const frames = [...recordedFrames];
  let index = 0;
  const intervalMs = 50;

  const timer = window.setInterval(() => {
    if (index >= frames.length) {
      window.clearInterval(timer);
      isReplaying = false;
      setSessionStatus("Live");
      return;
    }

    renderData(frames[index].data);
    index += 1;
  }, intervalMs);
}

if (recordBtn) {
  recordBtn.addEventListener("click", () => {
    if (isReplaying) return;
    recordedFrames = [];
    isRecording = true;
    setSessionStatus("Recording");
  });
}

if (stopBtn) {
  stopBtn.addEventListener("click", () => {
    if (!isRecording) return;
    isRecording = false;
    setSessionStatus("Live");
  });
}

if (replayBtn) {
  replayBtn.addEventListener("click", () => {
    if (isRecording || isReplaying) return;
    if (recordedFrames.length === 0) {
      alert("No recorded data to replay.");
      return;
    }
    replaySession();
  });
}

connectSocket();

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("./sw.js")
      .then((reg) => {
        console.log("Service worker registered:", reg.scope);
      })
      .catch((err) => {
        console.error("Service worker registration failed:", err);
      });
  });
}
