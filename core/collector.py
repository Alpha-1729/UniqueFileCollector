import json
import os
import pickle
import shutil
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Set, Tuple

from tqdm import tqdm

from core.config import Config
from enums.hash_algorithm import HashAlgorithm
from utils.file_manager import FileManager
from utils.hash_calculator import FileHashCalculator
from utils.json_reader import JsonReader
from utils.string_generator import StringGenerator


def hash_file_worker(path: str) -> Tuple[str, Optional[str]]:
    """Top-level worker: compute hash for a single file (thread-safe)."""
    try:
        file_hash = FileHashCalculator.compute_hash(path, algorithm=HashAlgorithm.SHA256, chunk_size=65536)
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
        self.new_files_dir = Config.NEW_FILE_DIR_NAME if previous_hashes_file else ""
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)

    def load_previous_hashes(self) -> None:
        """Load previous hashes from pickle if provided."""
        if self.previous_hashes_file:
            try:
                self.file_hashes = FileManager.read_pickle(self.previous_hashes_file)
            except (IOError, pickle.PickleError) as e:
                print(f"Error loading previous hashes: {e}")
                self.file_hashes = set()

    def _group_files_by_size(self, file_paths: List[str]) -> Dict[int, List[str]]:
        """
        Group file paths by their size in bytes.
        Files with a unique size cannot be duplicates — skip hashing them entirely.
        """
        size_map: Dict[int, List[str]] = defaultdict(list)
        for path in file_paths:
            try:
                size = os.path.getsize(path)
                size_map[size].append(path)
            except OSError:
                pass
        return size_map

    def _hash_and_filter(self, file_paths: List[str]) -> None:
        """Hash files in parallel, adding only unseen ones to latest_files_dict."""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(hash_file_worker, p) for p in file_paths]
            for future in tqdm(as_completed(futures), total=len(futures), desc="Hashing files"):
                path, file_hash = future.result()
                if file_hash and file_hash not in self.file_hashes:
                    self.file_hashes.add(file_hash)
                    self.latest_files_dict[path] = None

    def load_latest_files(self) -> None:
        """
        Walk source dir and collect unique files.

        - If no previous hashes exist: use size-based pre-filtering to skip
        hashing files whose size is unique in the current batch.
        - If previous hashes exist: every file must be hashed and checked
        against the loaded hash set to avoid re-moving already-seen files.
        """
        file_paths: List[str] = []
        for root, _, files in os.walk(self.source_directory):
            for file in files:
                file_paths.append(os.path.join(root, file))

        if not file_paths:
            return

        if self.previous_hashes_file:
            # Incremental run: every file must be checked against existing hashes
            self._hash_and_filter(file_paths)
            return

        # Fresh run: skip hashing files whose size is unique in this batch
        size_map = self._group_files_by_size(file_paths)

        unique_size_files = []
        needs_hashing = []

        for paths in size_map.values():
            if len(paths) == 1:
                unique_size_files.append(paths[0])
            else:
                needs_hashing.extend(paths)

        for path in tqdm(unique_size_files, desc="Indexing unique-size files"):
            self.latest_files_dict[path] = None

        if needs_hashing:
            self._hash_and_filter(needs_hashing)

    def update_latest_files_destination(self) -> None:
        """Assign destination paths, ensuring unique filenames per destination folder."""
        unique_names_per_folder: Dict[str, Set[str]] = {}

        for source_file_path in tqdm(self.latest_files_dict.keys(), desc="Preparing destinations"):
            file_name = os.path.basename(source_file_path)
            base_name, extension = FileManager.split_file_name(file_name)

            if extension is None:
                extension = FileManager.get_extension(source_file_path)

            extension_category = FileManager.get_extension_category(extension, self.extension_category_dict)
            extension_folder = extension or Config.NO_EXTENSION_FILES_DIR

            dest_folder = os.path.join(
                self.destination_directory,
                extension_category,
                extension_folder,
                self.new_files_dir,
            )
            new_file_name = base_name if not extension else f"{base_name}.{extension}"

            folder_uniques = unique_names_per_folder.setdefault(dest_folder, set())
            if new_file_name in folder_uniques:
                random_suffix = "_" + StringGenerator.generate_random_string(10)
                new_file_name = f"{base_name}{random_suffix}" + (f".{extension}" if extension else "")

            folder_uniques.add(new_file_name)

            destination_file_path = os.path.join(dest_folder, new_file_name)
            self.latest_files_dict[source_file_path] = destination_file_path

    def load_extension_category(self) -> None:
        """Load extension → category mapping from JSON config."""
        try:
            extension_category_json = JsonReader.read_from_file(Config.EXTENSION_CATEGORY_PATH)
            for category, extensions in extension_category_json.items():
                for ext in extensions:
                    self.extension_category_dict[ext] = category
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading extension categories: {e}")
            raise

    def store_unique_hashes(self) -> None:
        """Persist current hash set to pickle in destination directory."""
        hash_file_path = os.path.join(self.destination_directory, Config.HASH_FILE_NAME)
        try:
            FileManager.dump_pickle(hash_file_path, self.file_hashes)
        except IOError as e:
            print(f"Error storing hashes: {e}")

    def move_files(self) -> None:
        """Move all collected unique files to their computed destinations."""
        try:
            FileManager.move_files(self.latest_files_dict)
        except shutil.Error as e:
            print(f"Error moving files: {e}")

    def run(self) -> None:
        """Execute the full collection pipeline."""
        self.load_extension_category()
        self.load_previous_hashes()
        self.load_latest_files()
        self.update_latest_files_destination()
        self.move_files()
        self.store_unique_hashes()
