const state = {
  authMode: 'login',
  dashboard: null,
  mealSuggestions: [],
  coach: null,
  coachCheckIn: null,
  coachEquation: localStorage.getItem('nutritrack_coach_equation') || 'show_range',
  profile: null,
  weightHistory: null,
  activityHistory: null,
  analytics: null,
  selectedDate: new Date().toISOString().slice(0, 10),
  token: localStorage.getItem('nutritrack_token'),
  user: null,
};

const elements = {
  appShell: document.getElementById('app-shell'),
  authScreen: document.getElementById('auth-screen'),
  authForm: document.getElementById('auth-form'),
  authError: document.getElementById('auth-error'),
  authTitle: document.getElementById('auth-form-title'),
  authCopy: document.getElementById('auth-form-copy'),
  authSubmit: document.getElementById('auth-submit'),
  authPassword: document.getElementById('auth-password'),
  fullNameField: document.getElementById('full-name-field'),
  selectedDate: document.getElementById('selected-date'),
  pageTitle: document.getElementById('page-title'),
  sidebarUser: document.getElementById('sidebar-user'),
  profilePrompt: document.getElementById('profile-prompt'),
  mealDialog: document.getElementById('meal-dialog'),
  mealForm: document.getElementById('meal-form'),
  mealError: document.getElementById('meal-error'),
  mealSuggestions: document.getElementById('meal-suggestions'),
  mealSuggestionList: document.getElementById('meal-suggestion-list'),
  profileForm: document.getElementById('profile-form'),
  profileError: document.getElementById('profile-error'),
  profileStatus: document.getElementById('profile-status'),
  coachContent: document.getElementById('coach-content'),
  coachEquation: document.getElementById('coach-equation'),
  weightForm: document.getElementById('weight-form'),
  weightError: document.getElementById('weight-error'),
  activityForm: document.getElementById('activity-form'),
  activityError: document.getElementById('activity-error'),
};

function refreshIcons() {
  window.lucide?.createIcons({ attrs: { width: 18, height: 18 } });
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;',
  }[character]));
}

function round(value) {
  return Math.round(value * 10) / 10;
}

function percent(value, goal) {
  if (!goal) return 0;
  return Math.min(100, Math.max(0, (value / goal) * 100));
}

function setProgress(id, value, goal) {
  document.getElementById(id).style.width = `${percent(value, goal)}%`;
}

function setMessage(element, message = '') {
  element.textContent = message;
  element.hidden = !message;
}

async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  if (options.body) headers['Content-Type'] = 'application/json';

  const response = await fetch(path, { ...options, headers });
  const contentType = response.headers.get('content-type') || '';
  const body = contentType.includes('application/json') ? await response.json() : null;

  if (!response.ok) {
    if (response.status === 401 && state.token) logout();
    const detail = body?.detail;
    throw new Error(Array.isArray(detail) ? detail[0]?.msg : detail || 'Something went wrong. Please try again.');
  }
  return body;
}

function formatDate(value) {
  return new Intl.DateTimeFormat(undefined, { weekday: 'long', month: 'long', day: 'numeric' }).format(new Date(`${value}T12:00:00`));
}

function formatTime(value) {
  return new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit' }).format(new Date(value));
}

function showAuth() {
  elements.appShell.hidden = true;
  elements.authScreen.hidden = false;
  refreshIcons();
}

function showApp() {
  elements.authScreen.hidden = true;
  elements.appShell.hidden = false;
  refreshIcons();
}

