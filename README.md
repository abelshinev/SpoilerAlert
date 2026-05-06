# Spoiler Alert Backend

This directory contains the FastAPI backend for the Spoiler Alert project. 
It serves as the central API, handling client requests, managing the database, and integrating the food spoilage machine learning pipeline to analyze sticker images and estimate remaining shelf life.

To run this project run 

```bash
    pip install -r requirements.txt
```

And then run the server:

```bash
    uvicorn app.main:app --reload
```
