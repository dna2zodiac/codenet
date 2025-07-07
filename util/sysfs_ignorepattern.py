import os
import re
from pathlib import Path

def IsPathIgnored(file_path, gitignore_patterns=[]):
   """
   Check if a file path matches any pattern in a .gitignore file.

   Args:
      file_path: Path to check (string or Path object)
      gitignore_patterns: Patterns from .gitignore file (default: '.gitignore')

   Returns:
      bool: True if the path should be ignored, False otherwise
   """
   file_path = Path(file_path)
   # Check the file path and all its parent directories
   if _MatchesAnyPattern(file_path, gitignore_patterns):
      return True
   return False


def ParseIgnoreFile(gitignore_path):
   """
   Parse .gitignore file and return a list of (pattern, is_negation) tuples.
   """
   compiled_patterns = []

   with open(gitignore_path, 'r') as f:
      for line in f:
         line = line.strip()

         # Skip empty lines and comments
         if not line or line.startswith('#'):
            continue

         # Check if it's a negation pattern
         is_negation = line.startswith('!')
         if is_negation:
            line = line[1:]

         # Check if it's a directory pattern
         is_dir_pattern = line.endswith('/')
         if is_dir_pattern:
            line = line[:-1]

         # Convert to regex and compile
         regex_pattern = _GitignoreToRegex(line)
         compiled_regex = re.compile(regex_pattern)

         compiled_patterns.append((compiled_regex, is_negation, is_dir_pattern))
   return compiled_patterns


def _MatchesAnyPattern(path, patterns):
   """
   Check if a path matches any of the gitignore patterns.
   """
   matched = False

   for compiled_regex, is_negation, is_dir_pattern in patterns:
      if _MatchesPattern(path, compiled_regex, is_dir_pattern):
         if is_negation:
            matched = False
         else:
            matched = True

   return matched


def _MatchesPattern(path, compiled_regex, is_dir_pattern):
   """
   Check if a single path matches a gitignore pattern.
   """
   # Handle directory patterns (ending with /)
   if is_dir_pattern and not os.path.isdir(path):
      return False

   # Match against the path
   return bool(compiled_regex.search(str(path)))


def _GitignoreToRegex(pattern):
   """
   Convert a .gitignore pattern to a regex pattern.

   Args:
      pattern (str): A .gitignore pattern

   Returns:
      str: A regex pattern string, or None if the pattern is a negation
   """
   # Skip negation patterns
   if pattern.startswith('!'):
      return None

   # Remove leading/trailing whitespace
   pattern = pattern.strip()

   # Skip empty lines and comments
   if not pattern or pattern.startswith('#'):
      return None

   # Escape special regex characters (except *, ?, [, ])
   # We'll handle *, ?, and character classes separately
   pattern = re.sub(r'([.+^${}()|\\])', r'\\\1', pattern)

   # Handle character classes [...]
   # These should be preserved as-is for regex

   # Convert gitignore wildcards to regex
   # ? -> . (any single character except /)
   pattern = pattern.replace('?', '[^/]')

   # Replace remaining * with [^/]* (matches any characters except /)
   # But be careful not to replace * that's part of **
   pattern = re.sub(r'(?<!\*)\*(?!\*)', r'[^/]*', pattern)

   # Handle ** (matches any number of directories)
   # Replace **/ with (?:.*/)?
   pattern = re.sub(r'\*\*/', r'(?:.*/)?', pattern)

   # Replace /** with (?:/.*)?
   pattern = re.sub(r'/\*\*', r'(?:/.*)?', pattern)

   # If pattern doesn't start with /, it can match at any depth
   if not pattern.startswith('/'):
      pattern = '(?:^|/)' + pattern
   else:
      # Remove leading / and anchor to start
      pattern = '^' + pattern[1:]

   # If pattern ends with /, it only matches directories
   if pattern.endswith('/'):
      pattern = pattern + '.*'
   else:
      # Pattern can match both files and directories
      pattern = pattern + '(?:/.*)?$'

   return pattern


# Test function
def _TestGitignoreToRegex():
    test_cases = [
        # (pattern, test_paths_that_should_match, test_paths_that_shouldnt_match)
        ("*.py", ["test.py", "src/main.py", "deep/path/file.py"], ["test.pyc", "python"]),
        ("src/**/way", ["src/way", "src/a/way", "src/a/b/way"], ["src/away", "way"]),
        ("build/", ["build/", "build/file"], ["builds", "src/build"]),
        ("/tmp", ["tmp", "tmp/file"], ["src/tmp", "a/tmp"]),
        ("*.log", ["test.log", "dir/app.log"], ["login", "log"]),
        ("doc/*.txt", ["doc/readme.txt"], ["doc/sub/readme.txt", "readme.txt"]),
        ("a?c", ["abc", "a1c", "dir/abc"], ["ac", "abbc"]),
    ]
    
    for pattern, should_match, shouldnt_match in test_cases:
        regex = _GitignoreToRegex(pattern)
        if regex:
            compiled = re.compile(regex)
            print(f"\nPattern: {pattern}")
            print(f"Regex: {regex}")
            
            for path in should_match:
                if compiled.search(path):
                    print(f"  ✓ Correctly matches: {path}")
                else:
                    print(f"  ✗ Should match but doesn't: {path}")
            
            for path in shouldnt_match:
                if not compiled.search(path):
                    print(f"  ✓ Correctly doesn't match: {path}")
                else:
                    print(f"  ✗ Shouldn't match but does: {path}")


if __name__ == "__main__":
    # Example usage
    print("Example conversions:")
    examples = [
        "*.py",
        "src/**/way", 
        "build/",
        "/tmp",
        "*.log",
        "!important.log",  # Will return None
        "doc/*.txt",
        "a?c",
        "test[0-9].txt"
    ]
    
    for pattern in examples:
        regex = _GitignoreToRegex(pattern)
        if regex:
            print(f"{pattern:20} -> {regex}")
        else:
            print(f"{pattern:20} -> (ignored)")
    
    print("\n" + "="*50 + "\n")
    
    # Run tests
    _TestGitignoreToRegex()
