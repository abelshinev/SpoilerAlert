# Spoiler Alert Backend

This directory contains the FastAPI backend for the Spoiler Alert project. 
It serves as the central API, handling client requests, managing the database, and integrating the food spoilage machine learning pipeline to analyze sticker images and estimate remaining shelf life.

## Tech Stack
- **Framework:** FastAPI
- **Server:** Uvicorn
- **Database:** SQLite (with `aiosqlite` for asynchronous operations)
- **Machine Learning & Image Processing:** OpenCV, NumPy, SciPy, Scikit-learn
- **Integrations:** Firebase Admin SDK (for notifications/auth)

## System Architecture (Abstract)
- **API Layer:** Exposes RESTful endpoints for the frontend application to interact with (e.g., adding items, fetching inventory, uploading sticker images).
- **Service Layer:** Contains the core business logic, including the orchestration of the ML pipeline for image analysis and spoilage prediction.
- **Data Access Layer:** Manages persistent storage of users, tracked food items, and application state using an asynchronous SQLite database.
- **Integration Layer:** Connects to external services like Firebase for pushing alerts and notifications to users.

To run this project run 

```bash
    pip install -r requirements.txt
```

And then run the server:

```bash
    uvicorn app.main:app --reload
```
