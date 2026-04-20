"""Smoke test: toàn bộ data pipeline comment → CSV → priority → re-prepare → OBS."""

from __future__ import annotations

import sys
import types
import tempfile
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# --- Stub tkinter trước khi import bất kỳ UI module nào ---
for _mod in [
    "tkinter", "tkinter.ttk", "tkinter.messagebox",
    "tkinter.filedialog", "tkinter.font", "tkinter.scrolledtext",
]:
    sys.modules.setdefault(_mod, types.ModuleType(_mod))

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
_errors: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  [{PASS}] {name}")
    else:
        msg = f"  [{FAIL}] {name}" + (f" — {detail}" if detail else "")
        print(msg)
        _errors.append(name)


def section(title: str) -> None:
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")


# ─────────────────────────────────────────────────────────────────────────────
# Setup: brand temp dir + fake video files
# ─────────────────────────────────────────────────────────────────────────────

def make_fake_video(folder: Path, name: str) -> Path:
    p = folder / name
    p.write_bytes(b"\x00" * 16)  # dummy file
    return p


def setup_brand(tmp: Path) -> tuple[str, Path, Path]:
    """Return (brand_id, rotate_folder, qa_folder)."""
    brand_id = "smoke_brand"
    rotate_folder = tmp / "rotate"
    qa_folder = tmp / "qa"
    rotate_folder.mkdir()
    qa_folder.mkdir()

    for i in range(1, 4):
        make_fake_video(rotate_folder, f"product{i}.mp4")
    for i in range(1, 3):
        make_fake_video(qa_folder, f"qa{i}.mp4")

    # Point brand data dir to tmp
    os.environ["BRAND_DATA_ROOT"] = str(tmp / "brands")
    return brand_id, rotate_folder, qa_folder


# ─────────────────────────────────────────────────────────────────────────────
# Section 1: CommentVideoMapper — CSV generation + matching
# ─────────────────────────────────────────────────────────────────────────────

def test_csv_matching(brand_id: str, rotate_folder: Path, qa_folder: Path) -> tuple[list[dict], list[dict]]:
    section("1. CommentVideoMapper — CSV generation + matching")

    from features.livestream.application.comment_video_mapper import CommentVideoMapper

    mapper = CommentVideoMapper()

    # Fake catalogs
    rotate_catalog = [
        {"id": "V0001", "path": str(rotate_folder / "product1.mp4")},
        {"id": "V0002", "path": str(rotate_folder / "product2.mp4")},
        {"id": "V0003", "path": str(rotate_folder / "product3.mp4")},
    ]
    qa_catalog = [
        {"id": "QA0001", "path": str(qa_folder / "qa1.mp4")},
        {"id": "QA0002", "path": str(qa_folder / "qa2.mp4")},
    ]

    # Generate rotate CSV
    rotate_csv = mapper.ensure_mapping_csv(brand_id, rotate_catalog)
    check("ensure_mapping_csv tạo file", rotate_csv.exists())

    # Generate QA CSV
    qa_csv = mapper.ensure_qa_mapping_csv(brand_id, qa_catalog)
    check("ensure_qa_mapping_csv tạo file", qa_csv.exists())

    # Ghi keywords vào CSV thủ công
    import csv
    with rotate_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "name", "description"])
        w.writeheader()
        w.writerows([
            {"id": "V0001", "name": "product1.mp4", "description": "sua tuoi vinamilk"},
            {"id": "V0002", "name": "product2.mp4", "description": "nuoc cam"},
            {"id": "V0003", "name": "product3.mp4", "description": "banh quy"},
        ])

    with qa_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["STT", "Câu hỏi", "Trả lời"])
        w.writeheader()
        w.writerows([
            {"STT": "1", "Câu hỏi": "giao hang bao lau", "Trả lời": "3-5 ngay"},
            {"STT": "2", "Câu hỏi": "doi tra hang the nao", "Trả lời": "7 ngay"},
        ])

    # Test rotate match ("sua"/"tuoi" là stop words, dùng "vinamilk" để match)
    vid = mapper.resolve_video_id_from_comments(["cho toi vinamilk di"], rotate_csv)
    check("rotate: match 'vinamilk' → V0001", vid == "V0001", f"got {vid}")

    vid2 = mapper.resolve_video_id_from_comments(["nuoc cam ep"], rotate_csv)
    check("rotate: match 'nuoc cam' → V0002", vid2 == "V0002", f"got {vid2}")

    # Test QA match
    qa_vid = mapper.resolve_qa_video_id_from_comments(
        ["giao hang mat bao lau"], qa_csv, qa_catalog
    )
    check("QA: match 'giao hang' → QA0001", qa_vid == "QA0001", f"got {qa_vid}")

    qa_vid2 = mapper.resolve_qa_video_id_from_comments(
        ["doi tra hang duoc khong"], qa_csv, qa_catalog
    )
    check("QA: match 'doi tra hang' → QA0002", qa_vid2 == "QA0002", f"got {qa_vid2}")

    # No match
    no_match = mapper.resolve_video_id_from_comments(["xin chao ban"], rotate_csv)
    check("rotate: no match → None", no_match is None, f"got {no_match}")

    return rotate_catalog, qa_catalog


