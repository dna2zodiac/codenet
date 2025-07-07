"""
import sqlite3

# Connect to database (creates file if it doesn't exist)
conn = sqlite3.connect('example.db')
cursor = conn.cursor()

# Create a table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        age INTEGER
    )
''')
print("Table created successfully")

# Insert a row
cursor.execute('''
    INSERT INTO users (name, email, age) 
    VALUES (?, ?, ?)
''', ('John Doe', 'john@example.com', 30))
conn.commit()
print(f"Row inserted with ID: {cursor.lastrowid}")
inserted_id = cursor.lastrowid

# Read the inserted row
cursor.execute('SELECT * FROM users WHERE id = ?', (inserted_id,))
print(f"Inserted row: {cursor.fetchone()}")

# Update the row
cursor.execute('''
    UPDATE users 
    SET name = ?, age = ? 
    WHERE id = ?
''', ('Jane Doe', 31, inserted_id))
conn.commit()
print(f"Updated {cursor.rowcount} row(s)")

# Read the updated row
cursor.execute('SELECT * FROM users WHERE id = ?', (inserted_id,))
print(f"Updated row: {cursor.fetchone()}")

# Delete the row
cursor.execute('DELETE FROM users WHERE id = ?', (inserted_id,))
conn.commit()
print(f"Deleted {cursor.rowcount} row(s)")

# Verify deletion
cursor.execute('SELECT * FROM users WHERE id = ?', (inserted_id,))
result = cursor.fetchone()
print(f"Row after deletion: {result}")

# Close the connection
cursor.close()
conn.close()
"""

"""
   def create_table(self):
        with self.get_cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    age INTEGER
                )
            ''')
            print("Table created successfully")
    
   def insert_row(self, name, email, age):
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO users (name, email, age) 
                VALUES (?, ?, ?)
            ''', (name, email, age))
            row_id = cursor.lastrowid
            print(f"Row inserted with ID: {row_id}")
            return row_id
    
   def update_row(self, row_id, name=None, email=None, age=None):
        # Build dynamic update query based on provided parameters
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if email is not None:
            updates.append("email = ?")
            params.append(email)
        if age is not None:
            updates.append("age = ?")
            params.append(age)
        
        if not updates:
            print("No fields to update")
            return
        
        params.append(row_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            print(f"Updated {cursor.rowcount} row(s)")
    
   def delete_row(self, row_id):
        with self.get_cursor() as cursor:
            cursor.execute('DELETE FROM users WHERE id = ?', (row_id,))
            print(f"Deleted {cursor.rowcount} row(s)")
    
   def get_row(self, row_id):
        with self.get_cursor() as cursor:
            cursor.execute('SELECT * FROM users WHERE id = ?', (row_id,))
            return cursor.fetchone()
"""

import os
import sqlite3
from datetime import datetime
from contextlib import contextmanager

from .sysfs import CalculateFileHash

