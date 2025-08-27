import xxhash
import hashlib
from utils.Enums.hash_algorithm import HashAlgorithm


class FileHashCalculator:
    @staticmethod
    def compute_hash(file_path: str, algorithm: HashAlgorithm = HashAlgorithm.XXHASH, chunk_size: int = 8192) -> str:
        """
        Compute file hash using specified algorithm with chunked reading.

        :param file_path: Path to the file.
        :param algorithm: 'xxhash' (fast) or 'sha256' (secure) or 'md5'.
        :param chunk_size: Bytes to read per chunk.
        :return: Hex digest of the hash.
        """
        if algorithm == HashAlgorithm.XXHASH:
            hash_algo = xxhash.xxh64()
        elif algorithm == HashAlgorithm.SHA256:
            hash_algo = hashlib.sha256()
        elif algorithm == HashAlgorithm.MD5:
            hash_algo = hashlib.md5()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(chunk_size):
                    hash_algo.update(chunk)
            return hash_algo.hexdigest()
        except IOError as e:
            print(f"Error hashing {file_path}: {e}")
            raise