# ─────────────────────────────────────────────────────────────────────────────
# Section 2: OBSService — queue + priority + re-prepare
# ─────────────────────────────────────────────────────────────────────────────

def make_mock_client() -> MagicMock:
    client = MagicMock()
    client.connected = True
    client.get_media_status.return_value = {"state": "playing", "duration": 60000, "cursor": 1000}
    return client


def test_obs_service_queue(brand_id: str, rotate_catalog: list[dict], qa_catalog: list[dict]) -> None:
    section("2. OBSService — priority queue + re-prepare logic")

    from features.obs.application.service import OBSService

    svc = OBSService(brand_id)

    # Inject fake video lists trực tiếp (bypass file import)
    with svc._lock:
        svc._import_queue = [
            {**item, "cooldown_override_seconds": None, "last_played_at": None, "blocked_until": 0.0}
            for item in rotate_catalog
        ]
        svc._qa_queue = [
            {**item, "cooldown_override_seconds": None, "last_played_at": None, "blocked_until": 0.0}
            for item in qa_catalog
        ]
        svc._id_counter = 3
        svc._qa_id_counter = 2
        svc._sync_ready_queue_locked()

    check("import_queue có 3 rotate videos", len(svc._import_queue) == 3)
    check("qa_queue có 2 QA videos", len(svc._qa_queue) == 2)

    # Priority rotate
    svc.prioritize_video_by_id("V0003")
    with svc._lock:
        top = svc._priority_ids[0] if svc._priority_ids else None
    check("prioritize V0003 → top of _priority_ids", top == "V0003", f"got {top}")

    picked = svc._next_from_play_queue()
    check("_pick_next picks V0003 (priority) first", picked and picked.get("id") == "V0003", f"got {picked}")
    check("_priority_ids cleared after pick", "V0003" not in svc._priority_ids)

    # Priority QA
    svc.prioritize_video_by_id("QA0001")
    qa_picked = svc._next_from_play_queue()
    check("_pick_next picks QA0001 (priority QA)", qa_picked and qa_picked.get("id") == "QA0001", f"got {qa_picked}")

    # _should_reprepare_standby_locked
    with svc._lock:
        svc._slots["B"] = {
            "file": "/path/product1.mp4",
            "item": {"id": "V0001"},
            "started": False,
            "prepared": True,
        }
        svc._priority_ids = ["V0002"]

    with svc._lock:
        should = svc._should_reprepare_standby_locked("B")
    check("_should_reprepare: V0002 priority ≠ V0001 prepared → True", should)

    with svc._lock:
        svc._priority_ids = ["V0001"]  # same as prepared
        should_not = svc._should_reprepare_standby_locked("B")
    check("_should_reprepare: same id → False", not should_not)

    with svc._lock:
        svc._priority_ids = []
        should_empty = svc._should_reprepare_standby_locked("B")
    check("_should_reprepare: no priority → False", not should_empty)

    # _reprepare_standby_if_needed (mock OBS client)
    svc.client = make_mock_client()
    cfg = MagicMock()
    cfg.scene_name = "Scene"
    cfg.source_a_name = "VideoA"
    cfg.source_b_name = "VideoB"

    with svc._lock:
        svc._slots["A"] = {"file": "", "item": None, "started": True, "prepared": False}
        svc._slots["B"] = {
            "file": str(rotate_catalog[0]["path"]),
            "item": {**svc._import_queue[0]},
            "started": False,
            "prepared": True,
        }
        svc._priority_ids = ["V0002"]

    svc._reprepare_standby_if_needed(cfg, "B")
    new_prepared_id = (svc._slots["B"]["item"] or {}).get("id")
    check("_reprepare: standby replaced V0001 → V0002", new_prepared_id == "V0002", f"got {new_prepared_id}")
    check("V0001 vẫn còn trong _import_queue", any(i["id"] == "V0001" for i in svc._import_queue))

    # QA re-prepare
    with svc._lock:
        svc._slots["B"] = {
            "file": str(rotate_catalog[1]["path"]),
            "item": {**svc._import_queue[1]},
            "started": False,
            "prepared": True,
        }
        svc._priority_ids = ["QA0002"]

    svc._reprepare_standby_if_needed(cfg, "B")
    qa_prepared_id = (svc._slots["B"]["item"] or {}).get("id")
    check("_reprepare QA: standby replaced rotate → QA0002", qa_prepared_id == "QA0002", f"got {qa_prepared_id}")


