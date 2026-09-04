# Backend setup

The API stores completed predictions in MongoDB.

1. Install MongoDB Community locally, or create a MongoDB Atlas cluster.
2. Copy `.env.example` to `.env`.
3. Set `MONGODB_URI` in `.env` to the local or Atlas connection string.
4. Install Python dependencies and start the API:

```powershell
cd Backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

The API uses the `student_support` database and `predictions` collection by default. Override either with `MONGODB_DATABASE` or `MONGODB_COLLECTION`.

Useful checks:

- `GET http://127.0.0.1:8000/health` confirms MongoDB connectivity.
- `GET http://127.0.0.1:8000/history` returns saved predictions.
- `GET http://127.0.0.1:8000/docs` opens the interactive API docs.

The frontend should use `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000`.