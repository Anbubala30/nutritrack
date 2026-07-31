# NutriTrack

NutriTrack is a local nutrition dashboard for setting personal targets, logging meals, and tracking daily hydration.

## What it includes

- Account registration and sign-in with bcrypt password hashing and JWT sessions
- A personal plan for calorie, protein, and water targets
- Meal logging with calories, protein, carbohydrates, fat, date, and meal type
- Daily calorie, macro, and water progress
- An AI Coach view with calorie estimates, macro ranges, and daily coaching notes
- A responsive browser dashboard served directly by FastAPI

## Run locally

1. Install Python 3.12 or newer.
2. From this folder, create and activate a virtual environment:

   ```powershell
   py -3.12 -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. Install the application packages:

   ```powershell
   pip install -r requirements.txt
   ```

4. Make sure `.env` contains a strong `SECRET_KEY`.
5. Start the app:

   ```powershell
   uvicorn main:app --reload
   ```

6. Open `http://127.0.0.1:8000`.

The `run-nutritrack.cmd` launcher can also start the app. It uses Python 3.12 when it is installed and otherwise uses the local Codex runtime when available.

## API

The interactive API documentation is available at `http://127.0.0.1:8000/docs` while the app is running.

| Endpoint | Purpose |
| --- | --- |
| `POST /auth/register` | Create an account |
| `POST /auth/login` | Receive a JWT access token |
| `GET /auth/me` | Read the signed-in user |
| `GET/PUT /api/profile` | Read or save daily targets |
| `GET/POST /api/meals` | List or add meals for a day |
| `DELETE /api/meals/{meal_id}` | Remove a meal |
| `PUT /api/water` | Set water intake for a day |
| `GET /api/dashboard` | Read the daily nutrition summary |
| `GET /api/coach` | Read calorie, macro, and goal-aware coaching estimates |

## Notes

- SQLite is used for local development. The database file is created automatically when the app starts.
- Passwords are stored as bcrypt hashes, never as plain text.
- The existing database remains intact when the new tracking tables are created.
- Coach estimates are for adults and educational use only. They are not medical advice or a replacement for care from a clinician or dietitian.