# ─────────────────────────────────────────────────────────────────────────────
# Section 3: Full pipeline — comment → enqueue → priority
# ─────────────────────────────────────────────────────────────────────────────

def test_full_pipeline(brand_id: str, rotate_catalog: list[dict], qa_catalog: list[dict]) -> None:
    section("3. Full pipeline — comment → CSV → enqueue priority")

    from features.obs.application import public_api as api
    from features.livestream.application.comment_switch_service import CommentSwitchService
    from features.livestream.application.ocr import OCRComment

    # Inject svc vào singleton để test
    svc = api.get_obs_service(brand_id)
    with svc._lock:
        svc._import_queue = [
            {**item, "cooldown_override_seconds": None, "last_played_at": None, "blocked_until": 0.0}
            for item in rotate_catalog
        ]
        svc._qa_queue = [
            {**item, "cooldown_override_seconds": None, "last_played_at": None, "blocked_until": 0.0}
            for item in qa_catalog
        ]
        svc._id_counter = 3
        svc._qa_id_counter = 2
        svc._priority_ids = []
        svc._sync_ready_queue_locked()

    css = CommentSwitchService()

    comment = OCRComment(
        author="user1",
        content_raw="cho toi hoi giao hang mat bao lau vay",
        content_normalized="cho toi hoi giao hang mat bao lau vay",
        timestamp="2024-01-01T00:00:00",
        confidence=0.95,
    )

    result = css.process_ocr_comment(brand_id=brand_id, comment=comment)
    check("QA comment → matched_qa=True", result.get("matched_qa") is True, str(result))
    check("QA comment → matched_video_id=QA0001", result.get("matched_video_id") == "QA0001", str(result.get("matched_video_id")))
    check("QA comment → enqueued=True", result.get("enqueued") is True)

    with svc._lock:
        pids = list(svc._priority_ids)
    check("QA0001 vào _priority_ids", "QA0001" in pids, f"priority_ids={pids}")

    # Rotate comment
    svc._priority_ids.clear()
    comment2 = OCRComment(
        author="user2",
        content_raw="nuoc cam ep tuoi ngon qua",
        content_normalized="nuoc cam ep tuoi ngon qua",
        timestamp="2024-01-01T00:00:01",
        confidence=0.95,
    )
    result2 = css.process_ocr_comment(brand_id=brand_id, comment=comment2)
    check("Rotate comment → matched_qa=False", result2.get("matched_qa") is False, str(result2))
    check("Rotate comment → matched_video_id=V0002", result2.get("matched_video_id") == "V0002", str(result2.get("matched_video_id")))


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    print("\n" + "="*60)
    print("  SMOKE TEST — Data Pipeline")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        brand_id, rotate_folder, qa_folder = setup_brand(tmp)

        rotate_catalog, qa_catalog = test_csv_matching(brand_id, rotate_folder, qa_folder)
        test_obs_service_queue(brand_id, rotate_catalog, qa_catalog)
        test_full_pipeline(brand_id, rotate_catalog, qa_catalog)

    print("\n" + "="*60)
    if _errors:
        print(f"  FAILED: {len(_errors)} test(s)")
        for e in _errors:
            print(f"    ✗ {e}")
        sys.exit(1)
    else:
        print(f"  ALL PASSED")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
