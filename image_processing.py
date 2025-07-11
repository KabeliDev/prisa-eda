from PIL import Image
import imagehash

def are_images_similar(image_path1, image_path2, threshold=5):
    """
    Compare two images using perceptual hash (pHash).

    Parameters:
        image_path1 (str): Path to the first image.
        image_path2 (str): Path to the second image.
        threshold (int): Maximum Hamming distance to consider images similar.

    Returns:
        bool: True if images are similar (distance <= threshold), False otherwise.
        int: The Hamming distance between the hashes.
    """
    try:
        hash1 = imagehash.phash(Image.open(image_path1))
        hash2 = imagehash.phash(Image.open(image_path2))
    except Exception as e:
        print(f"Error loading or processing images: {e}")
        return False, None

    distance = hash1 - hash2
    return distance <= threshold, distance
