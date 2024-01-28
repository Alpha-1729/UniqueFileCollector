import xxhash
import hashlib


class FileHashCalculator:
    @staticmethod
    def sha256(file_path):
        hash_algorithm = hashlib.sha256()

        with open(file_path, "rb") as file:
            file_content = file.read()
            hash_algorithm.update(file_content)

        return hash_algorithm.hexdigest()

    @staticmethod
    def xxhash(file_path):
        hash_algorithm = xxhash.xxh64()

        with open(file_path, "rb") as file:
            file_content = file.read()
            hash_algorithm.update(file_content)

        return hash_algorithm.hexdigest()
