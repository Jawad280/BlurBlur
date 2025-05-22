import opennsfw2 as n2

async def process_video(video_path: str) -> float:
    try:
        elapsed, probabilities = n2.predict_video_frames(video_path)
        return max(probabilities) if probabilities else 0.0
    except Exception as e:
        print(f"[NSFW VIDEO ERROR] {e}")
        return 0.0
