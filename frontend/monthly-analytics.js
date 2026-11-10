(() => {
  const section = document.getElementById('progress-view');
  if (!section) return;

  const range = document.getElementById('monthly-range');
  const averageCalories = document.getElementById('monthly-calorie-average');
  const activeDays = document.getElementById('monthly-active-days');
  const activityMinutes = document.getElementById('monthly-activity-total');
  const activityBurn = document.getElementById('monthly-burn-total');
  const weightValue = document.getElementById('monthly-weight-change');
  const weightNote = document.getElementById('monthly-weight-note');
  const chart = document.getElementById('monthly-chart');
  const empty = document.getElementById('monthly-empty');
  const dateInput = document.getElementById('selected-date');

  const formatNumber = (value) => Number(value || 0).toLocaleString();
  const dayLabel = (value) => new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' }).format(new Date(value + 'T12:00:00'));
  const rangeLabel = (start, end) => dayLabel(start) + ' - ' + dayLabel(end);

  function render(data) {
    range.textContent = rangeLabel(data.start_date, data.end_date);
    averageCalories.textContent = formatNumber(data.average_calories) + ' kcal';
    activeDays.textContent = data.active_days + ' of 30';
    activityMinutes.textContent = formatNumber(data.total_activity_minutes) + ' min';
    activityBurn.textContent = formatNumber(data.total_calories_burned) + ' kcal estimated burn';

    const weights = data.weight_entries || [];
    if (weights.length < 2) {
      weightValue.textContent = weights.length ? weights[0].weight_kg + ' kg' : '--';
      weightNote.textContent = weights.length ? 'Add another check-in to see your monthly change.' : 'Log weight check-ins to see a monthly trend.';
    } else {
      const change = Math.round((weights[weights.length - 1].weight_kg - weights[0].weight_kg) * 10) / 10;
      const direction = change === 0 ? 'steady' : change < 0 ? 'down' : 'up';
      weightValue.textContent = (change > 0 ? '+' : '') + change + ' kg';
      weightNote.textContent = direction === 'steady'
        ? 'Steady across your logged check-ins.'
        : (direction === 'down' ? 'Down' : 'Up') + ' from ' + weights[0].weight_kg + ' kg to ' + weights[weights.length - 1].weight_kg + ' kg.';
    }

    const highest = Math.max(1, ...data.days.map((day) => day.calories));
    chart.innerHTML = data.days.map((day, index) => {
      const height = Math.max(3, Math.round((day.calories / highest) * 100));
      const labelled = index % 5 === 0 || index === data.days.length - 1;
      return '<div class="monthly-bar-wrap" title="' + dayLabel(day.logged_on) + ': ' + formatNumber(day.calories) + ' kcal"><span class="monthly-bar" style="height: ' + height + '%"></span>' + (labelled ? '<small>' + dayLabel(day.logged_on) + '</small>' : '') + '</div>';
    }).join('');

    const hasProgress = data.days.some((day) => day.calories || day.water_ml || day.activity_minutes);
    empty.hidden = hasProgress;
    chart.hidden = !hasProgress;
  }

  async function loadMonthly(date) {
    const token = localStorage.getItem('nutritrack_token');
    if (!token) return;
    try {
      const response = await fetch('/api/analytics/month?end_date=' + encodeURIComponent(date), {
        headers: { Authorization: 'Bearer ' + token },
      });
      if (!response.ok) throw new Error('Unable to load monthly progress');
      render(await response.json());
    } catch {
      empty.hidden = false;
      empty.textContent = 'Monthly progress will appear as you log meals, water, activity, and weight.';
      chart.hidden = true;
    }
  }

  document.addEventListener('nutritrack:progress-open', (event) => loadMonthly(event.detail.date));
  dateInput.addEventListener('change', () => { if (!section.hidden) loadMonthly(dateInput.value); });
})();
