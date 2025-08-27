#!/usr/bin/python3

from utils.helpers.file_manager import FileManager
from utils.unique_file_collector import UniqueFileCollector


def main():
    source_dir = FileManager.select_directory("Select the source directory")
    destination_dir = FileManager.select_directory("Select the destination directory")

    previous_hash_file = None
    resp = input("Does the previous hash file exist? (yes/no): ").lower().strip()
    if resp in ("yes", "y"):
        previous_hash_file = FileManager.select_file("Select previous run hash file")

    unique_file_collector = UniqueFileCollector(
        source_directory=source_dir,
        destination_directory=destination_dir,
        previous_hashes_file=previous_hash_file,
        max_workers=4,  # tune as needed
    )
    unique_file_collector.run()


if __name__ == "__main__":
    # Required on Windows (spawn) so workers don’t re-run top-level GUI code
    main()
