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



def is_same_product_image(img_path1, img_path2, threshold=4):
    """
    Determines if two product images are visually identical or nearly identical.

    Parameters:
        img_path1 (str): Path to the first product image.
        img_path2 (str): Path to the second product image.
        threshold (int): Hamming distance threshold for similarity (lower = stricter).

    Returns:
        bool: True if the images are visually identical products, False otherwise.
    """
    try:
        img1 = Image.open(img_path1).convert("RGB")
        img2 = Image.open(img_path2).convert("RGB")

        hash1 = imagehash.phash(img1)
        hash2 = imagehash.phash(img2)

        distance = hash1 - hash2
        return distance <= threshold, distance
    except Exception as e:
        print(f"Error comparing product images: {e}")
        return False


if __name__ == "__main__":
    path1 = "/home/viktoria/Downloads/images/89295.png"
    path2 = "/home/viktoria/Downloads/images/12596.png"
    path3 = "/home/viktoria/Downloads/images/99840.png"
    issame, distance = is_same_product_image(path1, path2)
    print(distance)
    issame, distance = is_same_product_image(path1, path3)
    print(distance)
    issame, distance = is_same_product_image(path2, path3)
    print(distance)