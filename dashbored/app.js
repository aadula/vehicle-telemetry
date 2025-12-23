// ---------- WebSocket + Telemetry Client ----------

let socket = null;

let isRecording = false;
let isReplaying = false;
let recordedFrames = [];

let measuringZeroToSixty = false;
let zeroToSixtyStartTime = null;
let lastZeroToSixty = null;

const RECONNECT_DELAY_MS = 2000;

function connectSocket() {
  const host = window.location.hostname || "localhost";
  const url = `ws://${host}:8765`;
  console.log("Connecting to:", url);

  socket = new WebSocket(url);

  socket.onopen = () => {
    console.log("Connected to telemetry server");
    setStatus("Live");
  };

  socket.onerror = (err) => {
    console.error("WebSocket error:", err);
    setStatus("Error");
  };

  socket.onclose = () => {
    console.warn("WebSocket connection closed");
    if (!isReplaying) {
      setStatus("Disconnected (reconnecting…)");      
    }
    setTimeout(connectSocket, RECONNECT_DELAY_MS);
  };

  socket.onmessage = (event) => {
    if (isReplaying) {
      // ignore live data while replaying
      return;
    }

    const data = JSON.parse(event.data);
    renderData(data);

    if (isRecording) {
      recordedFrames.push({
        timestamp: Date.now(),
        data: data,
      });
    }
  };
}

connectSocket();

// ---------- Rendering & Derived Metrics ----------

function clamp(val, min, max) {
  return Math.min(Math.max(val, min), max);
}

