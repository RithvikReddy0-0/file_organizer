# 📂 File Organizer

A powerful and customizable file organization script that helps you tidy up your directories by automatically sorting files into folders based on their extensions. This Python script uses a JSON configuration to define categories like Images, Videos, Documents, and more.

---

## 🚀 Features

- ✅ Organizes files by extension into categorized folders
- 📁 Categories are defined in a customizable `file_types.json` config file
- 🔄 Handles filename collisions (e.g., `file.txt` ➝ `file_1.txt`, etc.)
- 🧪 Dry run mode to simulate changes without moving files
- 📜 Verbose logging with console + optional log file (`organizer.log`)
- 🔒 Skips organizing the script itself, log, config, and output folders
- 🔧 Easily extendable to include more categories or file types

---
# 📌 Requirements

- Python 3.6+
- No external packages needed (uses only Python standard library)

---
# Usage
Basic Command
  ```bash
  python organizer.py /path/to/target/directory
  ```
---
# Log File

A file named organizer.log is generated in the same directory by default, containing a timestamped log of file operations (unless --no-log-file is specified).

---
# Future Improvements

- Recursive directory support (currently only top-level files are processed)
- GUI version for non-CLI users
- Configuration via command-line without JSON
- File filtering by size, modified time, etc.
