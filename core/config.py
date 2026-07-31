import os


class Config:
    OTHER_FILES_DIR = "Other"
    NO_EXTENSION_FILES_DIR = "NoExt"
    NEW_FILE_DIR_NAME = "_NEW"
    HASH_FILE_NAME = "hash.pickle"
    EXTENSION_CATEGORY_PATH = os.path.join("config", "extension_category.json")
