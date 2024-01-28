#!usr/bin/python3

from utils.helpers.file_manager import FileManager
from utils.unique_file_collector import UniqueFileCollector

source_dir = FileManager.select_directory("Select the source directory.")
destination_dir = FileManager.select_directory("Select the destination directory")

previous_hash_file = None
previous_hash_file_exists = input("Does the previous hash file exist? (yes/no): ").lower()
if previous_hash_file_exists == "yes":
    previous_hash_file = FileManager.select_file("Select previous run hash file")

unique_file_collector = UniqueFileCollector(source_dir, destination_dir, previous_hash_file)
unique_file_collector.run()
