from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from flask import Flask, jsonify, render_template, request

from generator.review import service
from generator.review.queue import ReviewStatus


def create_app(root: Path) -> Flask:
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(Path(__file__).parent / "static"),
    )
    app.config["PROJECT_ROOT"] = root

    def cfg() -> Dict[str, Any]:
        return service.load_generator_config(root)

    @app.get("/")
    def index():
        return render_template("review.html")

    @app.get("/api/batches")
    def api_batches():
        return jsonify(service.list_batches(root, cfg()))

    @app.get("/api/candidates")
    def api_candidates():
        batch = request.args.get("batch") or None
        status = request.args.get("status") or None
        rows = service.list_candidates(root, cfg(), batch=batch)
        if status:
            rows = [r for r in rows if r.get("review_status") == status]
        return jsonify(rows)

    @app.get("/api/candidate/<batch>/<filename>")
    def api_get_candidate(batch: str, filename: str):
        try:
            return jsonify(service.get_candidate(root, cfg(), batch, filename))
        except FileNotFoundError:
            return jsonify({"error": "not found"}), 404

    @app.put("/api/candidate/<batch>/<filename>")
    def api_save_candidate(batch: str, filename: str):
        body = request.get_json(force=True) or {}
        puzzle = body.get("puzzle")
        if not puzzle:
            return jsonify({"error": "missing puzzle"}), 400
        try:
            return jsonify(service.save_candidate(root, cfg(), batch, filename, puzzle))
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    @app.post("/api/review/<batch>/<filename>")
    def api_review(batch: str, filename: str):
        body = request.get_json(force=True) or {}
        status = body.get("status", ReviewStatus.PENDING.value)
        notes = body.get("notes", "")
        entry = service.set_review_status(root, cfg(), batch, filename, status, notes)
        return jsonify(entry)

    @app.post("/api/publish/<batch>/<filename>")
    def api_publish(batch: str, filename: str):
        try:
            out_path, puzzle_id = service.publish_staging_candidate(root, cfg(), batch, filename)
            return jsonify(
                {
                    "published_id": puzzle_id,
                    "published_path": str(out_path.relative_to(root)),
                }
            )
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    @app.post("/api/publish-batch")
    def api_publish_batch():
        body = request.get_json(force=True) or {}
        items = body.get("items")
        batch = body.get("batch") or None
        only_accepted = bool(body.get("only_accepted", True))
        skip_published = bool(body.get("skip_published", True))
        if not items and not batch:
            return jsonify({"error": "provide items or batch"}), 400
        result = service.publish_staging_batch(
            root,
            cfg(),
            items=items,
            batch=batch,
            only_accepted=only_accepted,
            skip_published=skip_published,
        )
        return jsonify(result)

    return app