function setAuthMode(mode) {
  state.authMode = mode;
  const signingUp = mode === 'signup';
  document.getElementById('login-mode').classList.toggle('is-active', !signingUp);
  document.getElementById('signup-mode').classList.toggle('is-active', signingUp);
  document.getElementById('login-mode').setAttribute('aria-selected', String(!signingUp));
  document.getElementById('signup-mode').setAttribute('aria-selected', String(signingUp));
  elements.fullNameField.hidden = !signingUp;
  document.getElementById('full-name').required = signingUp;
  elements.authTitle.textContent = signingUp ? 'Create your account' : 'Welcome back';
  elements.authCopy.textContent = signingUp ? 'Start with a simple daily nutrition log.' : 'Use your NutriTrack account to continue.';
  elements.authSubmit.innerHTML = `${signingUp ? 'Create account' : 'Sign in'} <i data-lucide="arrow-right" aria-hidden="true"></i>`;
  elements.authPassword.autocomplete = signingUp ? 'new-password' : 'current-password';
  setMessage(elements.authError);
  refreshIcons();
}

async function submitAuth(event) {
  event.preventDefault();
  setMessage(elements.authError);
  const email = document.getElementById('auth-email').value.trim();
  const password = elements.authPassword.value;
  const submit = elements.authSubmit;
  submit.disabled = true;

  try {
    if (state.authMode === 'signup') {
      await api('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ email, password, full_name: document.getElementById('full-name').value.trim() || null }),
      });
    }
    const token = await api('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
    state.token = token.access_token;
    localStorage.setItem('nutritrack_token', state.token);
    await loadApp();
  } catch (error) {
    setMessage(elements.authError, error.message);
  } finally {
    submit.disabled = false;
  }
}

function setView(viewName) {
  const titles = { dashboard: "Today's overview", meals: 'Meals', coach: 'AI Coach', activity: 'Activity tracker', weight: 'Weight tracker', profile: 'My plan' };
  document.querySelectorAll('.view-section').forEach((section) => { section.hidden = section.id !== `${viewName}-view`; });
  document.querySelectorAll('[data-view]').forEach((button) => {
    const active = button.dataset.view === viewName;
    button.classList.toggle('is-active', active);
    button.toggleAttribute('aria-current', active);
  });
  elements.pageTitle.textContent = titles[viewName];
  if (viewName === 'coach') void loadCoach();
  if (viewName === 'activity') void loadActivityHistory();
  if (viewName === 'weight') void loadWeightHistory();
}

function defaultProfile() {
  return {
    age: null, height_cm: null, weight_kg: null, gender: null, goal_weight_kg: null, dietary_preference: 'no_preference', allergies: null, activity_level: 'moderately_active', goal: 'maintain', calorie_goal: 2000, protein_goal_g: 120, water_goal_ml: 2500,
  };
}

function fillProfileForm(profile) {
  const values = profile || defaultProfile();
  document.getElementById('profile-age').value = values.age ?? '';
  document.getElementById('profile-height').value = values.height_cm ?? '';
  document.getElementById('profile-weight').value = values.weight_kg ?? '';
  document.getElementById('profile-gender').value = values.gender ?? '';
  document.getElementById('profile-goal-weight').value = values.goal_weight_kg ?? '';
  document.getElementById('profile-diet').value = values.dietary_preference ?? 'no_preference';
  document.getElementById('profile-allergies').value = values.allergies ?? '';
  document.getElementById('profile-activity').value = values.activity_level;
  document.getElementById('profile-goal').value = values.goal;
  document.getElementById('profile-calories').value = values.calorie_goal;
  document.getElementById('profile-protein').value = values.protein_goal_g;
  document.getElementById('profile-water').value = values.water_goal_ml;
}

function mealIcon(mealType) {
  return mealType === 'snack' ? 'apple' : mealType === 'dinner' ? 'moon-star' : 'utensils';
}

function mealListMarkup(meals) {
  if (!meals.length) {
    return '<div class="empty-state"><span><i data-lucide="utensils" aria-hidden="true"></i>Nothing logged for this day.</span></div>';
  }
  return meals.map((meal) => `
    <article class="meal-row">
      <span class="meal-type-icon" data-type="${escapeHtml(meal.meal_type)}"><i data-lucide="${mealIcon(meal.meal_type)}" aria-hidden="true"></i></span>
      <div><p class="meal-name">${escapeHtml(meal.name)}</p><p class="meal-meta">${escapeHtml(meal.meal_type)} · ${formatTime(meal.logged_at)}</p></div>
      <p class="meal-calories">${meal.calories} kcal</p>
      <p class="meal-protein">${round(meal.protein_g)} g protein</p>
      <button class="icon-button delete-meal" type="button" data-meal-id="${meal.id}" aria-label="Delete ${escapeHtml(meal.name)}"><i data-lucide="trash-2" aria-hidden="true"></i></button>
    </article>
  `).join('');
}

