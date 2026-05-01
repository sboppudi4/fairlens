"""Seed the database with a demo user, dataset (Adult Income), and a queued audit.

Run inside the backend container after `alembic upgrade head`:

    docker compose exec backend python -m scripts.seed_demo

Steps:
  1. Create user demo@fairlens.dev / fairlens2026 if missing
  2. Download the Adult Income dataset from UCI (or a vendored fallback)
  3. Train an XGBoost model on it; generate predictions on the full set
  4. Build a CSV with the original columns + a 'prediction' column
  5. Upload to MinIO and create the Dataset record
  6. Create an Audit record analyzing 'sex' and 'race' as sensitive attributes
  7. Queue the Celery task to run the audit
"""
from __future__ import annotations

import io
import json
import sys
import urllib.request
import uuid

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from xgboost import XGBClassifier

from app.config import get_settings
from app.core.security import hash_password
from app.core.storage import ensure_bucket, get_client

# ---------------------------------------------------------------------------
# Adult Income dataset
# UCI ML Repository: https://archive.ics.uci.edu/ml/datasets/adult
# ---------------------------------------------------------------------------

ADULT_TRAIN_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data"
ADULT_COLS = [
    "age", "workclass", "fnlwgt", "education", "education_num",
    "marital_status", "occupation", "relationship", "race", "sex",
    "capital_gain", "capital_loss", "hours_per_week", "native_country", "income",
]


def _sync_db_url() -> str:
    return get_settings().DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://")


def _engine() -> Engine:
    return create_engine(_sync_db_url(), pool_pre_ping=True)


