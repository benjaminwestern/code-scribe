import os
import argparse
import re
import logging
import inquirer
import sys
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

def setup_logging(level: int = logging.INFO, 
                 log_file: Optional[str] = None) -> None:
    """Configure logging for the application.

    Args:
        level (int, optional): The logging level. Defaults to logging.INFO.
        log_file (Optional[str], optional): Path to the log file. Defaults to None.
    """
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(threadName)s - %(levelname)s - %(message)s'
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Always add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Optionally add file handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

def sanitise_filename(filename: str) -> str:
    """Sanitises a filename by removing invalid characters, lowercasing and replacing spaces.

    Args:
        filename (str): The filename to sanitise.

    Returns:
        str: The sanitised filename.
    """
    filename = re.sub(r'[^\w\s-]', '_', filename).strip().lower()
    filename = re.sub(r'[-\s]+', '_', filename)
    return filename


def generate_markdown_from_file(input_filepath: Path, output_filepath: Path, rel_path: str, language: Optional[str]) -> None:
    """Generates a single markdown file with extension info.

    Args:
        input_filepath (Path): Path to the input file.
        output_filepath (Path): Path to the output markdown file.
        rel_path (str): The relative path of the file.
        language (Optional[str]): Optional language for syntax highlighting.
    """
    try:
        with open(input_filepath, 'r', encoding='utf-8') as infile:
            file_contents = infile.read()
        markdown_output = f"# File Name: {rel_path}\n"
        markdown_output += "# File Contents:\n"
        if language:
            markdown_output += f"```{language}\n{file_contents}\n```\n\n"
        else:
           markdown_output += f"{file_contents}\n\n"
        with open(output_filepath, "w", encoding="utf-8") as outfile:
            outfile.write(markdown_output)
        logger.info(f"Markdown file '{output_filepath}' created successfully.")
    except UnicodeDecodeError:
        logger.warning(f"Skipping {input_filepath} due to encoding issues.")
    except Exception as e:
        logger.error(f"Error processing {input_filepath}: {e}")


def generate_tree_output(directory: Path, output_filename: Path, exclude_dirs: Optional[List[str]] = None) -> None:
    """Generates a tree-like representation of the directory.

    Args:
        directory (Path): Path to the directory to represent.
        output_filename (Path): Path to the output file.
        exclude_dirs (Optional[List[str]], optional): List of directory names to exclude. Defaults to None.
    """
    def get_tree_structure(path: Path, indent: str = "", exclude_dirs: Optional[List[str]] = None):
        """Recursively builds the tree structure.

        Args:
            path (Path): Current path in the recursion.
            indent (str, optional): Current indent string. Defaults to "".
            exclude_dirs (Optional[List[str]], optional): List of directory names to exclude. Defaults to None.

        Returns:
             list: List of tuples of path and tree output with prefix
        """
        tree = []
        entries = sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name))
        
        for i, entry in enumerate(entries):
            if should_exclude_directory(Path(entry), exclude_dirs):
                continue
            
            is_last = i == len(entries) - 1
            prefix = '└── ' if is_last else '├── '
            
            tree.append((entry.path, indent + prefix))
            
            if entry.is_dir():
                subtree = get_tree_structure(Path(entry.path), indent + ('    ' if is_last else '│   '), exclude_dirs=exclude_dirs)
                tree.extend(subtree)
                        
        return tree

    tree_structure = get_tree_structure(directory, exclude_dirs=exclude_dirs)
    
    tree_lines = ['.']
    for path, prefix in tree_structure:
        name = os.path.relpath(path, directory)
        if os.path.isdir(path):
            name = os.path.basename(path)
        else:
            name = os.path.basename(path)
        tree_lines.append(f"{prefix}{name}")

    dir_count = sum(1 for path, _ in tree_structure if os.path.isdir(path))
    file_count = sum(1 for path, _ in tree_structure if os.path.isfile(path))
    tree_lines.append(f"\n{dir_count} directories, {file_count} files")

    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(tree_lines))
    logger.info(f"Directory tree written to '{output_filename}'.")

def discover_extensions(input_dir: Path, exclude_dirs: List[str]) -> List[Tuple[str, int]]:
    """Discovers all unique file extensions in the input directory and provides counts.

    Args:
        input_dir (Path): The path to the input directory.
        exclude_dirs (List[str]): List of directories to exclude.

    Returns:
        List[Tuple[str, int]]: List of tuples of extension and count
    """
    extensions = {}
    
    def _scan_directory(directory: Path):
        for entry in os.scandir(directory):
            if should_exclude_directory(Path(entry), exclude_dirs):
                continue
            if entry.is_dir():
                _scan_directory(Path(entry.path))
            elif entry.is_file():
                ext = os.path.splitext(entry.name)[1].lower()
                if entry.name.startswith('.'):
                    extensions[entry.name] = extensions.get(entry.name, 0) + 1
                else:
                    extensions[ext] = extensions.get(ext, 0) + 1
    _scan_directory(input_dir)
    return list(extensions.items())


def select_extensions(input_dir: Path, exclude_dirs: List[str]) -> List[str]:
    """Lets the user select file extensions to process.

    Args:
        input_dir (Path): The path to the input directory.
        exclude_dirs (List[str]): List of directories to exclude.

    Returns:
        List[str]: A list of selected file extensions.
    """
    
    extensions_with_counts = discover_extensions(input_dir, exclude_dirs)
    
    if not extensions_with_counts:
      logger.warning("No files with usable extensions were found.")
      return []
    
    choices = [f"{ext} ({count})" for ext, count in extensions_with_counts]
    questions = [
        inquirer.Checkbox(
            'extensions',
            message="Select file extensions to process",
            choices=choices,
            default=choices
        ),
    ]
    answers = inquirer.prompt(questions)
    
    if not answers or 'extensions' not in answers:
      return []
    selected_extensions =  [choice.split(" ")[0] for choice in answers['extensions']]
    return selected_extensions