function renderDashboard() {
  const { dashboard } = state;
  if (!dashboard) return;
  const { goals, totals, water, meals } = dashboard;
  const remaining = goals.calorie_goal - totals.calories;
  elements.profilePrompt.hidden = dashboard.profile_complete;
  document.getElementById('calories-total').textContent = totals.calories.toLocaleString();
  document.getElementById('calories-remaining').textContent = remaining >= 0 ? `${remaining.toLocaleString()} kcal remaining` : `${Math.abs(remaining).toLocaleString()} kcal over goal`;
  document.getElementById('protein-total').textContent = round(totals.protein_g);
  document.getElementById('protein-goal').textContent = `of ${round(goals.protein_goal_g)} g goal`;
  document.getElementById('water-total').textContent = water.amount_ml.toLocaleString();
  document.getElementById('water-goal').textContent = `of ${water.goal_ml.toLocaleString()} ml goal`;
  document.getElementById('macro-protein').textContent = `${round(totals.protein_g)} g`;
  document.getElementById('macro-carbs').textContent = `${round(totals.carbs_g)} g`;
  document.getElementById('macro-fat').textContent = `${round(totals.fat_g)} g`;
  document.getElementById('water-summary').textContent = `${water.amount_ml.toLocaleString()} of ${water.goal_ml.toLocaleString()} ml`;
  setProgress('calorie-progress', totals.calories, goals.calorie_goal);
  setProgress('protein-progress', totals.protein_g, goals.protein_goal_g);
  setProgress('water-progress', water.amount_ml, water.goal_ml);
  setProgress('macro-protein-progress', totals.protein_g, goals.protein_goal_g);
  setProgress('macro-carbs-progress', totals.carbs_g, 300);
  setProgress('macro-fat-progress', totals.fat_g, 80);
  const markup = mealListMarkup(meals);
  document.getElementById('recent-meals').innerHTML = markup;
  document.getElementById('all-meals').innerHTML = markup;
  refreshIcons();
}

function renderAnalytics() {
  const analytics = state.analytics;
  if (!analytics) return;
  document.getElementById('weekly-calorie-average').textContent = `${analytics.average_calories.toLocaleString()} kcal`;
  document.getElementById('weekly-water-average').textContent = `${analytics.average_water_ml.toLocaleString()} ml`;
  document.getElementById('weekly-activity-total').textContent = `${analytics.total_activity_minutes.toLocaleString()} min`;
  document.getElementById('weekly-burn-total').textContent = `${analytics.total_calories_burned.toLocaleString()} kcal estimated burn`;
  document.getElementById('weekly-days').innerHTML = analytics.days.map((day) => `
    <article class="weekly-day">
      <strong class="weekly-day-name">${formatDate(day.logged_on)}</strong>
      <span class="weekly-day-metric">${day.calories.toLocaleString()} kcal</span>
      <span class="weekly-day-metric">${round(day.protein_g)} g protein</span>
      <span class="weekly-day-metric">${day.water_ml.toLocaleString()} ml water · ${day.activity_minutes} min</span>
    </article>
  `).join('');
}

async function loadAnalytics() {
  try {
    state.analytics = await api(`/api/analytics/week?end_date=${encodeURIComponent(state.selectedDate)}`);
    renderAnalytics();
  } catch {
    state.analytics = null;
  }
}

async function loadDashboard() {
  state.dashboard = await api(`/api/dashboard?logged_on=${encodeURIComponent(state.selectedDate)}`);
  renderDashboard();
  await loadAnalytics();
}

