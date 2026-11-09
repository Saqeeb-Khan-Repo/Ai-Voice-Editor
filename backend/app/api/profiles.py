import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.profile import ReciterProfile
from app.schemas.profile import (
    ReciterProfileCreate,
    ReciterProfileResponse,
    ProfileListResponse,
)

router = APIRouter(prefix="/profiles", tags=["Profiles"])

BUILTIN_PROFILES = [
    {
        "id": "builtin_studio_master",
        "name": "Studio Master (Recommended)",
        "description": "Full studio-grade polish: Auto-Tune pitch snapping, warm analog echo, 320 Hz boxiness cut, 10 kHz air sparkle, and broadcast loudness (-14 LUFS).",
        "is_builtin": True,
        "vocal_type": "all",
        "settings": {
            "preset": "studio_naat",
            "autotune_enabled": True,
            "autotune_strength": 0.65,
            "autotune_scale": "chromatic",
            "tube_saturation_enabled": True,
            "tube_warmth": 0.35,
            "doubler_enabled": False,
            "doubler_mix": 0.0,
            "echo_enabled": True,
            "echo_amount": 0.15,
            "echo_delay_ms": 240.0,
            "echo_feedback": 0.28,
            "reverb_amount": 0.15,
            "noise_reduction_strength": 0.65,
            "target_lufs": -14.0,
        },
    },
    {
        "id": "builtin_maqam_classical",
        "name": "Maqam Classical (Traditional & Soulful)",
        "description": "Classical Arabic & Urdu spiritual odes (Qasida Burda style). Bayati scale snapping, warm tube saturation, and acoustic chamber acoustics.",
        "is_builtin": True,
        "vocal_type": "classical",
        "settings": {
            "preset": "maqam_classical",
            "autotune_enabled": True,
            "autotune_strength": 0.40,
            "autotune_scale": "bayati",
            "tube_saturation_enabled": True,
            "tube_warmth": 0.45,
            "doubler_enabled": False,
            "doubler_mix": 0.0,
            "echo_enabled": True,
            "echo_amount": 0.10,
            "echo_delay_ms": 260.0,
            "echo_feedback": 0.22,
            "reverb_amount": 0.18,
            "noise_reduction_strength": 0.55,
            "target_lufs": -15.0,
        },
    },
    {
        "id": "builtin_modern_nasheed",
        "name": "Modern Nasheed Studio (Owais / Al-Afasy Style)",
        "description": "Contemporary studio vocal production with chromatic pitch snap, lush stereo vocal doubler/acapella width, 240ms ping-pong echo, and crisp 12kHz air.",
        "is_builtin": True,
        "vocal_type": "modern",
        "settings": {
            "preset": "modern_nasheed",
            "autotune_enabled": True,
            "autotune_strength": 0.75,
            "autotune_scale": "chromatic",
            "tube_saturation_enabled": True,
            "tube_warmth": 0.40,
            "doubler_enabled": True,
            "doubler_mix": 0.24,
            "doubler_width": 0.90,
            "echo_enabled": True,
            "echo_amount": 0.16,
            "echo_delay_ms": 240.0,
            "echo_feedback": 0.26,
            "reverb_amount": 0.16,
            "noise_reduction_strength": 0.60,
            "target_lufs": -14.0,
        },
    },
    {
        "id": "builtin_jalsa_live",
        "name": "Jalsa & Mehfil Live Master",
        "description": "Engineered for high-energy live gatherings, mosque microphones, and conferences. Aggressive background crowd noise gate, fast vocal compression, and peak limiting.",
        "is_builtin": True,
        "vocal_type": "live",
        "settings": {
            "preset": "jalsa_live",
            "autotune_enabled": True,
            "autotune_strength": 0.70,
            "autotune_scale": "chromatic",
            "tube_saturation_enabled": True,
            "tube_warmth": 0.30,
            "doubler_enabled": False,
            "doubler_mix": 0.0,
            "echo_enabled": True,
            "echo_amount": 0.18,
            "echo_delay_ms": 220.0,
            "echo_feedback": 0.32,
            "reverb_amount": 0.12,
            "noise_reduction_strength": 0.75,
            "target_lufs": -13.5,
        },
    },
    {
        "id": "builtin_deep_baritone",
        "name": "Deep Baritone (Low-End Authority)",
        "description": "Tailored for low-register reciters: 75Hz rumble cut, 300Hz boxy mud clearing, 3.5kHz articulation boost, and rich 50% tube warmth.",
        "is_builtin": True,
        "vocal_type": "baritone",
        "settings": {
            "preset": "deep_baritone",
            "autotune_enabled": True,
            "autotune_strength": 0.55,
            "autotune_scale": "chromatic",
            "tube_saturation_enabled": True,
            "tube_warmth": 0.50,
            "doubler_enabled": False,
            "doubler_mix": 0.0,
            "echo_enabled": True,
            "echo_amount": 0.14,
            "echo_delay_ms": 250.0,
            "echo_feedback": 0.28,
            "reverb_amount": 0.16,
            "noise_reduction_strength": 0.60,
            "target_lufs": -14.0,
        },
    },
    {
        "id": "builtin_youth_vocal",
        "name": "Youth & High-Register Polish",
        "description": "Tailored for high-pitched reciters: 450Hz boxy cut, 220Hz fundamental warmth, harsh 4.2kHz sibilance taming, and fast smooth autotune.",
        "is_builtin": True,
        "vocal_type": "tenor",
        "settings": {
            "preset": "youth_vocal",
            "autotune_enabled": True,
            "autotune_strength": 0.65,
            "autotune_scale": "chromatic",
            "tube_saturation_enabled": True,
            "tube_warmth": 0.45,
            "doubler_enabled": False,
            "doubler_mix": 0.0,
            "echo_enabled": True,
            "echo_amount": 0.12,
            "echo_delay_ms": 230.0,
            "echo_feedback": 0.24,
            "reverb_amount": 0.14,
            "noise_reduction_strength": 0.55,
            "target_lufs": -14.5,
        },
    },
]