class DatabaseManager:
   def __init__(self, db_path):
      self.db_path = db_path

   @contextmanager
   def GetCursor(self):
      """Context manager for database operations"""
      conn = sqlite3.connect(self.db_path)
      cursor = conn.cursor()
      try:
         yield cursor
         conn.commit()
      except Exception as e:
         conn.rollback()
         raise e
      finally:
         cursor.close()
         conn.close()

   def UpdateRepository(self, root_path, file_list):
      # Create tables if they don't exist
      with self.GetCursor() as cursor:
         # Config table
         cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
               key TEXT PRIMARY KEY,
               value TEXT,
               updated_at TIMESTAMP
            )
         ''')
         # Files table
         cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
               fid INTEGER PRIMARY KEY AUTOINCREMENT,
               filepath TEXT UNIQUE NOT NULL,
               ts TIMESTAMP
            )
         ''')
         # File hashes table
         cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_hashes (
               hid INTEGER PRIMARY KEY AUTOINCREMENT,
               filehash TEXT UNIQUE NOT NULL
            )
         ''')
         # File to hash mapping table
         cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_hash_mapping (
               fid INTEGER NOT NULL,
               hid INTEGER NOT NULL,
               PRIMARY KEY (fid, hid),
               FOREIGN KEY (fid) REFERENCES files(fid) ON DELETE CASCADE,
               FOREIGN KEY (hid) REFERENCES file_hashes(hid)
            )
         ''')
         # Create indexes for better performance
         cursor.execute('CREATE INDEX IF NOT EXISTS idx_filepath ON files(filepath)')
         cursor.execute('CREATE INDEX IF NOT EXISTS idx_filehash ON file_hashes(filehash)')

      # Update config
      current_timestamp = datetime.now()
      with self.GetCursor() as cursor:
         cursor.execute('''
            INSERT OR REPLACE INTO config (key, value, updated_at)
            VALUES (?, ?, ?)
         ''', ('root_path', root_path, current_timestamp))
         
         cursor.execute('''
            INSERT OR REPLACE INTO config (key, value, updated_at)
            VALUES (?, ?, ?)
         ''', ('last_update', str(current_timestamp), current_timestamp))

      # Get existing files from database
      with self.GetCursor() as cursor:
         cursor.execute('SELECT fid, filepath FROM files')
         existing_files = {row[1]: row[0] for row in cursor.fetchall()}

      # Process current file list
      current_files = set(file_list)
      existing_filepaths = set(existing_files.keys())

      # Files to remove (in DB but not in current list)
      files_to_remove = existing_filepaths - current_files

      # Files to add or update
      files_to_process = current_files

      # Remove obsolete files
      if files_to_remove:
         with self.GetCursor() as cursor:
            # Delete from file_hash_mapping first (due to foreign key)
            placeholders = ','.join('?' * len(files_to_remove))
            cursor.execute(f'''
               DELETE FROM file_hash_mapping 
               WHERE fid IN (
                  SELECT fid FROM files WHERE filepath IN ({placeholders})
               )
            ''', tuple(files_to_remove))

            # Delete from files table
            cursor.execute(f'''
               DELETE FROM files WHERE filepath IN ({placeholders})
            ''', tuple(files_to_remove))

      # Process each file
      for filepath in files_to_process:
         full_path = os.path.join(root_path, filepath)

         # Skip if file doesn't exist
         if not os.path.exists(full_path):
            continue

         # Get file modification time
         file_mtime = datetime.fromtimestamp(os.path.getmtime(full_path))

         # Check if file needs updating
         needs_update = True
         if filepath in existing_files:
            with self.GetCursor() as cursor:
               cursor.execute('SELECT ts FROM files WHERE filepath = ?', (filepath,))
               result = cursor.fetchone()
               if result and result[0]:
                  # Parse stored timestamp
                  stored_ts = datetime.fromisoformat(result[0])
                  if stored_ts >= file_mtime:
                     needs_update = False

         if needs_update:
            # Calculate file hash
            file_hash = CalculateFileHash(full_path)

            # Insert or update file record
            with self.GetCursor() as cursor:
               cursor.execute('''
                  INSERT OR REPLACE INTO files (filepath, ts)
                  VALUES (?, ?)
               ''', (filepath, file_mtime))

               # Get the file ID
               cursor.execute('SELECT fid FROM files WHERE filepath = ?', (filepath,))
               fid = cursor.fetchone()[0]

               # Insert hash if it doesn't exist
               cursor.execute('''
                  INSERT OR IGNORE INTO file_hashes (filehash)
                  VALUES (?)
               ''', (file_hash,))

               # Get hash ID
               cursor.execute('SELECT hid FROM file_hashes WHERE filehash = ?', (file_hash,))
               hid = cursor.fetchone()[0]

               # Remove old mapping if exists
               cursor.execute('DELETE FROM file_hash_mapping WHERE fid = ?', (fid,))

               # Insert new mapping
               cursor.execute('''
                  INSERT INTO file_hash_mapping (fid, hid)
                  VALUES (?, ?)
               ''', (fid, hid))

      # Clean up orphaned hashes (hashes with no file references)
      with self.GetCursor() as cursor:
         cursor.execute('''
               DELETE FROM file_hashes
               WHERE hid NOT IN (
                  SELECT DISTINCT hid FROM file_hash_mapping
               )
         ''')

if __name__ == "__main__":
   import sys
   from .sysfs import IterateFiles
   from .sysfs import BuildExclusioinFilter, BuildGitignoreFilter
   db_filepath = sys.argv[1]
   repo_filepath = sys.argv[2]
   db = DatabaseManager(db_filepath)
   f1 = BuildExclusioinFilter(['.git'])
   f2 = BuildGitignoreFilter('.gitignore')
   file_list = IterateFiles(repo_filepath, lambda x, y: f1(x, y) or f2(x, y))
   print(file_list)
   db.UpdateRepository(repo_filepath, file_list)