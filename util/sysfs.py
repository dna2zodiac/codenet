import os
import hashlib
from typing import List

def IterateFiles(root_path: str, exclusions: List[str] = None) -> List[str]:
   """
   Iterate through all files in a directory tree, excluding specified directories.
    
   Args:
      root_path: The root directory to start iteration from
      exclusions: List of directory names to exclude (e.g., ['.git', '.svn'])
    
   Returns:
      List of file paths relative to the root_path
   """
   if exclusions is None:
      exclusions = []
    
   exclusion_set = set(exclusions)
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
      dirnames[:] = [d for d in dirnames if d not in exclusion_set]
        
      # Also remove directories we can't access
      accessible_dirs = []
      for dirname in dirnames:
         full_dir_path = os.path.join(dirpath, dirname)
         try:
            # Check if we have read and execute permissions for the directory
            if os.access(full_dir_path, os.R_OK | os.X_OK):
               accessible_dirs.append(dirname)
         except Exception:
            # Skip directories that cause any errors
            pass
        
      dirnames[:] = accessible_dirs
        
      for filename in filenames:
         try:
            full_path = os.path.join(dirpath, filename)
            
            # Check if we can access the file
            if not os.access(full_path, os.R_OK):
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


# Example usage
if __name__ == "__main__":
    # Example 1: Iterate files
    root = "."
    exclusions = ['.git', '.svn', '__pycache__', 'node_modules']
    files = IterateFiles(root, exclusions)
    
    print(f"Found {len(files)} files:")
    for file in files[:10]:  # Print first 10 files
        print(f"  {file}")
    
    if len(files) > 10:
        print(f"  ... and {len(files) - 10} more files")
    
    # Example 2: Calculate file hash
    if files:
        test_file = os.path.join(root, files[0])
        try:
            file_hash = CalculateFileHash(test_file)
            print(f"\nSHA256 hash of '{files[0]}':")
            print(f"  {file_hash}")
        except Exception as e:
            print(f"\nError calculating hash: {e}")