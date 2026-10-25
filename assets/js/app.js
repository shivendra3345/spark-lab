/* Spark Lab front-end: search, filters, favorites, progress, random picks. */
(function () {
  "use strict";
  var DATA = window.SPARK || { projects: [], cats: {} };
  var P = DATA.projects, CATS = DATA.cats;
  var base = document.body.getAttribute("data-base") || "";
  var DIFF_N = { Easy: 1, Medium: 2, Hard: 3 };

  /* ---------- safe storage ---------- */
  var store = {
    get: function (k, d) { try { var v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } },
    set: function (k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  };
  var favs = function () { return store.get("spark-favs", []); };

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function dots(d) {
    var n = DIFF_N[d] || 1, h = "";
    for (var i = 0; i < 3; i++) h += '<i class="' + (i < n ? "on" : "") + '"></i>';
    return '<span class="diff" title="' + d + '"><span class="dots" aria-hidden="true">' + h + "</span>" + d + "</span>";
  }
  function card(p) {
    var c = CATS[p.c];
    var art = p.i
      ? '<div class="art has-photo"><img src="' + base + esc(p.i) + '" alt="' + esc(p.t) + '" loading="lazy"></div>'
      : '<div class="art" style="--fill:' + c.f + ";--accent:" + c.a + '"><svg class="art-icon" width="92" height="92" viewBox="0 0 64 64" aria-hidden="true" style="--f:' + c.a + '">' + c.svg + '</svg><span class="art-emoji" aria-hidden="true">' + p.e + "</span></div>";
    return '<article class="card" style="--accent:' + c.a + ";--fill:" + c.f + '"><a class="card-link" href="' + base + "projects/" + p.s + '.html">' + art +
      '<div class="card-body"><p class="card-cat">' + esc(c.n) + "</p><h3>" + esc(p.t) + '</h3><p class="meta"><span>Ages ' + esc(p.a) + "</span><span>" + esc(p.tm) + "</span>" + dots(p.d) + "</p></div></a></article>";
  }

  /* ---------- mobile menu ---------- */
  var mb = document.querySelector(".menu-btn"), nav = document.getElementById("site-nav");
  if (mb && nav) mb.addEventListener("click", function () {
    var open = nav.classList.toggle("open");
    mb.setAttribute("aria-expanded", open ? "true" : "false");
  });

  /* ---------- random project ---------- */
  document.querySelectorAll("[data-random]").forEach(function (el) {
    el.addEventListener("click", function (ev) {
      ev.preventDefault();
      var p = P[Math.floor(Math.random() * P.length)];
      if (p) location.href = base + "projects/" + p.s + ".html";
    });
  });

  /* ---------- browse page ---------- */
  var results = document.getElementById("results");
  if (results) {
    var fq = document.getElementById("fq"), fage = document.getElementById("fage"),
      sort = document.getElementById("sort"), count = document.getElementById("count"),
      empty = document.getElementById("empty"), more = document.getElementById("more");
    var PAGE = 48, shown = PAGE;
    var params = new URLSearchParams(location.search);

    // restore state from the address bar
    if (params.get("q")) fq.value = params.get("q");
    if (params.get("age")) fage.value = params.get("age");
    if (params.get("sort")) sort.value = params.get("sort");
    ["topic", "diff", "time"].forEach(function (n) {
      params.getAll(n).forEach(function (v) {
        v.split(",").forEach(function (x) {
          var box = document.querySelector('input[name="' + n + '"][value="' + x + '"]');
          if (box) box.checked = true;
        });
      });
    });
    var hq = document.getElementById("hq");
    if (hq && fq.value) hq.value = fq.value;

    function checked(n) {
      return Array.prototype.map.call(document.querySelectorAll('input[name="' + n + '"]:checked'), function (b) { return b.value; });
    }
    var order = Object.keys(CATS);
    function run(resetPage) {
      if (resetPage) shown = PAGE;
      var q = fq.value.trim().toLowerCase(), words = q ? q.split(/\s+/) : [];
      var topics = checked("topic"), diffs = checked("diff"), times = checked("time"), age = parseInt(fage.value, 10);
      var list = P.filter(function (p) {
        if (topics.length && topics.indexOf(p.c) < 0) return false;
        if (diffs.length && diffs.indexOf(p.d) < 0) return false;
        if (times.length && times.indexOf(p.b) < 0) return false;
        if (age && (age < p.a0 || age > p.a1)) return false;
        if (words.length) {
          var hay = (p.t + " " + p.k + " " + CATS[p.c].n).toLowerCase();
          for (var i = 0; i < words.length; i++) if (hay.indexOf(words[i]) < 0) return false;
        }
        return true;
      });
      var s = sort.value;
      list.sort(function (a, b) {
        if (s === "az") return a.t.localeCompare(b.t);
        if (s === "easy") return DIFF_N[a.d] - DIFF_N[b.d] || a.m - b.m;
        if (s === "quick") return a.m - b.m;
        if (s === "young") return a.a0 - b.a0;
        return order.indexOf(a.c) - order.indexOf(b.c);
      });
      results.innerHTML = list.slice(0, shown).map(card).join("");
      count.textContent = list.length === P.length ? "Showing all " + P.length + " projects"
        : list.length + (list.length === 1 ? " project matches" : " projects match");
      empty.hidden = list.length > 0;
      more.hidden = list.length <= shown;

      // keep the address shareable
      var np = new URLSearchParams();
      if (q) np.set("q", fq.value.trim());
      topics.length && np.set("topic", topics.join(","));
      diffs.length && np.set("diff", diffs.join(","));
      times.length && np.set("time", times.join(","));
      if (age) np.set("age", age);
      if (s !== "topic") np.set("sort", s);
      var qs = np.toString();
      history.replaceState(null, "", location.pathname + (qs ? "?" + qs : ""));
    }
    var t;
    fq.addEventListener("input", function () { clearTimeout(t); t = setTimeout(function () { run(true); }, 150); });
    [fage, sort].forEach(function (el) { el.addEventListener("change", function () { run(true); }); });
    document.querySelectorAll(".filters input[type=checkbox]").forEach(function (b) { b.addEventListener("change", function () { run(true); }); });
    more.addEventListener("click", function () { shown += PAGE; run(false); });
    function clearAll() {
      fq.value = ""; fage.value = ""; sort.value = "topic";
      document.querySelectorAll(".filters input[type=checkbox]").forEach(function (b) { b.checked = false; });
      run(true);
    }
    document.getElementById("clear").addEventListener("click", clearAll);
    document.querySelectorAll("[data-clear]").forEach(function (b) { b.addEventListener("click", clearAll); });
    // header search on this page filters in place
    var hs = document.querySelector(".header-search");
    if (hs) hs.addEventListener("submit", function (ev) { ev.preventDefault(); fq.value = hq.value; run(true); fq.focus(); });
    run(true);
  }

  /* ---------- project page ---------- */
  var proj = document.querySelector(".project");
  if (proj) {
    var slug = proj.getAttribute("data-slug"), key = "spark-progress-" + slug, prog = store.get(key, {});
    proj.querySelectorAll("input[data-key]").forEach(function (b) {
      var k = b.getAttribute("data-key");
      b.checked = !!prog[k];
      b.addEventListener("change", function () { prog[k] = b.checked; store.set(key, prog); });
    });
    var fb = proj.querySelector("[data-fav]");
    function paint() {
      var on = favs().indexOf(slug) >= 0;
      fb.setAttribute("aria-pressed", on ? "true" : "false");
      fb.textContent = on ? " Saved to favorites" : "Save to favorites";
    }
    if (fb) {
      paint();
      fb.addEventListener("click", function () {
        var f = favs(), i = f.indexOf(slug);
        if (i >= 0) f.splice(i, 1); else f.push(slug);
        store.set("spark-favs", f); paint();
      });
    }
    var pr = proj.querySelector("[data-print]");
    if (pr) pr.addEventListener("click", function () { window.print(); });
  }

  /* ---------- favorites page ---------- */
  var favGrid = document.getElementById("fav-results");
  if (favGrid) {
    var f = favs(), list = P.filter(function (p) { return f.indexOf(p.s) >= 0; });
    favGrid.innerHTML = list.map(card).join("");
    document.getElementById("fav-empty").hidden = list.length > 0;
    var fc = document.getElementById("fav-count");
    if (fc) fc.textContent = list.length ? "You have saved " + list.length + (list.length === 1 ? " project." : " projects.") : "";
  }
})();
