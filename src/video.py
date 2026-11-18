from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(tags=["video"])
VIDEOS = {"tears-of-steel": Path("data/video/tears_of_steel_720p.mov")}


@router.get("/video/{film_id}")
def video(film_id: str):
    path = VIDEOS.get(film_id)
    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail="video introuvable")
    return FileResponse(path, media_type="video/mp4")
