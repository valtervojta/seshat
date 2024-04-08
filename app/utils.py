from hashlib import sha256


# noinspection InsecureHash
def get_file_hash(filepath):
    """
    Hashes a file using SHA256.

    Args:
        filepath (str): Path to the file to hash.

    Returns:
        str: The hexadecimal digest of the hashed file.
    """
    CHUNK_SIZE = 64 * 1024
    with open(filepath, "rb") as file:
        hasher = sha256()
        chunk_size = CHUNK_SIZE
        for chunk in iter(lambda: file.read(chunk_size), b""):
            hasher.update(chunk)
        return hasher.hexdigest()
