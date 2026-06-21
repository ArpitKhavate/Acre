"""Arize model-monitoring feed (PRD section 4, Arize track).

Every detection carries a class + confidence; we log those to Arize so accuracy
and drift can be tracked across the demo run. Reads from the same `detections`
table the web app uses. No-ops with a clear message if the SDK/keys are missing.

    python -m cloud.integrations.arize_logger --farm demo-farm-1
"""
from __future__ import annotations

import argparse
import os

from sqlalchemy.orm import Session

from cloud.app import models
from cloud.app.db import SessionLocal

MODEL_ID = os.environ.get("ARIZE_MODEL_ID", "acre-plant-classifier")
MODEL_VERSION = os.environ.get("ARIZE_MODEL_VERSION", "0.1.0")


def _client():
    api_key = os.environ.get("ARIZE_API_KEY")
    space_id = os.environ.get("ARIZE_SPACE_ID")
    if not api_key or not space_id:
        return None, "ARIZE_API_KEY / ARIZE_SPACE_ID not set"
    try:
        from arize.api import Client

        return Client(space_id=space_id, api_key=api_key), None
    except Exception as exc:
        return None, f"arize SDK unavailable: {exc}"


def log_detections(db: Session, farm_id: str) -> int:
    client, err = _client()
    zone_ids = [z.id for z in db.query(models.Zone)
                .filter(models.Zone.farm_id == farm_id).all()]
    rows = (db.query(models.Detection)
            .filter(models.Detection.zone_id.in_(zone_ids)).all())

    if client is None:
        print(f"[arize] {err}; would have logged {len(rows)} predictions "
              f"(model={MODEL_ID} v{MODEL_VERSION}).")
        return 0

    from arize.utils.types import Environments, ModelTypes, Schema  # noqa
    import pandas as pd

    df = pd.DataFrame([{
        "prediction_id": r.id,
        "prediction_label": r.class_name,
        "confidence": r.confidence,
        "zone_id": r.zone_id,
        "crop_type": r.crop_type,
        "health_score": r.health_score,
        "captured_at": r.captured_at,
    } for r in rows])

    schema = Schema(
        prediction_id_column_name="prediction_id",
        prediction_label_column_name="prediction_label",
        feature_column_names=["zone_id", "crop_type", "health_score"],
    )
    client.log(
        dataframe=df, model_id=MODEL_ID, model_version=MODEL_VERSION,
        model_type=ModelTypes.SCORE_CATEGORICAL, environment=Environments.PRODUCTION,
        schema=schema,
    )
    print(f"[arize] logged {len(df)} predictions to {MODEL_ID} v{MODEL_VERSION}")
    return len(df)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--farm", default="demo-farm-1")
    args = ap.parse_args()
    db = SessionLocal()
    try:
        log_detections(db, args.farm)
    finally:
        db.close()


if __name__ == "__main__":
    main()
