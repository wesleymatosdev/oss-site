/* Renders the catalog from www/projects.js (generated from data/projects.json). */
(function () {
  "use strict";

  var data = window.OSS_PROJECTS;
  if (!data || !data.groups) return;

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function starLabel(n) {
    return n === 1 ? "1 star" : n + " stars";
  }

  function cardHref(p) {
    if (p.public && p.url) return p.url;
    return p.site || null;
  }

  function sectionCard(p) {
    var foot = "";
    if (p.language) foot += '<span class="badge">' + esc(p.language) + "</span>";
    if (p.public && p.stars > 0) foot += '<span class="stars">★ ' + esc(starLabel(p.stars)) + "</span>";

    var actions = "";
    if (p.public && p.url) {
      actions += '<a class="star-btn" href="' + esc(p.url) + '" target="_blank" rel="noopener" ' +
        'title="Opens the repository on GitHub, where the Star control lives">★ Star on GitHub</a>';
    }
    if (p.site) {
      actions += '<a class="site-btn" href="' + esc(p.site) + '" target="_blank" rel="noopener">Visit ↗</a>';
    }

    var state = p.state
      ? '<div class="card-state"><span class="badge state">' + esc(p.state) + "</span>" +
        (p.state_note ? '<span class="state-note">' + esc(p.state_note) + "</span>" : "") + "</div>"
      : "";

    return (
      '<article class="card card-full">' +
      '<h3 class="card-name">' + esc(p.name) + "</h3>" +
      (p.description ? '<p class="card-desc">' + esc(p.description) + "</p>" : "") +
      (p.purpose ? '<p class="card-purpose">' + esc(p.purpose) + "</p>" : "") +
      state +
      '<div class="card-foot">' + foot +
      (actions ? '<div class="card-actions">' + actions + "</div>" : "") +
      (p.local ? '<span class="badge soon">soon</span>' : "") +
      "</div></article>"
    );
  }

  function card(p) {
    var href = cardHref(p);
    var foot = "";
    if (p.language) foot += '<span class="badge">' + esc(p.language) + "</span>";
    if (p.public && p.stars > 0) foot += '<span class="stars">★ ' + esc(starLabel(p.stars)) + "</span>";
    var desc = p.description
      ? '<p class="card-desc">' + esc(p.description) + "</p>"
      : '<p class="card-desc null"></p>';
    var soon = p.local ? '<span class="badge soon">soon</span>' : "";

    if (href) {
      return (
        '<a class="card" href="' + esc(href) + '" target="_blank" rel="noopener">' +
        '<h3 class="card-name">' + esc(p.name) + "</h3>" + desc +
        '<div class="card-foot">' + foot + "</div></a>"
      );
    }
    return (
      '<article class="card' + (p.local ? " soon" : "") + '">' +
      '<h3 class="card-name">' + esc(p.name) + "</h3>" + desc +
      '<div class="card-foot">' + foot + soon + "</div></article>"
    );
  }

  var main = document.getElementById("catalog");
  var html = "";
  data.groups.forEach(function (g) {
    var full = g.projects.filter(function (p) { return p.full; });
    var compact = g.projects.filter(function (p) { return !p.full; });
    html += '<section class="group" data-group="' + esc(g.id) + '">' +
      '<h2 class="group-title">' + esc(g.title) +
      ' <span class="group-count">(' + g.projects.length + ")</span></h2>" +
      '<p class="group-blurb">' + esc(g.blurb) + "</p>";
    if (full.length) html += '<div class="sections">' + full.map(sectionCard).join("") + "</div>";
    if (compact.length) html += '<div class="cards">' + compact.map(card).join("") + "</div>";
    html += "</section>";
  });
  main.innerHTML = html;

  // live filter
  var total = 0;
  data.groups.forEach(function (g) { total += g.projects.length; });

  var input = document.getElementById("filter");
  var count = document.getElementById("count");

  function updateCount(shown) {
    count.textContent = shown === total
      ? total + " projects"
      : shown + " of " + total + " projects";
  }
  updateCount(total);

  input.addEventListener("input", function () {
    var q = input.value.trim().toLowerCase();
    var shown = 0;
    main.querySelectorAll(".group").forEach(function (group) {
      var groupShown = 0;
      [".sections", ".cards"].forEach(function (sel) {
        var wrap = group.querySelector(sel);
        if (!wrap) return;
        var wrapShown = 0;
        wrap.querySelectorAll(".card").forEach(function (el) {
          var hit = !q || el.textContent.toLowerCase().indexOf(q) !== -1;
          el.style.display = hit ? "" : "none";
          if (hit) { groupShown++; wrapShown++; }
        });
        wrap.style.display = wrapShown ? "" : "none";
      });
      group.style.display = groupShown ? "" : "none";
      shown += groupShown;
    });
    updateCount(shown);
  });

  document.getElementById("generated").textContent = "generated " + data.generated;
})();
