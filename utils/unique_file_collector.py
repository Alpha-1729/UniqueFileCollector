import json
import os
import pickle
import shutil
from typing import Dict, Set, Optional, Tuple, List
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import utils.config as config
from utils.helpers.file_manager import FileManager
from utils.helpers.file_hash_calculator import FileHashCalculator
from utils.helpers.json_reader import JsonReader
from utils.helpers.string_generator import StringGenerator
from utils.Enums.hash_algorithm import HashAlgorithm


# Top-level, importable worker (safe for threads; also safe if using processes later)
def hash_file_worker(path: str) -> Tuple[str, Optional[str]]:
    try:
        file_hash = FileHashCalculator.compute_hash(path, algorithm=HashAlgorithm.SHA256, chunk_size=8192)
        return path, file_hash
    except Exception:
        return path, None


class UniqueFileCollector:

    def __init__(
        self,
        source_directory: str,
        destination_directory: str,
        previous_hashes_file: Optional[str] = None,
        max_workers: Optional[int] = None,
    ):
        self.source_directory = source_directory
        self.destination_directory = destination_directory
        self.previous_hashes_file = previous_hashes_file
        self.file_hashes: Set[str] = set()
        self.latest_files_dict: Dict[str, Optional[str]] = {}
        self.extension_category_dict: Dict[str, str] = {}
        self.new_files_dir = config.NEW_FILE_DIR_NAME if previous_hashes_file else ""
        # reasonable default worker count for threads
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)

    def load_previous_hashes(self) -> None:
        """Load previous hashes from pickle if provided."""
        if self.previous_hashes_file:
            try:
                self.file_hashes = FileManager.read_pickle(self.previous_hashes_file)
            except (IOError, pickle.PickleError) as e:
                print(f"Error loading previous hashes: {e}")
                self.file_hashes = set()

    def load_latest_files(self) -> None:
        """Walk source dir and hash files in parallel (threads), adding unique ones."""
        file_paths: List[str] = []
        for root, _, files in os.walk(self.source_directory):
            for file in files:
                file_paths.append(os.path.join(root, file))

        if not file_paths:
            return
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(hash_file_worker, path) for path in file_paths]
            for future in tqdm(as_completed(futures), total=len(file_paths), desc="Hashing files"):
                path, file_hash = future.result()
                if file_hash and file_hash not in self.file_hashes:
                    self.file_hashes.add(file_hash)
                    self.latest_files_dict[path] = None

    def update_latest_files_destination(self) -> None:
        """Update destinations with per-folder unique name checking."""
        unique_names_per_folder: Dict[str, Set[str]] = {}

        for source_file_path in tqdm(self.latest_files_dict.keys(), desc="Preparing destinations"):
            file_name = os.path.basename(source_file_path)
            base_name, extension = FileManager.split_file_name(file_name)

            if extension is None:
                extension = FileManager.get_extension(source_file_path)

            extension_category = FileManager.get_extension_category(extension, self.extension_category_dict)
            extension_folder = extension or config.NO_EXTENSION_FILES_DIR

            dest_folder = os.path.join(
                self.destination_directory, extension_category, extension_folder, self.new_files_dir
            )
            new_file_name = base_name if not extension else f"{base_name}.{extension}"

            # Ensure unique per destination folder
            folder_uniques = unique_names_per_folder.setdefault(dest_folder, set())
            if new_file_name in folder_uniques:
                random_string = "_" + StringGenerator.generate_random_string(10)
                new_file_name = f"{base_name}{random_string}" + (f".{extension}" if extension else "")

            folder_uniques.add(new_file_name)

            destination_file_path = os.path.join(dest_folder, new_file_name)
            self.latest_files_dict[source_file_path] = destination_file_path

    def load_extension_category(self) -> None:
        """Load extension categories from JSON."""
        try:
            extension_category_json = JsonReader.read_from_file(config.EXTENSION_CATEGORY_PATH)
            for category, extensions in extension_category_json.items():
                for ext in extensions:
                    self.extension_category_dict[ext] = category
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading extension categories: {e}")
            raise

    def store_unique_hashes(self) -> None:
        """Store updated hashes to pickle."""
        hash_file_path = os.path.join(self.destination_directory, config.HASH_FILE_NAME)
        try:
            FileManager.dump_pickle(hash_file_path, self.file_hashes)
        except IOError as e:
            print(f"Error storing hashes: {e}")

    def move_files(self) -> None:
        """Move files to destinations."""
        try:
            FileManager.move_files(self.latest_files_dict)
        except shutil.Error as e:
            print(f"Error moving files: {e}")

    def run(self) -> None:
        """Run the full collection process."""
        self.load_extension_category()
        self.load_previous_hashes()
        self.load_latest_files()
        self.update_latest_files_destination()
        self.move_files()
        self.store_unique_hashes()