def _download_adult() -> pd.DataFrame:
    print("[seed] downloading Adult Income from UCI...")
    try:
        req = urllib.request.Request(ADULT_TRAIN_URL, headers={"User-Agent": "fairlens-seed/0.1"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
    except Exception as e:
        print(f"[seed] download failed ({e}); using a synthetic fallback so the demo still runs.")
        return _synthetic_adult()

    df = pd.read_csv(io.StringIO(raw), header=None, names=ADULT_COLS, skipinitialspace=True, na_values="?")
    df = df.dropna().reset_index(drop=True)
    return df


def _synthetic_adult(n: int = 5000) -> pd.DataFrame:
    """Fallback synthetic dataset with intentional bias on `sex` and `race`."""
    rng = np.random.default_rng(42)
    sex = rng.choice(["Male", "Female"], size=n, p=[0.6, 0.4])
    race = rng.choice(["White", "Black", "Asian-Pac-Islander", "Other"], size=n, p=[0.7, 0.15, 0.1, 0.05])
    age = rng.integers(20, 70, size=n)
    education_num = rng.integers(6, 17, size=n)
    hours_per_week = rng.integers(20, 80, size=n)
    # Income probability has bias by sex and race
    base = 0.05 + 0.02 * (age - 20) / 50 + 0.04 * (education_num - 6) / 10 + 0.02 * (hours_per_week - 20) / 60
    base = np.clip(base, 0, 0.9)
    sex_bonus = np.where(sex == "Male", 0.15, 0.0)
    race_bonus = np.where(race == "White", 0.10, np.where(race == "Asian-Pac-Islander", 0.08, 0.0))
    p = np.clip(base + sex_bonus + race_bonus, 0.01, 0.95)
    income = rng.binomial(1, p)
    income_str = np.where(income == 1, ">50K", "<=50K")
    return pd.DataFrame({
        "age": age,
        "workclass": "Private",
        "fnlwgt": rng.integers(50000, 500000, size=n),
        "education": "Bachelors",
        "education_num": education_num,
        "marital_status": "Married-civ-spouse",
        "occupation": "Prof-specialty",
        "relationship": "Husband",
        "race": race,
        "sex": sex,
        "capital_gain": 0,
        "capital_loss": 0,
        "hours_per_week": hours_per_week,
        "native_country": "United-States",
        "income": income_str,
    })


def _train_and_predict(df: pd.DataFrame) -> pd.DataFrame:
    print("[seed] training XGBoost...")
    df = df.copy()
    # Encode label
    df["income_bin"] = (df["income"].astype(str).str.strip().str.replace(".", "", regex=False) == ">50K").astype(int)
    # Simple categorical encoding via factorize for the demo
    feature_cols = ["age", "education_num", "hours_per_week", "capital_gain", "capital_loss", "fnlwgt"]
    cat_cols = ["workclass", "marital_status", "occupation", "relationship", "race", "sex", "native_country", "education"]
    for c in cat_cols:
        df[f"{c}_enc"], _ = pd.factorize(df[c].astype(str))
        feature_cols.append(f"{c}_enc")

    X = df[feature_cols].fillna(0).to_numpy()
    y = df["income_bin"].to_numpy()
    X_train, _X_test, y_train, _y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        random_state=42,
        n_jobs=2,
        eval_metric="logloss",
        verbosity=0,
    )
    model.fit(X_train, y_train)
    df["prediction_bin"] = model.predict(X)
    df["prediction"] = np.where(df["prediction_bin"] == 1, ">50K", "<=50K")
    return df.drop(columns=["income_bin", "prediction_bin"] + [c for c in df.columns if c.endswith("_enc")])


def main() -> int:
    settings = get_settings()
    eng = _engine()

    # 1. Demo user
    print("[seed] ensuring demo user exists")
    with eng.begin() as conn:
        existing = conn.execute(
            text("SELECT id FROM users WHERE email = :e"), {"e": "demo@fairlens.dev"}
        ).scalar()
        if existing:
            user_id = existing
            print(f"[seed]   user already present: {user_id}")
        else:
            user_id = uuid.uuid4()
            conn.execute(
                text(
                    "INSERT INTO users (id, email, hashed_password, full_name, is_active, is_verified) "
                    "VALUES (:id, :e, :p, :n, TRUE, TRUE)"
                ),
                {
                    "id": user_id,
                    "e": "demo@fairlens.dev",
                    "p": hash_password("fairlens2026"),
                    "n": "FairLens Demo",
                },
            )
            print(f"[seed]   created user: demo@fairlens.dev / fairlens2026 ({user_id})")

    # 2-4. Build dataset
    df_raw = _download_adult()
    df = _train_and_predict(df_raw)
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    print(f"[seed] dataset shape: {df.shape} | csv size: {len(csv_bytes)} bytes")

    # 5. Upload to MinIO
    print("[seed] uploading to object storage")
    ensure_bucket()
    dataset_id = uuid.uuid4()
    s3_key = f"datasets/{user_id}/{dataset_id}/adult_income_with_predictions.csv"
    client = get_client()
    client.put_object(
        Bucket=settings.AWS_BUCKET_NAME,
        Key=s3_key,
        Body=csv_bytes,
        ContentType="text/csv",
    )

    # 5b. Create dataset row
    column_types = {c: "numeric" if pd.api.types.is_numeric_dtype(df[c]) else "categorical" for c in df.columns}
    with eng.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO datasets (id, user_id, name, description, filename, s3_key, "
                "row_count, column_names, column_types, file_size_bytes, status) "
                "VALUES (:id, :uid, :name, :desc, :fn, :sk, :rc, CAST(:cn AS json), CAST(:ct AS json), :sz, 'ready')"
            ),
            {
                "id": dataset_id,
                "uid": user_id,
                "name": "Adult Income (UCI) — demo",
                "desc": "Classic fairness benchmark with known biases against women and certain racial groups.",
                "fn": "adult_income_with_predictions.csv",
                "sk": s3_key,
                "rc": int(df.shape[0]),
                "cn": json.dumps(list(df.columns)),
                "ct": json.dumps(column_types),
                "sz": len(csv_bytes),
            },
        )
    print(f"[seed] dataset created: {dataset_id}")

    # 6. Create audit row
    audit_id = uuid.uuid4()
    config = {
        "label_column": "income",
        "prediction_column": "prediction",
        "sensitive_attributes": ["sex", "race"],
        "positive_label": ">50K",
        "favorable_prediction": ">50K",
        "model_type": "binary_classification",
    }
    with eng.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO audits (id, user_id, dataset_id, name, description, config, status) "
                "VALUES (:id, :uid, :did, :n, :d, CAST(:c AS json), 'pending')"
            ),
            {
                "id": audit_id,
                "uid": user_id,
                "did": dataset_id,
                "n": "Adult Income — demo audit",
                "d": "Audit XGBoost predictions on Adult Income, analyzing sex and race.",
                "c": json.dumps(config),
            },
        )
    print(f"[seed] audit created: {audit_id}")

    # 7. Queue Celery task
    from app.tasks.audit_tasks import run_audit  # imported here to avoid Celery startup cost on dry-run

    task = run_audit.delay(str(audit_id))
    with eng.begin() as conn:
        conn.execute(
            text("UPDATE audits SET task_id = :tid WHERE id = :id"),
            {"tid": task.id, "id": audit_id},
        )
    print(f"[seed] queued Celery task: {task.id}")
    print("[seed] done. Login at http://localhost:5173 with demo@fairlens.dev / fairlens2026")
    print(f"[seed] poll status: GET /api/v1/audits/{audit_id}/status")
    return 0


if __name__ == "__main__":
    sys.exit(main())