def should_exclude_directory(path: Path, exclude_dirs: List[str] = None) -> bool:
  """Checks if a directory should be excluded based on user input and defaults.

  Args:
      path (Path): Path of the directory to check.
      exclude_dirs (List[str], optional): List of directory names to exclude. Defaults to None.

  Returns:
      bool: True if the directory should be excluded, False otherwise.
  """
  default_exclude = ['.terraform', 'node_modules', '.git']
  full_exclude = default_exclude 
  
  if exclude_dirs:
    full_exclude += exclude_dirs

  for exclude_dir in full_exclude:
    if path.name == exclude_dir:
      return True
  return False
  
def generate_markdown_from_directory(input_dir: Path, output_dir: Path, extensions: List[str], single_file: bool, exclude_dirs: List[str]) -> None:
    """Generates markdown files and directory tree.

    Args:
        input_dir (Path): Path to the input directory.
        output_dir (Path): Path to the output directory.
        extensions (List[str]): List of file extensions to process.
        single_file (bool): Whether to output to a single file.
        exclude_dirs (List[str]): List of directories to exclude.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    all_markdown_content = []
    
    for root, _, files in os.walk(input_dir):
        
        root_path = Path(root)
        if should_exclude_directory(root_path, exclude_dirs):
            logger.debug(f"Skipping excluded directory: {root}")
            continue
        
        for file in files:
          if file not in ['.DS_Store', '.env']:
            ext = os.path.splitext(file)[1].lower()
            if ext in extensions or (not ext and file in extensions):
                input_filepath = Path(os.path.join(root, file))
                rel_path = os.path.relpath(input_filepath, input_dir)
                sanitised_filename = sanitise_filename(rel_path)
                markdown_filename = f"{sanitised_filename}.txt"
                language = ext[1:]

                if not single_file:
                    output_filepath = output_dir / rel_path
                    output_filepath = output_filepath.with_name(markdown_filename)
                    output_filepath.parent.mkdir(parents=True, exist_ok=True)
                    generate_markdown_from_file(input_filepath, output_filepath, rel_path, language)
                
                else:
                  try:
                      with open(input_filepath, 'r', encoding='utf-8') as infile:
                          file_contents = infile.read()
                      
                      markdown_content = f"# File Name: {rel_path}\n"
                      markdown_content += "# File Contents:\n"
                      if language:
                          markdown_content += f"```{language}\n{file_contents}\n```\n\n"
                      else:
                          markdown_content += f"{file_contents}\n\n"

                      all_markdown_content.append(markdown_content)
                  except UnicodeDecodeError:
                        logger.warning(f"Skipping {input_filepath} due to encoding issues.")
                  except Exception as e:
                      logger.error(f"Error processing {input_filepath}: {e}")
                      
    
    if single_file:
      single_output_file = output_dir / 'all_files.txt'
      with open(single_output_file, 'w', encoding='utf-8') as outfile:
        outfile.write("---\n".join(all_markdown_content))
      logger.info(f"All markdown content written to {single_output_file}")
    
    generate_tree_output(input_dir, output_dir / "directory_tree.txt", exclude_dirs)


def main():
    """Main execution function."""
    setup_logging()

    parser = argparse.ArgumentParser(
        description="Generate markdown files and directory tree from directory contents."
    )
    parser.add_argument("input_dir", nargs="?", help="Path to the input directory")
    parser.add_argument("output_dir", nargs="?", help="Path to the output directory")
    parser.add_argument(
        "--extensions",
        nargs="+",
        help="File extensions to include (e.g., .py .js .md)",
    )
    parser.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        help="Directories to exclude (can be used multiple times)",
    )
    parser.add_argument(
        "--single-file",
        action="store_true",
        help="Output all content to a single file",
    )
    args = parser.parse_args()
    
    
    questions = [
        inquirer.Path(
            'input_dir',
            message="Enter the input directory",
            path_type=inquirer.Path.DIRECTORY,
            exists=True
        ),
        inquirer.Text(
            'output_dir',
            message="Enter the output directory (leave blank to use default)",
            default=""
        ),
        inquirer.Confirm(
            'single_file',
            message="Output all content to a single file?",
            default=False
        ),
    ]
    
    if not args.input_dir:
        answers = inquirer.prompt(questions)
        input_dir = Path(answers['input_dir']) if answers else None
        output_dir_str = answers['output_dir'] if answers else ""
        single_file = answers['single_file'] if answers else False
    
    else:
      input_dir = Path(args.input_dir)
      output_dir_str = args.output_dir if args.output_dir else ""
      single_file = args.single_file
      
    if output_dir_str == "":
        if input_dir:
            output_dir = Path(os.getcwd()) /  input_dir.name
        else:
            output_dir = None
    else:
        output_dir = Path(output_dir_str)
    
    exclude_dirs = args.exclude_dir
    
    if not input_dir or not output_dir:
        logger.error("Input or output directory not provided.")
        return

    if not input_dir.is_dir():
        logger.error(f"Input directory '{input_dir}' not found.")
        return
    
    if args.extensions:
        selected_extensions = [ext.lower() for ext in args.extensions]
        logger.info(f"Using extensions from arguments: {selected_extensions}")
    else:
        selected_extensions = select_extensions(input_dir, exclude_dirs)
    
    if not selected_extensions:
      logger.info("No extensions selected. Exiting.")
      return
      
    generate_markdown_from_directory(
        input_dir, output_dir, selected_extensions, single_file, exclude_dirs
    )
    logger.info("Markdown generation complete.")


if __name__ == "__main__":
    main()