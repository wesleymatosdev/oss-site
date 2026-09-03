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

  function card(p) {
    var foot = "";
    if (p.language) foot += '<span class="badge">' + esc(p.language) + "</span>";
    if (p.stars > 0) foot += '<span class="stars">★ ' + esc(starLabel(p.stars)) + "</span>";
    var desc = p.description
      ? '<p class="card-desc">' + esc(p.description) + "</p>"
      : '<p class="card-desc null"></p>';

    if (p.url) {
      return (
        '<a class="card" href="' + esc(p.url) + '" target="_blank" rel="noopener">' +
        '<h3 class="card-name">' + esc(p.name) + "</h3>" + desc +
        '<div class="card-foot">' + foot + "</div></a>"
      );
    }
    return (
      '<article class="card soon">' +
      '<h3 class="card-name">' + esc(p.name) + "</h3>" + desc +
      '<div class="card-foot">' + foot + '<span class="badge soon">soon</span></div></article>'
    );
  }

  var main = document.getElementById("catalog");
  var html = "";
  data.groups.forEach(function (g) {
    html +=
      '<section class="group" data-group="' + esc(g.id) + '">' +
      '<h2 class="group-title">' + esc(g.title) +
      ' <span class="group-count">(' + g.projects.length + ")</span></h2>" +
      '<p class="group-blurb">' + esc(g.blurb) + "</p>" +
      '<div class="cards">' + g.projects.map(card).join("") + "</div></section>";
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
      group.querySelectorAll(".card").forEach(function (el) {
        var hit = !q || el.textContent.toLowerCase().indexOf(q) !== -1;
        el.style.display = hit ? "" : "none";
        if (hit) groupShown++;
      });
      group.style.display = groupShown ? "" : "none";
      shown += groupShown;
    });
    updateCount(shown);
  });

  document.getElementById("generated").textContent = "generated " + data.generated;
})();
