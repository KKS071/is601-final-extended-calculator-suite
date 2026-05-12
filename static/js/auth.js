// File: static/js/auth.js
// Purpose: Navbar state only. Password-toggle wiring lives in each page's own
//          script block so there is no cross-script timing dependency.

document.addEventListener("DOMContentLoaded", function () {
  var token = localStorage.getItem("access_token");

  function show(id) { var el = document.getElementById(id); if (el) el.style.display = "inline"; }
  function hide(id) { var el = document.getElementById(id); if (el) el.style.display = "none";   }

  if (token) {
    show("nav-dashboard"); show("nav-profile");
    hide("nav-login");     hide("nav-register"); show("nav-logout");
  } else {
    hide("nav-dashboard"); hide("nav-profile");
    show("nav-login");     show("nav-register"); hide("nav-logout");
  }
});

// ── Logout ────────────────────────────────────────────────────────────────────
function logout() {
  ["access_token", "refresh_token", "user_id", "username", "full_name"].forEach(function (k) {
    localStorage.removeItem(k);
  });
  window.location.href = "/login";
}
