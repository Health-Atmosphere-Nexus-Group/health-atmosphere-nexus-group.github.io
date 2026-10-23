// Mobile menu
var burger = document.querySelector('.burger');
if (burger) burger.addEventListener('click', function () { document.body.classList.toggle('nav-open'); });

// Home banner video plays at the speed set in index.md (the Wix site used 0.5)
document.querySelectorAll('video[data-rate]').forEach(function (v) {
  var rate = parseFloat(v.dataset.rate) || 1;
  var apply = function () { v.playbackRate = rate; };
  apply();
  v.addEventListener('loadedmetadata', apply);
  v.addEventListener('play', apply);
});

// Publications: "Show More" reveals 4 more cards per click
document.querySelectorAll('.pubs-more').forEach(function (btn) {
  btn.addEventListener('click', function () {
    var hidden = document.querySelectorAll('.pub[hidden]');
    for (var i = 0; i < Math.min(4, hidden.length); i++) hidden[i].hidden = false;
    if (hidden.length <= 4) btn.remove();
  });
});

// Pictures marked data-lightbox open full size; click or Esc closes
document.addEventListener('click', function (e) {
  var link = e.target.closest('a[data-lightbox]');
  if (!link) return;
  e.preventDefault();
  var box = document.createElement('div');
  box.className = 'lightbox';
  var img = document.createElement('img');
  img.src = link.href;
  img.alt = '';
  box.appendChild(img);
  box.addEventListener('click', function () { box.remove(); });
  document.body.appendChild(box);
});
document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape') document.querySelectorAll('.lightbox').forEach(function (b) { b.remove(); });
});

// People: if a long bio would run into the profile icons, put the icons below the text instead
function placePersonLinks() {
  document.querySelectorAll('.person').forEach(function (person) {
    var links = person.querySelector('.person-links'), bio = person.querySelector('.person-bio');
    if (!links || !bio) return;
    links.classList.remove('in-flow');
    if (getComputedStyle(links).position !== 'absolute') return;
    var range = document.createRange();
    range.selectNodeContents(bio);
    var rects = range.getClientRects(), box = links.getBoundingClientRect();
    for (var i = 0; i < rects.length; i++) {
      var r = rects[i];
      if (r.width && r.bottom > box.top + 1 && r.top < box.bottom && r.right > box.left - 12) { links.classList.add('in-flow'); return; }
    }
  });
}
if (document.fonts && document.fonts.ready) document.fonts.ready.then(placePersonLinks); else window.addEventListener('load', placePersonLinks);
window.addEventListener('resize', placePersonLinks);
