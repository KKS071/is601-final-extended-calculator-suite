// File: static/js/auth.js
// Purpose: Navbar state, logout, and password-visibility toggles.
//
// Password toggle pattern:
//   <button type="button" data-pwd-toggle="inputId">
//     <svg class="eye-open">...</svg>   <!-- shown when password is hidden  -->
//     <svg class="eye-shut hidden">...</svg> <!-- shown when password is visible -->
//   </button>
//
// Wired automatically by the DOMContentLoaded block below — no onclick needed.

// ── Navbar state ───────────────────────────────────────────────────────────────
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

  // ── Wire every password toggle button on the page ─────────────────────────
  document.querySelectorAll("[data-pwd-toggle]").forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      var inputId = btn.getAttribute("data-pwd-toggle");
      var inp     = document.getElementById(inputId);
      if (!inp) return;

      var isHidden = inp.type === "password";
      inp.type = isHidden ? "text" : "password";

      // Swap icons
      var eyeOpen = btn.querySelector(".eye-open");
      var eyeShut = btn.querySelector(".eye-shut");
      if (eyeOpen) eyeOpen.classList.toggle("hidden",  isHidden);  // hide when revealing
      if (eyeShut) eyeShut.classList.toggle("hidden", !isHidden);  // show when revealing

      btn.setAttribute("aria-label", isHidden ? "Hide password" : "Show password");
    });
  });
});

// ── Logout ────────────────────────────────────────────────────────────────────
function logout() {
  ["access_token", "refresh_token", "user_id", "username", "full_name"].forEach(function (k) {
    localStorage.removeItem(k);
  });
  window.location.href = "/login";
}
