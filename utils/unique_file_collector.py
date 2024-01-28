import os
from tqdm import tqdm

import utils.config as config
from utils.helpers.file_manager import FileManager
from utils.helpers.file_hash_calculator import FileHashCalculator
from utils.helpers.json_reader import JsonReader
from utils.helpers.string_generator import StringGenerator


class UniqueFileCollector:
    def __init__(self, source_directory, destination_directory, previous_hashes_file=None):
        self.source_directory = source_directory
        self.destination_directory = destination_directory
        self.previous_hashes_file = previous_hashes_file
        self.file_hashes = set()
        self.latest_files_dict = dict()
        self.extension_category_dict = dict()
        self.new_files_dir = config.NEW_FILE_DIR_NAME if previous_hashes_file else ""

    def load_previous_hashes(self):
        if self.previous_hashes_file:
            previous_file_hash = FileManager.read_pickle(self.previous_hashes_file)
            self.file_hashes = previous_file_hash

    def load_latest_files(self):
        file_path_set = set()
        for root, dirs, files in os.walk(self.source_directory):
            for file in files:
                file_path = os.path.join(root, file)
                file_path_set.add(file_path)

        for file_path in tqdm(file_path_set):
            file_hash = FileHashCalculator.sha256(file_path)

            if file_hash not in self.file_hashes:
                self.file_hashes.add(file_hash)
                self.latest_files_dict[file_path] = None

    def update_latest_files_destination(self):
        unique_file_names = set()

        for source_file_path in tqdm(self.latest_files_dict.keys()):
            file_name = os.path.basename(source_file_path)
            base_name, extension = FileManager.split_file_name(file_name)

            if extension is None:
                extension = FileManager.get_extension(source_file_path)

            extension_category = FileManager.get_extension_category(extension, self.extension_category_dict)
            extension_folder = config.NO_EXTENSION_FILES_DIR if extension == "" else extension

            new_file_name = base_name if extension == "" else f"{base_name}.{extension}"

            if new_file_name in unique_file_names:
                random_string = "_" + StringGenerator.generate_random_string(10)
                new_file_name = f"{base_name}{random_string}"
                if extension != "":
                    new_file_name = f"{new_file_name}.{extension}"

            unique_file_names.add(new_file_name)

            destination_file_path = os.path.join(
                self.destination_directory,
                config.UNIQUE_FILES_BASE_DIR,
                extension_category,
                extension_folder,
                self.new_files_dir,
                new_file_name
            )

            self.latest_files_dict[source_file_path] = destination_file_path

    def load_extension_category(self):
        extension_category_json = JsonReader.read_from_file(config.EXTENSION_CATEGORY_PATH)

        for extension_category, extensions in extension_category_json.items():
            for extension in extensions:
                self.extension_category_dict[extension] = extension_category

    def store_unique_hashes(self):
        hash_file_path = os.path.join(self.destination_directory, config.UNIQUE_FILES_BASE_DIR, config.HASH_FILE_NAME)
        FileManager.dump_pickle(hash_file_path, self.file_hashes)

    def move_files(self):
        FileManager.move_files(self.latest_files_dict)

    def run(self):
        self.load_extension_category()
        self.load_previous_hashes()
        self.load_latest_files()
        self.update_latest_files_destination()
        self.move_files()
        self.store_unique_hashes()