@router.get("", response_model=ProfileListResponse)
def list_profiles(db: Session = Depends(get_db)):
    """Lists built-in profiles and user-created personalized profiles."""
    user_profiles = db.query(ReciterProfile).order_by(ReciterProfile.created_at.desc()).all()
    user_list = [p.to_dict() for p in user_profiles]

    all_profiles = BUILTIN_PROFILES + user_list
    return ProfileListResponse(
        total=len(all_profiles),
        profiles=all_profiles
    )

@router.post("", response_model=ReciterProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: ReciterProfileCreate,
    db: Session = Depends(get_db)
):
    """Saves a new personalized reciter profile."""
    profile_id = str(uuid.uuid4())
    record = ReciterProfile(
        id=profile_id,
        name=payload.name,
        description=payload.description,
        is_builtin=False,
        vocal_type=payload.vocal_type,
        settings=payload.settings,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record.to_dict()

@router.get("/{profile_id}", response_model=ReciterProfileResponse)
def get_profile(profile_id: str, db: Session = Depends(get_db)):
    """Retrieves a single profile by ID."""
    for b in BUILTIN_PROFILES:
        if b["id"] == profile_id:
            return b

    user_p = db.query(ReciterProfile).filter(ReciterProfile.id == profile_id).first()
    if not user_p:
        raise HTTPException(status_code=404, detail="Profile not found")
    return user_p.to_dict()

@router.delete("/{profile_id}", status_code=status.HTTP_200_OK)
def delete_profile(profile_id: str, db: Session = Depends(get_db)):
    """Deletes a custom user profile."""
    for b in BUILTIN_PROFILES:
        if b["id"] == profile_id:
            raise HTTPException(status_code=400, detail="Cannot delete built-in studio profiles.")

    user_p = db.query(ReciterProfile).filter(ReciterProfile.id == profile_id).first()
    if not user_p:
        raise HTTPException(status_code=404, detail="Profile not found")

    db.delete(user_p)
    db.commit()
    return {"message": "Profile deleted successfully", "id": profile_id}