function formatRange(range) {
  if (range.low === range.high) return range.low.toLocaleString();
  return `${range.low.toLocaleString()}-${range.high.toLocaleString()}`;
}

function renderCoach() {
  const coach = state.coach;
  if (!coach) {
    elements.coachContent.innerHTML = '<div class="coach-empty"><i data-lucide="sparkles" aria-hidden="true"></i><p>Preparing your personal estimate.</p></div>';
    refreshIcons();
    return;
  }

  if (!coach.ready) {
    elements.coachContent.innerHTML = `
      <div class="coach-empty">
        <i data-lucide="clipboard-pen-line" aria-hidden="true"></i>
        <h3>Complete your plan for a personal estimate.</h3>
        ${coach.messages.map((message) => `<p>${escapeHtml(message)}</p>`).join('')}
        <p class="coach-disclaimer">${escapeHtml(coach.disclaimer)}</p>
      </div>`;
    refreshIcons();
    return;
  }

  const macros = coach.macro_guidance;
  elements.coachContent.innerHTML = `
    <section class="coach-estimate-grid" aria-label="Calorie estimates">
      <article class="coach-estimate"><p class="section-kicker">Resting estimate</p><p class="coach-estimate-value">${formatRange(coach.bmr_calories)} <span class="coach-estimate-unit">kcal</span></p><p class="coach-estimate-note">Estimated energy used at rest.</p></article>
      <article class="coach-estimate"><p class="section-kicker">Maintenance range</p><p class="coach-estimate-value">${formatRange(coach.maintenance_calories)} <span class="coach-estimate-unit">kcal</span></p><p class="coach-estimate-note">Estimated daily energy with your activity setting.</p></article>
      <article class="coach-estimate"><p class="section-kicker">Goal range</p><p class="coach-estimate-value">${formatRange(coach.goal_calories)} <span class="coach-estimate-unit">kcal</span></p><p class="coach-estimate-note">Starting range for your selected plan.</p><button id="apply-coach-target" class="text-button coach-apply-target" type="button">Use midpoint <i data-lucide="arrow-right" aria-hidden="true"></i></button></article>
    </section>
    <section class="coach-section" aria-labelledby="macro-guide-title">
      <h3 id="macro-guide-title">Macro guide</h3>
      <div class="macro-guide-grid">
        <article class="macro-guide"><p>Protein</p><strong>${round(macros.protein_goal_g)} g</strong><span>${round(macros.protein_logged_g)} g logged today against your saved goal.</span></article>
        <article class="macro-guide"><p>Carbohydrates</p><strong>${formatRange(macros.carbohydrate_range_g)} g</strong><span>General daily range based on 45-65% of the goal-calorie midpoint.</span></article>
        <article class="macro-guide"><p>Fat</p><strong>${formatRange(macros.fat_range_g)} g</strong><span>General daily range based on 20-35% of the goal-calorie midpoint.</span></article>
      </div>
    </section>
    <section class="coach-section" aria-labelledby="coach-guidance-title">
      <h3 id="coach-guidance-title">Coach guidance</h3>
      <div class="coach-guidance">${coach.messages.map((message) => `<div class="coach-guidance-item"><i data-lucide="circle-check" aria-hidden="true"></i><p>${escapeHtml(message)}</p></div>`).join('')}</div>
    </section>
    <section class="coach-section coach-check-in" aria-labelledby="coach-check-in-title">
      <h3 id="coach-check-in-title">Quick check-in</h3>
      <div class="coach-prompt-row">
        <button class="coach-prompt" type="button" data-coach-focus="summary">Today</button>
        <button class="coach-prompt" type="button" data-coach-focus="protein">Protein</button>
        <button class="coach-prompt" type="button" data-coach-focus="hydration">Water</button>
        <button class="coach-prompt" type="button" data-coach-focus="activity">Activity</button>
        <button class="coach-prompt" type="button" data-coach-focus="energy">Energy</button>
      </div>
      <p id="coach-check-in-answer" class="coach-check-in-answer" aria-live="polite">Choose a topic for a personal check-in.</p>
    </section>
    <p class="coach-method">${escapeHtml(coach.method)}</p>
    <p class="coach-disclaimer">${escapeHtml(coach.disclaimer)}</p>`;
  refreshIcons();
}

