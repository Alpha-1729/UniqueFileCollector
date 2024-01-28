import os
import magic
import shutil
import pickle
from tkinter import *
from tkinter import filedialog

import utils.config as config


class FileManager:
    @staticmethod
    def select_directory(title):
        root = Tk()
        root.withdraw()
        return filedialog.askdirectory(title=title)

    @staticmethod
    def select_file(title):
        root = Tk()
        root.withdraw()
        return filedialog.askopenfilename(title=title)

    @staticmethod
    def get_size(file_path):
        return os.path.getsize(file_path)

    @staticmethod
    def read_pickle(file_path):
        with open(file_path, "rb") as file:
            content = pickle.load(file)
        return content

    @staticmethod
    def split_file_name(file_name) -> tuple:
        if "." in file_name:
            base_name, extension = file_name.rsplit(".", 1)
            return base_name, extension.lower()
        return file_name, None

    @staticmethod
    def get_extension(file_path) -> str:
        file_mime_type = magic.from_file(file_path, mime=True)
        extension = file_mime_type.split(r"/")[-1]
        return extension

    @staticmethod
    def get_extension_category(extension, extension_category) -> str:
        return extension_category.get(extension, config.OTHER_FILES_DIR)

    @staticmethod
    def dump_pickle(file_path, content) -> None:
        with open(file_path, "wb") as file:
            pickle.dump(content, file)

    @staticmethod
    def move_files(source_destination_paths) -> None:
        for source_file, destination_file in source_destination_paths.items():
            destination_dir = os.path.dirname(destination_file)

            # Create directories if they do not exist
            if not os.path.exists(destination_dir):
                os.makedirs(destination_dir)

            # Move files
            shutil.move(source_file, destination_file)
