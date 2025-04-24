document.addEventListener("DOMContentLoaded", function () {
    const userType = document.getElementById("id_user_type");
    const authDiv = document.getElementById("div_authorization_id");

    function toggleAuthField() {
      if (userType && authDiv) {
        if (userType.value === "broadcaster") {
          authDiv.style.display = "block";
        } else {
          authDiv.style.display = "none";
          const input = document.getElementById("id_authorization_id");
          if (input) input.value = "";
        }
      }
    }

    if (userType) {
      toggleAuthField();
      userType.addEventListener("change", toggleAuthField);
    }
  });

  function togglePassword(icon) {
    const input = icon.previousElementSibling;
    const type =
      input.getAttribute("type") === "password" ? "text" : "password";
    input.setAttribute("type", type);
    icon.classList.toggle("bi-eye");
    icon.classList.toggle("bi-eye-slash");
  }
