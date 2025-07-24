document.addEventListener("DOMContentLoaded", () => {
    const today = new Date().toISOString().split("T")[0];
    const dateInputs = document.querySelectorAll("input[type='date']");
    dateInputs.forEach(input => input.setAttribute("max", today));
  });
  