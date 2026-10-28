document.addEventListener("DOMContentLoaded", () => {
  // Set sensible minimum dates on booking date inputs.
  const today = new Date();
  const localDate = new Date(today.getTime() - today.getTimezoneOffset() * 60000)
    .toISOString().slice(0, 10);
  document.querySelectorAll('input[type="date"]').forEach((input) => {
    if (!input.min) input.min = localDate;
  });
  document.querySelectorAll('form.booking-form').forEach((form) => {
    const start = form.querySelector('[name="check_in"]');
    const end = form.querySelector('[name="check_out"]');
    if (start && end) {
      start.addEventListener("change", () => {
        end.min = start.value || localDate;
        if (end.value && start.value && end.value <= start.value) end.value = "";
      });
    }
  });
});
