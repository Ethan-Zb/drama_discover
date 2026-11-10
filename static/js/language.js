document.querySelectorAll('.language-switch').forEach((form) => {
  form.addEventListener('submit', () => {
    form.querySelector('input[name="next"]').value = window.location.pathname + window.location.search + window.location.hash;
  });
});
