// File: static/js/auth.js
// Purpose: Shared navbar state, logout helper, and password-visibility toggle.

// ── Navbar state ───────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", function () {
  var token = localStorage.getItem("access_token");

  function show(id) { var el = document.getElementById(id); if (el) el.style.display = "inline"; }
  function hide(id) { var el = document.getElementById(id); if (el) el.style.display = "none";   }

  if (token) {
    show("nav-dashboard");
    show("nav-profile");
    hide("nav-login");
    hide("nav-register");
    show("nav-logout");
  } else {
    hide("nav-dashboard");
    hide("nav-profile");
    show("nav-login");
    show("nav-register");
    hide("nav-logout");
  }
});

// ── Logout ────────────────────────────────────────────────────────────────────
function logout() {
  ["access_token", "refresh_token", "user_id", "username", "full_name"].forEach(function (k) {
    localStorage.removeItem(k);
  });
  window.location.href = "/login";
}

// ── Password visibility toggle ────────────────────────────────────────────────
// Call once per password input: togglePwd(inputId, buttonElement)
function togglePwd(inputId, btn) {
  var inp     = document.getElementById(inputId);
  var showing = inp.type === "text";
  inp.type    = showing ? "password" : "text";

  // Swap icon: eye-off when showing (click to hide), eye when hidden (click to show)
  btn.innerHTML = showing ? eyeSVG() : eyeOffSVG();
  btn.setAttribute("aria-label", showing ? "Show password" : "Hide password");
}

function eyeSVG() {
  return '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" ' +
         'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
         '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>' +
         '<circle cx="12" cy="12" r="3"/></svg>';
}

function eyeOffSVG() {
  return '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" ' +
         'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
         '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>' +
         '<path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>' +
         '<line x1="1" y1="1" x2="23" y2="23"/></svg>';
}
