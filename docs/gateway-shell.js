/* gateway-shell.js — Non-redirecting 5G Permanent Mobile PWA Shell */
(function () {
  const RAW_GW = "https://raw.githubusercontent.com/neon0104/hyperliquid-vault-analyzer/main/docs/gateway.json";
  const LOCAL_GW = "../gateway.json";
  const REPO_PREFIX = "/hyperliquid-vault-analyzer";

  let tunnelBase = "";
  let currentRoute = window.__GW_DEFAULT_ROUTE || "/live";

  function b64ToBytes(b64) {
    const bin = atob(b64.replace(/-/g, "+").replace(/_/g, "/"));
    const arr = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
    return arr;
  }

  async function decryptPayload(gwObj, secretKey) {
    const enc = new TextEncoder();
    const keyHash = await crypto.subtle.digest("SHA-256", enc.encode(secretKey));
    const cKey = await crypto.subtle.importKey("raw", keyHash, { name: "AES-GCM" }, false, ["decrypt"]);
    const iv = b64ToBytes(gwObj.iv);
    const ct = b64ToBytes(gwObj.ct);
    const plainBuf = await crypto.subtle.decrypt({ name: "AES-GCM", iv }, cKey, ct);
    return JSON.parse(new TextDecoder().decode(plainBuf));
  }

  async function fetchJsonNoCache(url) {
    const r = await fetch(url + "?t=" + Date.now(), { cache: "no-store" });
    if (!r.ok) throw new Error("HTTP " + r.status);
    return await r.json();
  }

  function getSecretKey() {
    let hk = decodeURIComponent((window.location.hash || "").replace(/^#/, "").trim());
    if (hk.startsWith("k=")) hk = hk.slice(2);
    if (hk) {
      try { localStorage.setItem("hl_gw_key", hk); } catch (e) {}
      try { history.replaceState(null, "", window.location.pathname + window.location.search); } catch (e) {}
      return hk;
    }
    try { return localStorage.getItem("hl_gw_key") || ""; } catch (e) { return ""; }
  }

  function getJwt() {
    try { return localStorage.getItem("hl_jwt") || ""; } catch (e) { return ""; }
  }

  function setJwt(tok) {
    try {
      if (tok) localStorage.setItem("hl_jwt", tok);
      else localStorage.removeItem("hl_jwt");
    } catch (e) {}
  }

  async function refreshTunnelBase() {
    const sec = getSecretKey();
    if (!sec) throw new Error("MISSING_KEY");
    const settled = await Promise.allSettled([fetchJsonNoCache(RAW_GW), fetchJsonNoCache(LOCAL_GW)]);
    const cands = settled.filter(s => s.status === "fulfilled" && s.value && s.value.ct).map(s => s.value);
    if (!cands.length) throw new Error("GATEWAY_FETCH_FAILED");
    cands.sort((a, b) => String(b.updated_at || "").localeCompare(String(a.updated_at || "")));
    const data = await decryptPayload(cands[0], sec);
    if (!data || !data.url) throw new Error("INVALID_KEY");
    tunnelBase = String(data.url).replace(/\/+$/, "");
    return tunnelBase;
  }

  function showOverlay(mode, message) {
    const ov = document.getElementById("gw-overlay");
    const spin = document.getElementById("gw-spin");
    const ttl = document.getElementById("gw-title");
    const msg = document.getElementById("gw-msg");
    const keyForm = document.getElementById("gw-key-form");
    const loginForm = document.getElementById("gw-login-form");
    const retryBtn = document.getElementById("gw-retry-btn");
    const frame = document.getElementById("app-frame");

    ov.style.display = "flex";
    frame.style.display = "none";
    keyForm.style.display = "none";
    loginForm.style.display = "none";
    retryBtn.style.display = "none";

    if (mode === "loading") {
      spin.style.display = "block";
      ttl.textContent = "🔒 고정 보안 터널 연결 중...";
      msg.textContent = message || "실시간 온체인 서버와 동기화하고 있습니다.";
    } else if (mode === "key") {
      spin.style.display = "none";
      ttl.textContent = "🔑 최초 1회 보안키 등록";
      msg.textContent = message || "전달받은 전체 고정 링크(#포함)로 열거나 보안키를 1회 입력해 주세요.";
      keyForm.style.display = "block";
    } else if (mode === "login") {
      spin.style.display = "none";
      ttl.textContent = "👤 내 전용 포트폴리오 로그인";
      msg.textContent = message || "최초 1회 로그인하면 PC가 재부팅되어도 180일간 로그인이 유지됩니다.";
      loginForm.style.display = "block";
    } else if (mode === "error") {
      spin.style.display = "none";
      ttl.textContent = "⚠️ PC 서버 응답 대기 중";
      msg.textContent = message || "PC 대시보드 서버가 재시작 중이거나 일시적 네트워크 지연입니다.";
      retryBtn.style.display = "block";
    }
  }

  function buildBridgeScript(route) {
    const forceLive = (route === "/live" || route === "/m" || route === "/my-portfolio") ? "true" : "false";
    return `<script>
(function(){
  window.__FORCE_LIVE_MODE = ${forceLive};
  const origFetch = window.fetch.bind(window);
  window.fetch = async function(input, init) {
    let url = (typeof input === "string") ? input : (input && input.url ? input.url : String(input));
    const isRel = url.startsWith("/") && !url.startsWith("//");
    if (!isRel) return origFetch(input, init);
    const makeReq = (base) => {
      const opts = Object.assign({}, init || {});
      const hdrs = new Headers(opts.headers || {});
      const tok = window.parent.__getJwt();
      if (tok) hdrs.set("Authorization", "Bearer " + tok);
      hdrs.set("X-Gateway-Client", "1");
      opts.headers = hdrs;
      opts.credentials = "omit";
      return origFetch(base + url, opts);
    };
    try {
      let res = await makeReq(window.parent.__getTunnelBase());
      if (res.status === 401) {
        window.parent.__onUnauthorized();
      }
      return res;
    } catch (err) {
      const newBase = await window.parent.__refreshTunnelBase();
      let res2 = await makeReq(newBase);
      if (res2.status === 401) window.parent.__onUnauthorized();
      return res2;
    }
  };
  document.addEventListener("click", function(e) {
    const a = e.target && e.target.closest ? e.target.closest("a") : null;
    if (!a) return;
    const href = a.getAttribute("href") || "";
    if (!href || href.startsWith("#") || href.startsWith("javascript:")) return;
    if (a.target === "_blank" || href.startsWith("http://") || href.startsWith("https://")) return;
    if (href.startsWith("/")) {
      e.preventDefault();
      window.parent.__navigateRoute(href);
    }
  }, true);
})();
<\/script>`;
  }

  async function fetchBackendHtml(route) {
    const jwt = getJwt();
    if (!jwt) {
      showOverlay("login");
      return null;
    }
    const doFetch = async (base) => {
      return await fetch(base + route, {
        headers: {
          "Authorization": "Bearer " + jwt,
          "X-Gateway-Client": "1"
        },
        cache: "no-store"
      });
    };
    let res;
    try {
      if (!tunnelBase) await refreshTunnelBase();
      res = await doFetch(tunnelBase);
    } catch (e) {
      await refreshTunnelBase();
      res = await doFetch(tunnelBase);
    }
    if (res.status === 401) {
      setJwt("");
      showOverlay("login", "세션이 만료되었습니다. 다시 로그인해 주세요.");
      return null;
    }
    if (!res.ok) throw new Error("HTTP " + res.status);
    return await res.text();
  }

  async function loadRoute(route, pushHist) {
    if (route === "/logout") {
      setJwt("");
      showOverlay("login", "안전하게 로그아웃되었습니다.");
      return;
    }
    currentRoute = route || "/live";
    showOverlay("loading");
    try {
      const rawHtml = await fetchBackendHtml(currentRoute);
      if (rawHtml === null) return;

      // Strip backend manifest/apple-touch-icon links so browser uses permanent github.io PWA manifest
      let cleanHtml = rawHtml
        .replace(/<link[^>]*rel=["']manifest["'][^>]*>/gi, "")
        .replace(/href=["']\/app-icon\.svg["']/gi, 'href="../app-icon.svg"');

      const bridge = buildBridgeScript(currentRoute);
      if (/<head[^>]*>/i.test(cleanHtml)) {
        cleanHtml = cleanHtml.replace(/<head[^>]*>/i, (m) => m + bridge);
      } else {
        cleanHtml = bridge + cleanHtml;
      }

      const frame = document.getElementById("app-frame");
      const ov = document.getElementById("gw-overlay");
      frame.srcdoc = cleanHtml;
      frame.style.display = "block";
      ov.style.display = "none";

      if (pushHist) {
        let prettyUrl = window.location.pathname;
        if (currentRoute.startsWith("/autobot")) prettyUrl = REPO_PREFIX + "/autobot/";
        else if (currentRoute.startsWith("/live") || currentRoute === "/m") prettyUrl = REPO_PREFIX + "/live/";
        else if (currentRoute === "/") prettyUrl = REPO_PREFIX + "/go/";
        else prettyUrl = REPO_PREFIX + "/go/?to=" + encodeURIComponent(currentRoute);
        try { history.pushState({ route: currentRoute }, "", prettyUrl); } catch (e) {}
      }
    } catch (err) {
      if (err && err.message === "MISSING_KEY") {
        showOverlay("key");
      } else if (err && err.message === "INVALID_KEY") {
        showOverlay("key", "보안키가 올바르지 않습니다. 다시 확인해 주세요.");
      } else {
        showOverlay("error", "PC 서버와 연결을 재시도 중입니다. 잠시 후 [다시 연결]을 눌러주세요.");
      }
    }
  }

  // Expose parent bridge helpers to same-origin srcdoc iframe
  window.__getTunnelBase = () => tunnelBase;
  window.__getJwt = () => getJwt();
  window.__refreshTunnelBase = refreshTunnelBase;
  window.__onUnauthorized = () => {
    setJwt("");
    showOverlay("login", "다시 로그인해 주세요.");
  };
  window.__navigateRoute = (href) => loadRoute(href, true);

  window.__submitGatewayKey = async function (e) {
    e.preventDefault();
    const v = (document.getElementById("gw-key-input").value || "").trim();
    if (!v) return;
    try { localStorage.setItem("hl_gw_key", v); } catch (err) {}
    await boot();
  };

  window.__submitGatewayLogin = async function (e) {
    e.preventDefault();
    const email = (document.getElementById("gw-email").value || "").trim();
    const password = document.getElementById("gw-pw").value || "";
    const btn = document.getElementById("gw-login-btn");
    btn.disabled = true;
    btn.textContent = "로그인 중...";
    try {
      if (!tunnelBase) await refreshTunnelBase();
      let res;
      try {
        res = await fetch(tunnelBase + "/api/gateway-login", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Gateway-Client": "1" },
          body: JSON.stringify({ email, password })
        });
      } catch (netErr) {
        await refreshTunnelBase();
        res = await fetch(tunnelBase + "/api/gateway-login", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Gateway-Client": "1" },
          body: JSON.stringify({ email, password })
        });
      }
      const out = await res.json();
      if (!res.ok || !out.ok || !out.access_token) {
        showOverlay("login", out.error || "이메일 또는 비밀번호가 일치하지 않습니다.");
        return;
      }
      setJwt(out.access_token);
      await loadRoute(currentRoute, false);
    } catch (err) {
      showOverlay("error", "로그인 서버 응답 대기 중입니다. 잠시 후 다시 시도해 주세요.");
    } finally {
      btn.disabled = false;
      btn.textContent = "로그인 (180일 자동유지)";
    }
  };

  window.__retryGateway = () => boot();

  window.addEventListener("popstate", (ev) => {
    const r = (ev.state && ev.state.route) ? ev.state.route : (window.__GW_DEFAULT_ROUTE || "/live");
    loadRoute(r, false);
  });

  async function boot() {
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("./sw.js").catch(() => {});
    }
    const params = new URLSearchParams(window.location.search);
    if (params.get("to")) currentRoute = params.get("to");

    const sec = getSecretKey();
    if (!sec) {
      showOverlay("key");
      return;
    }
    showOverlay("loading");
    try {
      await refreshTunnelBase();
      if (!getJwt()) {
        showOverlay("login");
        return;
      }
      await loadRoute(currentRoute, false);
    } catch (err) {
      if (err && err.message === "INVALID_KEY") {
        showOverlay("key", "보안키가 올바르지 않습니다. 전체 고정 링크(#포함)로 다시 접속해 주세요.");
      } else {
        showOverlay("error");
      }
    }
  }

  document.addEventListener("DOMContentLoaded", boot);
})();