function computeDerivedMetrics(data) {
  const rpm = Number(data.rpm) || 0;
  const speed = Number(data.speed) || 0;
  const boost = Number(data.boost) || 0;
  const coolant = Number(data.coolant) || 0;
  const oil = Number(data.oil) || 0;

  // Simple pseudo N54-style boost target (for simulation)
  let boostTarget;
  if (rpm < 1500) boostTarget = 3;
  else if (rpm < 2500) boostTarget = 8;
  else if (rpm < 3500) boostTarget = 12;
  else boostTarget = 15;

  // Boost actual is just whatever we read
  const boostActual = boost;

  // Rough torque estimate based on boost
  let tqBase = 220 + boost * 10; // 0 psi ~220, 15 psi ~370
  const tq = clamp(tqBase, 150, 600);

  // HP estimate from torque and RPM
  let hp = (tq * rpm) / 5252;
  hp = clamp(hp, 0, 700);

  // IAT ~ coolant - offset (very rough)
  let iat = coolant - 20;
  iat = clamp(iat, 5, 120);

  // Transmission temp ~ follows coolant, higher at speed
  let trans = coolant - 5;
  if (speed > 20) trans = coolant + 5;
  if (speed > 60) trans = coolant + 10;
  trans = clamp(trans, 40, 140);

  // Timing corrections per cylinder
  const timingCorrections = [];
  for (let i = 0; i < 6; i++) {
    let val = 0;
    if (boost > 8) {
      // random small negative correction when under boost
      val = -Number((Math.random() * 3).toFixed(1));
    }
    timingCorrections.push(val);
  }
  const boostError = boostTarget - boostActual;

  return {
    boost_target: boostTarget,
    boost_actual: boostActual,
    boost_error: boostError,
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

  // Default when not really moving / boosting
  if (speed < 5 || rpm < 1500) {
    return "No boost (cruise/idle)";
  }
  // Underboost / slow spool
  if (error > 4) {
    return "Underboost / check leaks";
  }
  // Mild underboost
  if (error > 2) {
    return "Slight underboost";
  }
  // Overboost (danger for turbos / rods)
  if (error < -3) {
    return "Overboost / WG issue";
  }
  // Within +/- ~2 psi -> good
  return "Healthy";
}


function renderData(data) {
  // base telemetry values
  setNumeric("rpm", data.rpm, 0);
  setNumeric("speed", data.speed, 0);
  setNumeric("coolant", data.coolant, 1);
  setNumeric("oil", data.oil, 1);
  setNumeric("boost", data.boost, 1);
  setNumeric("voltage", data.voltage, 2);

  // mode indicator
  if (data.source) {
    const modeEl = document.getElementById("mode-indicator");
    if (modeEl) {
      modeEl.textContent = "Mode: " + data.source.toUpperCase();
    }
  }

  // derived metrics
  const derived = computeDerivedMetrics(data);

  setNumeric("boost_target", derived.boost_target, 1);
  setNumeric("boost_actual", derived.boost_actual, 1);
  setNumeric("boost_error", derived.boost_error, 1);
  setNumeric("hp", derived.hp, 0);
  setNumeric("tq", derived.tq, 0);
  setNumeric("iat", derived.iat, 1);
  setNumeric("trans_temp", derived.trans_temp, 1);
  
    const turboStatus = computeTurboHealth(derived, data);
  const turboEl = document.getElementById("turbo_health");
  if (turboEl) {
    turboEl.textContent = turboStatus;
    // red if not healthy
    if (turboStatus.includes("Underboost") || turboStatus.includes("Overboost")) {
      turboEl.style.color = "red";
    } else {
      turboEl.style.color = "#e5e7eb";
    }
  }
  const timingEl = document.getElementById("timing_corrections");
  if (timingEl && Array.isArray(derived.timing_corrections)) {
    timingEl.textContent = derived.timing_corrections
      .map((v) => v.toFixed(1))
      .join(", ");
  }

  applyAlerts(data, derived);
  updateZeroToSixty(data);
}

function setNumeric(id, value, decimals) {
  const el = document.getElementById(id);
  if (!el) return;

  const num = Number(value);
  if (isNaN(num)) {
    el.textContent = "--";
    el.style.color = "#e5e7eb";
    return;
  }

  el.textContent = num.toFixed(decimals);
  el.style.color = "#e5e7eb";
}

// ---------- Alerts ----------

function applyAlerts(data, derived) {
  const coolant = Number(data.coolant) || 0;
  const oil = Number(data.oil) || 0;
  const boost = Number(data.boost) || 0;
  const voltage = Number(data.voltage) || 0;
   const boostError = derived.boost_error || 0;

  if (coolant > 110) highlight("coolant");
  if (oil > 125) highlight("oil");
  if (boost > 17) highlight("boost");
  if (voltage < 12.2) highlight("voltage");
 if (Math.abs(boostError) > 5) {
    highlight("boost_error");
  }
  // Large timing corrections
  const timing = derived.timing_corrections || [];
  if (timing.some((v) => v < -3)) {
    const el = document.getElementById("timing_corrections");
    if (el) el.style.color = "red";
  }
}

function highlight(id) {
  const el = document.getElementById(id);
  if (el) {
    el.style.color = "red";
  }
}

// ---------- 0–60 mph estimator ----------

function updateZeroToSixty(data) {
  const speedMph = Number(data.speed) || 0;

  // reset when basically stopped
  if (speedMph < 1) {
    measuringZeroToSixty = false;
    zeroToSixtyStartTime = null;
    return;
  }

  // start measuring when we roll off from ~0
  if (!measuringZeroToSixty && speedMph >= 1 && speedMph < 5) {
    measuringZeroToSixty = true;
    zeroToSixtyStartTime = performance.now();
    lastZeroToSixty = null;
  }

  // complete measurement when we hit 60+
  if (measuringZeroToSixty && speedMph >= 60) {
    const elapsedMs = performance.now() - zeroToSixtyStartTime;
    lastZeroToSixty = elapsedMs / 1000.0;
    measuringZeroToSixty = false;
  }

  const el = document.getElementById("zeroToSixty");
  if (el) {
    if (lastZeroToSixty != null) {
      el.textContent = lastZeroToSixty.toFixed(2);
    } else {
      el.textContent = "--";
    }
  }
}

// ---------- Recording / Replay ----------

const recordBtn = document.getElementById("record-btn");
const stopBtn = document.getElementById("stop-btn");
const replayBtn = document.getElementById("replay-btn");
const statusEl = document.getElementById("session-status");

if (recordBtn) {
  recordBtn.addEventListener("click", () => {
    if (isReplaying) return;
    recordedFrames = [];
    isRecording = true;
    setStatus("Recording");
  });
}

if (stopBtn) {
  stopBtn.addEventListener("click", () => {
    if (!isRecording) return;
    isRecording = false;
    setStatus("Live (recording stopped)");
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

function setStatus(text) {
  if (statusEl) {
    statusEl.textContent = "Status: " + text;
  }
}

function replaySession() {
  isReplaying = true;
  setStatus("Replaying (live data paused)");

  const frames = [...recordedFrames];
  let index = 0;
  const intervalMs = 50; // ~20 Hz

  const timer = setInterval(() => {
    if (index >= frames.length) {
      clearInterval(timer);
      isReplaying = false;
      setStatus("Live (replay finished)");
      return;
    }

    const frame = frames[index];
    renderData(frame.data);
    index += 1;
  }, intervalMs);
}

// ---------- PWA: Service Worker Registration ----------

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
