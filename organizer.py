import os
import shutil
import json
import argparse
import logging
from pathlib import Path

# --- Configuration ---
CONFIG_FILE_NAME = "file_types.json"
DEFAULT_OTHERS_FOLDER = "Others" # Name of the folder for unclassified files
LOG_FILE_NAME = "organizer.log"
SCRIPT_NAME = Path(__file__).name

# --- Logging Setup ---
def setup_logging(log_to_file=True, log_level=logging.INFO):
    """Configures logging for the script."""
    logger = logging.getLogger("FileOrganizer")
    logger.setLevel(log_level)

    # Console Handler
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File Handler
    if log_to_file:
        try:
            fh = logging.FileHandler(LOG_FILE_NAME)
            fh.setLevel(log_level)
            file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            fh.setFormatter(file_formatter)
            logger.addHandler(fh)
        except Exception as e:
            logger.warning(f"Could not set up log file: {e}")
            # Continue without file logging if it fails
    return logger

logger = setup_logging() # Initialize logger early

def load_file_types(config_path):
    """Loads file type mappings from the JSON config file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Error: Configuration file '{config_path}' not found.")
        return None
    except json.JSONDecodeError:
        logger.error(f"Error: Could not decode JSON from '{config_path}'. Check its format.")
        return None

def get_category_for_extension(extension, file_types_map, extension_to_category_cache):
    """
    Determines the category folder for a given file extension.
    Uses a cache for faster lookups after the first time.
    """
    if not extension:
        return DEFAULT_OTHERS_FOLDER

    # Check cache first
    if extension in extension_to_category_cache:
        return extension_to_category_cache[extension]

    # Build cache if not already built (or if extension not found yet)
    if not extension_to_category_cache: # Or only rebuild if necessary
        for category, extensions in file_types_map.items():
            for ext in extensions:
                normalized_ext = ext.lower() # Ensure consistency
                if normalized_ext not in extension_to_category_cache:
                     extension_to_category_cache[normalized_ext] = category
    
    # Lookup again after cache might have been populated
    category = extension_to_category_cache.get(extension.lower(), DEFAULT_OTHERS_FOLDER)
    return category

def handle_collision(destination_path: Path) -> Path:
    """
    If a file with the same name exists at the destination,
    append a counter to the filename.
    e.g., image.jpg -> image_1.jpg -> image_2.jpg
    """
    if not destination_path.exists():
        return destination_path

    parent = destination_path.parent
    stem = destination_path.stem
    suffix = destination_path.suffix
    counter = 1
    
    new_path = parent / f"{stem}_{counter}{suffix}"
    while new_path.exists():
        counter += 1
        new_path = parent / f"{stem}_{counter}{suffix}"
    return new_path

# --- Main Logic ---
def organize_files(target_dir_path: Path, file_types_map: dict, dry_run: bool = False):
    """
    Organizes files in the target directory based on their extensions.
    """
    if not target_dir_path.is_dir():
        logger.error(f"Error: Target directory '{target_dir_path}' not found or is not a directory.")
        return

    logger.info(f"Scanning directory: {target_dir_path}{' (Dry Run)' if dry_run else ''}")

    # Create a cache for extension to category mapping for performance
    extension_to_category_cache = {}
    # Pre-populate the cache
    for category_name, extensions_list in file_types_map.items():
        for ext in extensions_list:
            extension_to_category_cache[ext.lower()] = category_name
    
    # Get a list of known category folder names to avoid processing them
    known_category_folders = set(file_types_map.keys())
    known_category_folders.add(DEFAULT_OTHERS_FOLDER) # Add "Others" too

    files_moved = 0
    files_skipped = 0

    for item_path in target_dir_path.iterdir():
        # Skip the script itself, its config, the log file, and any known category folders
        if item_path.name == SCRIPT_NAME or \
           item_path.name == CONFIG_FILE_NAME or \
           item_path.name == LOG_FILE_NAME or \
           (item_path.is_dir() and item_path.name in known_category_folders):
            logger.debug(f"Skipping: {item_path.name} (protected or category folder)")
            continue

        if item_path.is_file():
            file_extension = item_path.suffix.lower() # Get extension and make it lowercase
            
            category_name = get_category_for_extension(
                file_extension, 
                file_types_map, 
                extension_to_category_cache
            )

            destination_folder_path = target_dir_path / category_name
            destination_file_path = destination_folder_path / item_path.name

            if not dry_run:
                try:
                    destination_folder_path.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    logger.error(f"Could not create directory {destination_folder_path}: {e}")
                    files_skipped += 1
                    continue
            
            # Handle potential filename collisions
            if not dry_run: # Only resolve collision if not a dry run, for dry run just show target
                 final_destination_file_path = handle_collision(destination_file_path)
            else:
                 final_destination_file_path = destination_file_path # For dry run, show intended path
                 if destination_file_path.exists(): # If collision would occur
                     resolved_collision_path = handle_collision(destination_file_path)
                     logger.info(f"[DRY RUN] Would move: '{item_path.name}' to '{destination_folder_path.name}/{resolved_collision_path.name}' (collision handling)")
                     files_moved += 1
                     continue # Skip actual move logging for this case

            if dry_run:
                logger.info(f"[DRY RUN] Would move: '{item_path.name}' to '{destination_folder_path.name}/{item_path.name}'")
            else:
                try:
                    shutil.move(str(item_path), str(final_destination_file_path))
                    logger.info(f"Moved: '{item_path.name}' to '{destination_folder_path.name}/{final_destination_file_path.name}'")
                except Exception as e:
                    logger.error(f"Could not move '{item_path.name}': {e}")
                    files_skipped += 1
                    continue
            files_moved +=1
        
        elif item_path.is_dir():
            logger.debug(f"Skipping directory: {item_path.name} (sub-directory processing not implemented)")
            # Future: Add recursive processing option here if desired

    logger.info("-" * 30)
    logger.info(f"Organization complete.{' (Dry Run)' if dry_run else ''}")
    logger.info(f"Files processed/moved: {files_moved}")
    logger.info(f"Files skipped (errors/protected): {files_skipped}")
    if not dry_run and files_moved > 0:
        logger.info(f"Log file saved to: {LOG_FILE_NAME}")

def main():
    parser = argparse.ArgumentParser(
        description="Organize files in a target directory based on their extensions.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "target_directory",
        type=str,
        help="The directory to scan and organize."
    )
    parser.add_argument(
        "--config",
        type=str,
        default=CONFIG_FILE_NAME,
        help=f"Path to the JSON file type configuration. (default: {CONFIG_FILE_NAME})"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the organization process without actually moving any files."
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging (DEBUG level)."
    )
    parser.add_argument(
        "--no-log-file",
        action="store_true",
        help="Disable logging to a file (organizer.log)."
    )

    args = parser.parse_args()

    # Re-configure logger based on args
    global logger 
    log_level = logging.DEBUG if args.verbose else logging.INFO
    log_to_file_enabled = not args.no_log_file
    
    # Clear existing handlers if any, before re-setting up
    # This is important if main() could be called multiple times in a session (not typical for scripts)
    # or if setup_logging was called with defaults before parsing args.
    if logger.hasHandlers():
        logger.handlers.clear()
    logger = setup_logging(log_to_file=log_to_file_enabled, log_level=log_level)


    logger.info("File Organizer Script Started")
    logger.debug(f"Arguments: {args}")


    file_types_map = load_file_types(args.config)
    if file_types_map is None:
        logger.critical("Failed to load file types. Exiting.")
        return

    target_path = Path(args.target_directory).resolve() # Get absolute path

    organize_files(target_path, file_types_map, args.dry_run)

if __name__ == "__main__":
    main()