async function loadCoach() {
  elements.coachEquation.value = state.coachEquation;
  state.coach = null;
  renderCoach();
  try {
    state.coach = await api(`/api/coach?logged_on=${encodeURIComponent(state.selectedDate)}&sex_for_equation=${encodeURIComponent(state.coachEquation)}`);
    renderCoach();
  } catch (error) {
    elements.coachContent.innerHTML = `<div class="coach-empty"><i data-lucide="triangle-alert" aria-hidden="true"></i><p>${escapeHtml(error.message)}</p></div>`;
    refreshIcons();
  }
}

function coachTargetMidpoint() {
  if (!state.coach?.goal_calories) return null;
  const range = state.coach.goal_calories;
  return Math.round(((range.low + range.high) / 2) / 50) * 50;
}

async function applyCoachTarget() {
  const calorieGoal = coachTargetMidpoint();
  const button = document.getElementById('apply-coach-target');
  if (!calorieGoal || !state.profile || !button) return;
  button.disabled = true;
  const previousMarkup = button.innerHTML;
  button.textContent = 'Saving...';
  try {
    const profile = state.profile;
    state.profile = await api('/api/profile', {
      method: 'PUT',
      body: JSON.stringify({
        age: profile.age,
        height_cm: profile.height_cm,
        weight_kg: profile.weight_kg,
        gender: profile.gender,
        goal_weight_kg: profile.goal_weight_kg,
        dietary_preference: profile.dietary_preference,
        allergies: profile.allergies,
        activity_level: profile.activity_level,
        goal: profile.goal,
        calorie_goal: calorieGoal,
        protein_goal_g: profile.protein_goal_g,
        water_goal_ml: profile.water_goal_ml,
      }),
    });
    fillProfileForm(state.profile);
    await loadDashboard();
    await loadCoach();
  } catch (error) {
    button.textContent = error.message;
  } finally {
    if (document.getElementById('apply-coach-target')) {
      document.getElementById('apply-coach-target').innerHTML = previousMarkup;
      document.getElementById('apply-coach-target').disabled = false;
      refreshIcons();
    }
  }
}

async function loadCoachCheckIn(focus) {
  const answer = document.getElementById('coach-check-in-answer');
  if (!answer) return;
  const buttons = document.querySelectorAll('[data-coach-focus]');
  buttons.forEach((button) => { button.disabled = true; });
  answer.textContent = 'Preparing your check-in...';
  try {
    const checkIn = await api(`/api/coach/check-in?focus=${encodeURIComponent(focus)}&logged_on=${encodeURIComponent(state.selectedDate)}&sex_for_equation=${encodeURIComponent(state.coachEquation)}`);
    state.coachCheckIn = checkIn;
    answer.textContent = checkIn.answer;
  } catch (error) {
    answer.textContent = error.message;
  } finally {
    buttons.forEach((button) => { button.disabled = false; });
  }
}

