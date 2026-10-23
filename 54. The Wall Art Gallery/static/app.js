// Images that finished loading before the onload attribute fired still need to fade in.
document.querySelectorAll("img").forEach(function (im) {
  if (im.complete && im.naturalWidth > 0) im.classList.add("in");
});
