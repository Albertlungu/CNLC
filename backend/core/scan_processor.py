"""
./backend/core/scan_processor.py

Async 3D video scan processing pipeline using COLMAP + OpenMVS.
Extracts frames from uploaded videos, runs Structure-from-Motion,
dense reconstruction, mesh generation, and exports GLB models.
"""

import json
import os
import random
import shutil
import subprocess
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from config.config import DATA_DIR, PROJECT_ROOT

SCANS_JSON = DATA_DIR / "scans.json"
SCANS_WORK_DIR = PROJECT_ROOT / "data" / "uploads" / "scans"
MEDIA_UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads" / "media"

# Allowed video formats for scanning
ALLOWED_SCAN_FORMATS = {".mp4", ".webm", ".mov", ".avi", ".mkv"}

# Frame extraction settings
FRAME_SAMPLE_INTERVAL = 10  # Extract every Nth frame
MAX_FRAMES = 200  # Cap total frames


def _ensure_dirs():
    os.makedirs(str(SCANS_WORK_DIR), exist_ok=True)
    os.makedirs(str(MEDIA_UPLOAD_DIR), exist_ok=True)


def _load_scans() -> list[dict]:
    try:
        with open(str(SCANS_JSON), "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_scans(scans: list[dict]) -> None:
    with open(str(SCANS_JSON), "w") as f:
        json.dump(scans, f, indent=4)


def _generate_id() -> int:
    return random.randint(10000000, 99999999)


def _get_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


def submit_scan(
    video_path: str, user_id: int, business_id: int, original_name: str = ""
) -> dict:
    """
    Queue a video scan for processing.
    Returns the scan entry with status 'processing'.
    """
    _ensure_dirs()

    scan_id = _generate_id()
    scan_dir = SCANS_WORK_DIR / str(scan_id)
    os.makedirs(str(scan_dir), exist_ok=True)

    # Move video to scan working directory
    ext = _get_extension(video_path)
    video_dest = scan_dir / f"input{ext}"
    shutil.move(video_path, str(video_dest))

    entry = {
        "scanId": scan_id,
        "businessId": business_id,
        "userId": user_id,
        "originalName": original_name,
        "status": "processing",
        "progress": "queued",
        "videoPath": str(video_dest),
        "outputPath": None,
        "mediaId": None,
        "error": None,
        "createdAt": datetime.utcnow().isoformat(),
        "completedAt": None,
    }

    scans = _load_scans()
    scans.append(entry)
    _save_scans(scans)

    # Start processing in background thread
    thread = threading.Thread(target=_process_scan, args=(scan_id,), daemon=True)
    thread.start()

    return entry


def _update_scan_status(scan_id: int, **kwargs) -> None:
    """Update scan entry fields."""
    scans = _load_scans()
    for s in scans:
        if s["scanId"] == scan_id:
            s.update(kwargs)
            break
    _save_scans(scans)


def _process_scan(scan_id: int) -> None:
    """
    Background processing pipeline:
    1. Extract frames from video using OpenCV
    2. Run COLMAP feature extraction + matching + sparse reconstruction
    3. Run COLMAP/OpenMVS dense reconstruction
    4. Generate mesh with OpenMVS
    5. Convert to GLB format using trimesh
    """
    try:
        scans = _load_scans()
        scan = None
        for s in scans:
            if s["scanId"] == scan_id:
                scan = s
                break

        if not scan:
            return

        scan_dir = Path(scan["videoPath"]).parent
        frames_dir = scan_dir / "frames"
        sparse_dir = scan_dir / "sparse"
        dense_dir = scan_dir / "dense"
        os.makedirs(str(frames_dir), exist_ok=True)
        os.makedirs(str(sparse_dir), exist_ok=True)
        os.makedirs(str(dense_dir), exist_ok=True)

        # ==================== Step 1: Extract frames ====================
        _update_scan_status(scan_id, progress="extracting_frames")

        try:
            import cv2
        except ImportError:
            _update_scan_status(
                scan_id,
                status="failed",
                error="OpenCV (cv2) is not installed. Install with: pip install opencv-python",
                completedAt=datetime.utcnow().isoformat(),
            )
            return

        cap = cv2.VideoCapture(scan["videoPath"])
        if not cap.isOpened():
            _update_scan_status(
                scan_id,
                status="failed",
                error="Could not open video file.",
                completedAt=datetime.utcnow().isoformat(),
            )
            return

        frame_count = 0
        saved_count = 0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # Dynamically calculate sample interval to stay under MAX_FRAMES
        interval = max(FRAME_SAMPLE_INTERVAL, total_frames // MAX_FRAMES + 1)

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_count % interval == 0 and saved_count < MAX_FRAMES:
                frame_path = frames_dir / f"frame_{saved_count:05d}.jpg"
                cv2.imwrite(str(frame_path), frame)
                saved_count += 1
            frame_count += 1

        cap.release()

        if saved_count < 3:
            _update_scan_status(
                scan_id,
                status="failed",
                error="Video too short. Need at least 3 usable frames.",
                completedAt=datetime.utcnow().isoformat(),
            )
            return

        # ==================== Step 2: COLMAP Feature Extraction ====================
        _update_scan_status(scan_id, progress="feature_extraction")

        colmap_db = scan_dir / "database.db"

        # Check if COLMAP is available
        colmap_cmd = shutil.which("colmap")
        if not colmap_cmd:
            _update_scan_status(
                scan_id,
                status="failed",
                error="COLMAP is not installed. Install it from https://colmap.github.io/",
                completedAt=datetime.utcnow().isoformat(),
            )
            return

        # Feature extraction
        result = subprocess.run(
            [
                colmap_cmd,
                "feature_extractor",
                "--database_path",
                str(colmap_db),
                "--image_path",
                str(frames_dir),
                "--ImageReader.single_camera",
                "1",
                "--SiftExtraction.use_gpu",
                "0",
            ],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode != 0:
            _update_scan_status(
                scan_id,
                status="failed",
                error=f"COLMAP feature extraction failed: {result.stderr[:500]}",
                completedAt=datetime.utcnow().isoformat(),
            )
            return

        # ==================== Step 3: Feature Matching ====================
        _update_scan_status(scan_id, progress="feature_matching")

        result = subprocess.run(
            [
                colmap_cmd,
                "sequential_matcher",
                "--database_path",
                str(colmap_db),
                "--SiftMatching.use_gpu",
                "0",
            ],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode != 0:
            _update_scan_status(
                scan_id,
                status="failed",
                error=f"COLMAP matching failed: {result.stderr[:500]}",
                completedAt=datetime.utcnow().isoformat(),
            )
            return

        # ==================== Step 4: Sparse Reconstruction ====================
        _update_scan_status(scan_id, progress="sparse_reconstruction")

        sparse_model_dir = sparse_dir / "0"
        os.makedirs(str(sparse_model_dir), exist_ok=True)

        result = subprocess.run(
            [
                colmap_cmd,
                "mapper",
                "--database_path",
                str(colmap_db),
                "--image_path",
                str(frames_dir),
                "--output_path",
                str(sparse_dir),
            ],
            capture_output=True,
            text=True,
            timeout=1200,
        )
        if result.returncode != 0:
            _update_scan_status(
                scan_id,
                status="failed",
                error=f"COLMAP reconstruction failed: {result.stderr[:500]}",
                completedAt=datetime.utcnow().isoformat(),
            )
            return

        # Find the actual model directory (COLMAP creates numbered subdirectories)
        model_dirs = [d for d in sparse_dir.iterdir() if d.is_dir()]
        if not model_dirs:
            _update_scan_status(
                scan_id,
                status="failed",
                error="COLMAP did not produce a reconstruction. Try a video with more overlap between frames.",
                completedAt=datetime.utcnow().isoformat(),
            )
            return

        sparse_model_dir = sorted(model_dirs)[0]

        # ==================== Step 5: Dense Reconstruction ====================
        _update_scan_status(scan_id, progress="dense_reconstruction")

        # Image undistorter
        result = subprocess.run(
            [
                colmap_cmd,
                "image_undistorter",
                "--image_path",
                str(frames_dir),
                "--input_path",
                str(sparse_model_dir),
                "--output_path",
                str(dense_dir),
                "--output_type",
                "COLMAP",
            ],
            capture_output=True,
            text=True,
            timeout=600,
        )

        # Dense stereo
        if result.returncode == 0:
            result = subprocess.run(
                [
                    colmap_cmd,
                    "patch_match_stereo",
                    "--workspace_path",
                    str(dense_dir),
                    "--PatchMatchStereo.geom_consistency",
                    "true",
                ],
                capture_output=True,
                text=True,
                timeout=1800,
            )

        # Dense fusion
        fused_ply = dense_dir / "fused.ply"
        if result.returncode == 0:
            result = subprocess.run(
                [
                    colmap_cmd,
                    "stereo_fusion",
                    "--workspace_path",
                    str(dense_dir),
                    "--output_path",
                    str(fused_ply),
                ],
                capture_output=True,
                text=True,
                timeout=600,
            )

        # ==================== Step 6: Mesh Generation ====================
        _update_scan_status(scan_id, progress="mesh_generation")

        # Try OpenMVS if available, otherwise use COLMAP's Poisson mesher
        openmvs_reconstruct = shutil.which("ReconstructMesh")

        mesh_ply = dense_dir / "mesh.ply"

        if fused_ply.exists():
            if openmvs_reconstruct:
                # Use OpenMVS for mesh reconstruction
                result = subprocess.run(
                    [openmvs_reconstruct, str(fused_ply), "-o", str(mesh_ply)],
                    capture_output=True,
                    text=True,
                    timeout=1200,
                )
            else:
                # Fall back to COLMAP Poisson meshing
                result = subprocess.run(
                    [
                        colmap_cmd,
                        "poisson_mesher",
                        "--input_path",
                        str(fused_ply),
                        "--output_path",
                        str(mesh_ply),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=600,
                )

        # ==================== Step 7: Convert to GLB ====================
        _update_scan_status(scan_id, progress="converting_to_glb")

        output_glb = MEDIA_UPLOAD_DIR / f"{uuid.uuid4().hex}.glb"

        try:
            import trimesh

            # Try to load the mesh (prefer textured mesh, then dense fused, then sparse)
            mesh_file = None
            for candidate in [mesh_ply, fused_ply]:
                if candidate.exists():
                    mesh_file = candidate
                    break

            if not mesh_file:
                _update_scan_status(
                    scan_id,
                    status="failed",
                    error="No mesh output produced. The video may not have sufficient overlap or detail.",
                    completedAt=datetime.utcnow().isoformat(),
                )
                return

            mesh = trimesh.load(str(mesh_file))
            mesh.export(str(output_glb), file_type="glb")

        except ImportError:
            _update_scan_status(
                scan_id,
                status="failed",
                error="trimesh is not installed. Install with: pip install trimesh",
                completedAt=datetime.utcnow().isoformat(),
            )
            return
        except Exception as e:
            _update_scan_status(
                scan_id,
                status="failed",
                error=f"GLB conversion failed: {str(e)[:300]}",
                completedAt=datetime.utcnow().isoformat(),
            )
            return

        # ==================== Step 8: Create Media Entry ====================
        _update_scan_status(scan_id, progress="finalizing")

        from backend.core.media_manager import _generate_id as gen_media_id
        from backend.core.media_manager import _load_media, _save_media

        media_entry = {
            "mediaId": gen_media_id(),
            "businessId": scan["businessId"],
            "uploadedByUserId": scan["userId"],
            "filename": output_glb.name,
            "originalName": f"3D Scan - {scan['originalName']}",
            "mediaType": "3d",
            "mimeType": "model/gltf-binary",
            "createdAt": datetime.utcnow().isoformat(),
            "fromScan": True,
            "scanId": scan_id,
        }

        media = _load_media()
        media.append(media_entry)
        _save_media(media)

        # Update scan as completed
        _update_scan_status(
            scan_id,
            status="completed",
            progress="done",
            outputPath=f"/uploads/media/{output_glb.name}",
            mediaId=media_entry["mediaId"],
            completedAt=datetime.utcnow().isoformat(),
        )

        # Clean up working directory (keep the GLB output)
        try:
            shutil.rmtree(str(scan_dir))
        except Exception:
            pass

    except subprocess.TimeoutExpired:
        _update_scan_status(
            scan_id,
            status="failed",
            error="Processing timed out. The video may be too long or complex.",
            completedAt=datetime.utcnow().isoformat(),
        )
    except Exception as e:
        _update_scan_status(
            scan_id,
            status="failed",
            error=f"Unexpected error: {str(e)[:500]}",
            completedAt=datetime.utcnow().isoformat(),
        )


def get_scan_status(scan_id: int) -> Optional[dict]:
    """Get the current status of a scan."""
    scans = _load_scans()
    for s in scans:
        if s["scanId"] == scan_id:
            return {
                "scanId": s["scanId"],
                "status": s["status"],
                "progress": s["progress"],
                "outputPath": s.get("outputPath"),
                "mediaId": s.get("mediaId"),
                "error": s.get("error"),
                "createdAt": s.get("createdAt"),
                "completedAt": s.get("completedAt"),
            }
    return None


def list_scans(business_id: int) -> list[dict]:
    """List all scans for a business."""
    scans = _load_scans()
    return [
        {
            "scanId": s["scanId"],
            "status": s["status"],
            "progress": s["progress"],
            "originalName": s.get("originalName", ""),
            "outputPath": s.get("outputPath"),
            "mediaId": s.get("mediaId"),
            "error": s.get("error"),
            "createdAt": s.get("createdAt"),
            "completedAt": s.get("completedAt"),
        }
        for s in scans
        if s["businessId"] == business_id
    ]