function renderWeightHistory() {
  const history = state.weightHistory;
  if (!history) return;
  const latest = history.entries[0];
  document.getElementById('latest-weight').textContent = latest ? `${round(latest.weight_kg)} kg` : 'No entry';
  const change = latest && history.entries[1] ? round(latest.weight_kg - history.entries[1].weight_kg) : null;
  document.getElementById('weight-change').textContent = change === null ? 'Log your first measurement.' : `${change > 0 ? '+' : ''}${change} kg from previous entry`;
  document.getElementById('bmi-value').textContent = history.bmi ?? '--';
  document.getElementById('bmi-note').textContent = history.bmi_note;
  document.getElementById('weight-list').innerHTML = history.entries.length ? history.entries.map((entry) => `<article class="weight-row"><div><strong>${round(entry.weight_kg)} kg</strong><p>${formatDate(entry.logged_on)}${entry.note ? ` · ${escapeHtml(entry.note)}` : ''}</p></div><button class="icon-button delete-weight" type="button" data-weight-id="${entry.id}" aria-label="Delete weight entry"><i data-lucide="trash-2" aria-hidden="true"></i></button></article>`).join('') : '<div class="empty-state"><span><i data-lucide="scale" aria-hidden="true"></i>No weight entries yet.</span></div>';
  refreshIcons();
}
async function loadWeightHistory() {
  try { state.weightHistory = await api('/api/weights?days=90'); renderWeightHistory(); }
  catch (error) { setMessage(elements.weightError, error.message); }
}
async function saveWeight(event) {
  event.preventDefault(); setMessage(elements.weightError);
  const submit = document.getElementById('weight-save'); submit.disabled = true;
  try {
    await api('/api/weights', { method: 'PUT', body: JSON.stringify({ weight_kg: Number(document.getElementById('weight-value-input').value), logged_on: document.getElementById('weight-date').value, note: document.getElementById('weight-note').value.trim() || null }) });
    elements.weightForm.reset(); document.getElementById('weight-date').value = state.selectedDate; await loadWeightHistory();
  } catch (error) { setMessage(elements.weightError, error.message); }
  finally { submit.disabled = false; }
}
async function deleteWeight(entryId) {
  try { await api(`/api/weights/${entryId}`, { method: 'DELETE' }); await loadWeightHistory(); }
  catch (error) { window.alert(error.message); }
}

function renderActivityHistory() {
  const history = state.activityHistory;
  if (!history) return;
  document.getElementById('activity-minutes-total').textContent = `${history.total_minutes.toLocaleString()} min`;
  document.getElementById('activity-calories-total').textContent = `${history.total_calories_burned.toLocaleString()} kcal`;
  document.getElementById('activity-list').innerHTML = history.entries.length
    ? history.entries.map((entry) => `<article class="activity-row"><div><strong>${escapeHtml(entry.activity_type)}</strong><p>${entry.minutes} min · ${entry.calories_burned} kcal${entry.note ? ` · ${escapeHtml(entry.note)}` : ''}</p></div><button class="icon-button delete-activity" type="button" data-activity-id="${entry.id}" aria-label="Delete activity entry"><i data-lucide="trash-2" aria-hidden="true"></i></button></article>`).join('')
    : '<div class="empty-state"><span><i data-lucide="person-standing" aria-hidden="true"></i>No activity logged for this day.</span></div>';
  refreshIcons();
}

async function loadActivityHistory() {
  try {
    state.activityHistory = await api(`/api/activities?logged_on=${encodeURIComponent(state.selectedDate)}`);
    renderActivityHistory();
  } catch (error) {
    setMessage(elements.activityError, error.message);
  }
}

async function saveActivity(event) {
  event.preventDefault();
  setMessage(elements.activityError);
  const submit = document.getElementById('activity-save');
  submit.disabled = true;
  try {
    await api('/api/activities', {
      method: 'POST',
      body: JSON.stringify({
        activity_type: document.getElementById('activity-type').value.trim(),
        minutes: Number(document.getElementById('activity-minutes').value),
        calories_burned: Number(document.getElementById('activity-calories').value),
        logged_on: state.selectedDate,
        note: document.getElementById('activity-note').value.trim() || null,
      }),
    });
    elements.activityForm.reset();
    document.getElementById('activity-calories').value = '0';
    await loadActivityHistory();
  } catch (error) {
    setMessage(elements.activityError, error.message);
  } finally {
    submit.disabled = false;
  }
}

async function deleteActivity(entryId) {
  try {
    await api(`/api/activities/${entryId}`, { method: 'DELETE' });
    await loadActivityHistory();
  } catch (error) {
    window.alert(error.message);
  }
}

