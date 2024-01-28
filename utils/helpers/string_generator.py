import random
import string


class StringGenerator:
    @staticmethod
    def generate_random_string(length) -> str:
        random_string = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
        return random_string
