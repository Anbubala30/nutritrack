(() => {
  const section = document.getElementById('planner-view');
  if (!section) return;

  const form = document.getElementById('planner-form');
  const dateInput = document.getElementById('planner-date');
  const list = document.getElementById('planned-meal-list');
  const error = document.getElementById('planner-error');
  const selectedDate = document.getElementById('selected-date');

  const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[character]));
  const setError = (message) => { error.textContent = message || ''; error.hidden = !message; };

  async function api(path, options = {}) {
    const token = localStorage.getItem('nutritrack_token');
    const headers = { ...(options.headers || {}), Authorization: 'Bearer ' + token };
    if (options.body) headers['Content-Type'] = 'application/json';
    const response = await fetch(path, { ...options, headers });
    const data = response.status === 204 ? null : await response.json();
    if (!response.ok) throw new Error(data?.detail || 'Something went wrong. Please try again.');
    return data;
  }

  function render(meals) {
    if (!meals.length) {
      list.innerHTML = '<div class="empty-state"><span><i data-lucide="calendar-plus" aria-hidden="true"></i>No meals planned for this day yet.</span></div>';
    } else {
      list.innerHTML = meals.map((meal) => '<article class="planned-meal-row"><span class="planned-meal-type">' + escapeHtml(meal.meal_type) + '</span><div><p class="meal-name">' + escapeHtml(meal.name) + '</p><p class="meal-meta">' + meal.calories + ' kcal · ' + meal.protein_g + ' g protein</p></div><button class="icon-button delete-planned-meal" type="button" data-plan-id="' + meal.id + '" aria-label="Remove planned ' + escapeHtml(meal.name) + '"><i data-lucide="trash-2" aria-hidden="true"></i></button></article>').join('');
    }
    window.lucide?.createIcons({ attrs: { width: 18, height: 18 } });
  }

  async function loadPlans() {
    setError();
    try {
      render(await api('/api/plans?planned_for=' + encodeURIComponent(dateInput.value)));
    } catch (loadError) {
      setError(loadError.message);
    }
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    setError();
    const submit = document.getElementById('planner-save');
    submit.disabled = true;
    try {
      await api('/api/plans', {
        method: 'POST',
        body: JSON.stringify({
          planned_for: dateInput.value,
          name: document.getElementById('planner-name').value.trim(),
          meal_type: document.getElementById('planner-type').value,
          calories: Number(document.getElementById('planner-calories').value),
          protein_g: Number(document.getElementById('planner-protein').value || 0),
          carbs_g: Number(document.getElementById('planner-carbs').value || 0),
          fat_g: Number(document.getElementById('planner-fat').value || 0),
        }),
      });
      form.reset();
      dateInput.value = selectedDate.value;
      await loadPlans();
    } catch (saveError) {
      setError(saveError.message);
    } finally {
      submit.disabled = false;
    }
  });

  list.addEventListener('click', async (event) => {
    const button = event.target.closest('.delete-planned-meal');
    if (!button) return;
    try {
      await api('/api/plans/' + button.dataset.planId, { method: 'DELETE' });
      await loadPlans();
    } catch (deleteError) {
      setError(deleteError.message);
    }
  });

  dateInput.addEventListener('change', loadPlans);
  document.addEventListener('nutritrack:planner-open', () => {
    dateInput.value = selectedDate.value;
    void loadPlans();
  });
})();