async function loadApp() {
  try {
    const [user, profile] = await Promise.all([api('/auth/me'), api('/api/profile')]);
    state.user = user;
    state.profile = profile;
    elements.sidebarUser.textContent = user.email;
    fillProfileForm(profile);
    elements.selectedDate.value = state.selectedDate;
    elements.coachEquation.value = state.coachEquation;
    showApp();
    await loadDashboard();
  } catch (error) {
    logout();
    setMessage(elements.authError, 'Your session has ended. Please sign in again.');
  }
}

function logout() {
  state.token = null;
  state.user = null;
  state.dashboard = null;
  localStorage.removeItem('nutritrack_token');
  showAuth();
}

function renderMealSuggestions() {
  const suggestions = state.mealSuggestions;
  elements.mealSuggestions.hidden = !suggestions.length;
  elements.mealSuggestionList.innerHTML = suggestions.map((meal, index) => `
    <button class="meal-suggestion" type="button" data-meal-suggestion="${index}">
      <strong>${escapeHtml(meal.name)}</strong>
      <span>${meal.calories} kcal · ${round(meal.protein_g)} g protein</span>
    </button>
  `).join('');
}

async function loadMealSuggestions() {
  try {
    state.mealSuggestions = await api('/api/meals/suggestions');
    renderMealSuggestions();
  } catch {
    state.mealSuggestions = [];
    renderMealSuggestions();
  }
}

function applyMealSuggestion(index) {
  const meal = state.mealSuggestions[Number(index)];
  if (!meal) return;
  document.getElementById('meal-name').value = meal.name;
  document.getElementById('meal-type').value = meal.meal_type;
  document.getElementById('meal-calories').value = meal.calories;
  document.getElementById('meal-protein').value = meal.protein_g;
  document.getElementById('meal-carbs').value = meal.carbs_g;
  document.getElementById('meal-fat').value = meal.fat_g;
  document.getElementById('meal-name').focus();
}

function openMealDialog() {
  setMessage(elements.mealError);
  elements.mealForm.reset();
  document.getElementById('meal-protein').value = '0';
  document.getElementById('meal-carbs').value = '0';
  document.getElementById('meal-fat').value = '0';
  const now = new Date();
  const day = state.selectedDate;
  const localTime = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
  document.getElementById('meal-time').value = `${day}T${localTime}`;
  elements.mealDialog.showModal();
  document.getElementById('meal-name').focus();
  void loadMealSuggestions();
}

async function submitMeal(event) {
  event.preventDefault();
  setMessage(elements.mealError);
  const submit = document.getElementById('meal-submit');
  submit.disabled = true;
  try {
    await api('/api/meals', {
      method: 'POST',
      body: JSON.stringify({
        name: document.getElementById('meal-name').value.trim(),
        meal_type: document.getElementById('meal-type').value,
        calories: Number(document.getElementById('meal-calories').value),
        protein_g: Number(document.getElementById('meal-protein').value),
        carbs_g: Number(document.getElementById('meal-carbs').value),
        fat_g: Number(document.getElementById('meal-fat').value),
        logged_at: document.getElementById('meal-time').value || null,
      }),
    });
    elements.mealDialog.close();
    await loadDashboard();
  } catch (error) {
    setMessage(elements.mealError, error.message);
  } finally {
    submit.disabled = false;
  }
}

async function deleteMeal(mealId) {
  try {
    await api(`/api/meals/${mealId}`, { method: 'DELETE' });
    await loadDashboard();
  } catch (error) {
    window.alert(error.message);
  }
}

async function changeWater(delta) {
  if (!state.dashboard) return;
  const amount = Math.max(0, state.dashboard.water.amount_ml + delta);
  try {
    await api(`/api/water?logged_on=${encodeURIComponent(state.selectedDate)}`, { method: 'PUT', body: JSON.stringify({ amount_ml: amount }) });
    await loadDashboard();
  } catch (error) {
    window.alert(error.message);
  }
}

