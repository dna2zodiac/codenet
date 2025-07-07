import os
import hashlib
from typing import List

from .sysfs_ignorepattern import IsPathIgnored, ParseIgnoreFile

def BuildExclusioinFilter(exclusions: List[str] = None):
   exclusion_set = set(exclusions or [])
   def filter(name, _):
      return name in exclusion_set
   return filter

def BuildGitignoreFilter(gitignore_file_path):
   patterns = ParseIgnoreFile(gitignore_file_path)
   def filter(_, file_path):
      return IsPathIgnored(file_path, patterns)
   return filter

def IterateFiles(root_path: str, exclusion_filter) -> List[str]:
   """
   Iterate through all files in a directory tree, excluding specified directories.

   Args:
      root_path: The root directory to start iteration from
      exclusion_filter: filter function to exclude fn(name, path) (e.g., ['.git', '.svn'])

   Returns:
      List of file paths relative to the root_path
   """
   file_list = []

   # Normalize the root path
   try:
      root_path = os.path.abspath(root_path)
   except Exception:
      # If we can't even process the root path, return empty list
      return file_list

   # Check if root path exists and is accessible
   if not os.path.exists(root_path) or not os.access(root_path, os.R_OK):
      return file_list
   for dirpath, dirnames, filenames in os.walk(root_path):
      # Remove excluded directories from dirnames to prevent os.walk from traversing them
      dirnames[:] = [d for d in dirnames]

      # Also remove directories we can't access
      accessible_dirs = []
      for dirname in dirnames:
         full_dir_path = os.path.join(dirpath, dirname)
         try:
            # Check if we have read and execute permissions for the directory
            if (
               (not os.access(full_dir_path, os.R_OK | os.X_OK)) or
               exclusion_filter(dirname, full_dir_path)
            ):
               continue
            accessible_dirs.append(dirname)
         except Exception:
            # Skip directories that cause any errors
            pass

      dirnames[:] = accessible_dirs
      for filename in filenames:
         try:
            full_path = os.path.join(dirpath, filename)

            # Check if we can access the file
            if (
               not os.access(full_path, os.R_OK) or
               exclusion_filter(filename, full_path)
            ):
               continue

            # Get relative path from root
            relative_path = os.path.relpath(full_path, root_path)
            file_list.append(relative_path)

         except Exception:
            # Skip any files that cause errors (permission issues, broken symlinks, etc.)
            continue 
   return file_list


# Map algorithm names to hashlib functions
HASH_ALGORITHM = {
   'md5': hashlib.md5,
   'sha1': hashlib.sha1,
   'sha256': hashlib.sha256,
   'sha512': hashlib.sha512
}
def CalculateFileHash(filepath: str, algorithm: str = 'sha256') -> str:
   """
   Calculate the hash of a file.

   Args:
      filepath: Path to the file
      algorithm: Hash algorithm to use ('md5', 'sha1', 'sha256', 'sha512')

   Returns:
      Hexadecimal string representation of the file hash

   Raises:
      FileNotFoundError: If the file doesn't exist
      ValueError: If the algorithm is not supported
   """
   
   if algorithm not in HASH_ALGORITHM:
      raise ValueError(f"Unsupported algorithm: {algorithm}. Supported: {list(HASH_ALGORITHM.keys())}")

   if not os.path.isfile(filepath):
      raise FileNotFoundError(f"File not found: {filepath}")

   hash_obj = HASH_ALGORITHM[algorithm]()

   # Read file in chunks to handle large files efficiently
   with open(filepath, 'rb') as f:
      chunk_size = 8192  # 8KB chunks
      while chunk := f.read(chunk_size):
         hash_obj.update(chunk)

   return hash_obj.hexdigest()
