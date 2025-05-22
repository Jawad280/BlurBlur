import opennsfw2 as n2

async def process_image(image_path: str) -> float:
    try:
        score = n2.predict_image(image_path)
        return score
    except Exception as e:
        print(f"[NSFW DETECTION ERROR] {e}")
        return 0.0