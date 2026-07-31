#!/usr/bin/env python3

from core.collector import UniqueFileCollector
from utils.file_manager import FileManager


def main():
    source_dir = FileManager.select_directory("Select the source directory")
    destination_dir = FileManager.select_directory("Select the destination directory")

    previous_hash_file = None
    resp = input("Does a previous hash file exist? (yes/no): ").lower().strip()
    if resp in ("yes", "y"):
        previous_hash_file = FileManager.select_file("Select previous run hash file")

    collector = UniqueFileCollector(
        source_directory=source_dir,
        destination_directory=destination_dir,
        previous_hashes_file=previous_hash_file,
        max_workers=4,
    )
    collector.run()


if __name__ == "__main__":
    main()
