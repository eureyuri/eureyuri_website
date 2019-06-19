function toggleNav() {
  var body = document.body;
  var hamburger = document.getElementById('js_hamburger');
  var blackBg = document.getElementById('js_black_bg');

  hamburger.addEventListener('click', function() {
    body.classList.toggle('nav_open');
  });
  blackBg.addEventListener('click', function() {
    body.classList.remove('nav_open');
  });
}
toggleNav();