async function saveProfile(event) {
  event.preventDefault();
  setMessage(elements.profileError);
  elements.profileStatus.textContent = '';
  const submit = document.getElementById('profile-save');
  submit.disabled = true;
  const optionalNumber = (id) => {
    const value = document.getElementById(id).value;
    return value === '' ? null : Number(value);
  };
  try {
    state.profile = await api('/api/profile', {
      method: 'PUT',
      body: JSON.stringify({
        age: optionalNumber('profile-age'),
        height_cm: optionalNumber('profile-height'),
        weight_kg: optionalNumber('profile-weight'),
        gender: document.getElementById('profile-gender').value || null,
        goal_weight_kg: optionalNumber('profile-goal-weight'),
        dietary_preference: document.getElementById('profile-diet').value,
        allergies: document.getElementById('profile-allergies').value.trim() || null,
        activity_level: document.getElementById('profile-activity').value,
        goal: document.getElementById('profile-goal').value,
        calorie_goal: Number(document.getElementById('profile-calories').value),
        protein_goal_g: Number(document.getElementById('profile-protein').value),
        water_goal_ml: Number(document.getElementById('profile-water').value),
      }),
    });
    elements.profileStatus.textContent = 'Daily plan saved.';
    await loadDashboard();
    if (!document.getElementById('coach-view').hidden) await loadCoach();
  } catch (error) {
    setMessage(elements.profileError, error.message);
  } finally {
    submit.disabled = false;
  }
}

document.getElementById('login-mode').addEventListener('click', () => setAuthMode('login'));
document.getElementById('signup-mode').addEventListener('click', () => setAuthMode('signup'));
elements.authForm.addEventListener('submit', submitAuth);
document.getElementById('logout-button').addEventListener('click', logout);
elements.selectedDate.addEventListener('change', async (event) => { state.selectedDate = event.target.value; await loadDashboard(); if (!document.getElementById('coach-view').hidden) await loadCoach(); if (!document.getElementById('activity-view').hidden) await loadActivityHistory(); });
document.querySelectorAll('[data-view]').forEach((button) => button.addEventListener('click', () => setView(button.dataset.view)));
elements.coachEquation.addEventListener('change', async (event) => { state.coachEquation = event.target.value; localStorage.setItem('nutritrack_coach_equation', state.coachEquation); await loadCoach(); });
document.getElementById('add-meal-button').addEventListener('click', openMealDialog);
document.querySelectorAll('[data-open-meal]').forEach((button) => button.addEventListener('click', openMealDialog));
document.getElementById('close-meal-dialog').addEventListener('click', () => elements.mealDialog.close());
document.getElementById('cancel-meal').addEventListener('click', () => elements.mealDialog.close());
elements.mealForm.addEventListener('submit', submitMeal);
elements.profileForm.addEventListener('submit', saveProfile);
elements.weightForm.addEventListener('submit', saveWeight);
elements.activityForm.addEventListener('submit', saveActivity);
document.querySelectorAll('[data-water]').forEach((button) => button.addEventListener('click', () => changeWater(Number(button.dataset.water))));
document.getElementById('water-reset').addEventListener('click', () => changeWater(-state.dashboard?.water.amount_ml || 0));
document.addEventListener('click', (event) => {
  const button = event.target.closest('.delete-meal');
  if (button) deleteMeal(button.dataset.mealId);
  const weightButton = event.target.closest('.delete-weight');
  if (weightButton) deleteWeight(weightButton.dataset.weightId);
  const activityButton = event.target.closest('.delete-activity');
  if (activityButton) deleteActivity(activityButton.dataset.activityId);
  const mealSuggestionButton = event.target.closest('[data-meal-suggestion]');
  if (mealSuggestionButton) applyMealSuggestion(mealSuggestionButton.dataset.mealSuggestion);
  const coachButton = event.target.closest('[data-coach-focus]');
  if (coachButton) loadCoachCheckIn(coachButton.dataset.coachFocus);
  const applyCoachTargetButton = event.target.closest('#apply-coach-target');
  if (applyCoachTargetButton) applyCoachTarget();
});

setAuthMode('login');
document.getElementById('weight-date').value = state.selectedDate;
if (state.token) loadApp(); else showAuth();
