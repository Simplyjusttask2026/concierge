// Simply Just Task Concierge - embeddable chat widget
// Usage:
// <script src="https://cdn.jsdelivr.net/gh/Simplyjusttask2026/concierge@main/widget.js"
//   data-api="https://sjt-concierge.onrender.com/api/chat"
//   data-title="Simply Just Task Concierge"></script>
(function () {
  var script = document.currentScript;
  var API = script.getAttribute("data-api");
  var TITLE = script.getAttribute("data-title") || "Concierge";

  var css = document.createElement("style");
  css.textContent = [
    "#sjt-bubble{position:fixed;bottom:20px;right:20px;width:60px;height:60px;border-radius:50%;background:linear-gradient(135deg,#2dd4bf,#0d9488);color:#fff;font-size:28px;border:none;cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,.3);z-index:99999;display:flex;align-items:center;justify-content:center}",
    "#sjt-panel{position:fixed;bottom:90px;right:20px;width:340px;max-width:90vw;height:440px;background:#fff;border-radius:16px;box-shadow:0 8px 30px rgba(0,0,0,.25);display:none;flex-direction:column;overflow:hidden;z-index:99999;font-family:-apple-system,Segoe UI,Roboto,sans-serif}",
    "#sjt-panel.open{display:flex}",
    "#sjt-head{background:linear-gradient(135deg,#2dd4bf,#0d9488);color:#fff;padding:14px 16px;font-weight:600;font-size:15px}",
    "#sjt-msgs{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px;background:#f0fdfa}",
    ".sjt-msg{max-width:80%;padding:9px 12px;border-radius:14px;font-size:14px;line-height:1.4;white-space:pre-wrap}",
    ".sjt-bot{background:#ccfbf1;color:#222;align-self:flex-start;border-bottom-left-radius:4px}",
    ".sjt-user{background:#0d9488;color:#fff;align-self:flex-end;border-bottom-right-radius:4px}",
    ".sjt-typing{color:#888;font-style:italic}",
    "#sjt-form{display:flex;border-top:1px solid #eee}",
    "#sjt-input{flex:1;border:none;padding:12px;font-size:14px;outline:none}",
    "#sjt-send{border:none;background:#0d9488;color:#fff;padding:0 18px;font-size:16px;cursor:pointer}"
  ].join("\n");
  document.head.appendChild(css);

  var bubble = document.createElement("button");
  bubble.id = "sjt-bubble";
  bubble.textContent = "\u{1F4AC}";

  var panel = document.createElement("div");
  panel.id = "sjt-panel";
  panel.innerHTML =
    '<div id="sjt-head">' + TITLE + '</div>' +
    '<div id="sjt-msgs"></div>' +
    '<form id="sjt-form"><input id="sjt-input" placeholder="Type a message..." autocomplete="off"><button id="sjt-send" type="submit">\u27A4</button></form>';

  document.body.appendChild(bubble);
  document.body.appendChild(panel);

  var msgs = panel.querySelector("#sjt-msgs");
  var input = panel.querySelector("#sjt-input");
  var opened = false;

  function addMsg(text, cls) {
    var d = document.createElement("div");
    d.className = "sjt-msg " + cls;
    d.textContent = text;
    msgs.appendChild(d);
    msgs.scrollTop = msgs.scrollHeight;
    return d;
  }

  bubble.onclick = function () {
    panel.classList.toggle("open");
    if (!opened) {
      opened = true;
      addMsg("Hi! Welcome to Simply Just Task \u{1F44B} I'm your concierge. How can I help you today?", "sjt-bot");
    }
    input.focus();
  };

  panel.querySelector("#sjt-form").onsubmit = function (e) {
    e.preventDefault();
    var text = input.value.trim();
    if (!text) return;
    input.value = "";
    addMsg(text, "sjt-user");
    var typing = addMsg("typing...", "sjt-bot sjt-typing");
    fetch(API, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    })
      .then(function (r) { return r.json(); })
      .then(function (d) { typing.textContent = d.reply || "..."; typing.classList.remove("sjt-typing"); })
      .catch(function () { typing.textContent = "Hmm, connection trouble. Try again?"; typing.classList.remove("sjt-typing"); });
  };
})();
