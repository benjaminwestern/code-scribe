# Code Scribe

Code Scribe is a Python script that converts source code files within a directory into Markdown files, including a directory tree output. This script is designed to be used as an input to a RAG Agent, for context or Long Prompt LLM Call. 

## Features

-   Converts code files into Markdown files with syntax highlighting.
-   Outputs a single markdown file or multiple output files
-   Creates a directory tree representation.
-   Allows users to select file extensions to process.
-   Supports excluding directories.
-   Handles common encoding issues.
-   Provides interactive prompts for input and output directories if not specified as arguments.

## Requirements

-   Python 3.7+
-   Libraries listed in `requirements.txt` (run `pip install -r requirements.txt` to install)

## Installation

1.  Clone the repository:

    ```bash
    git clone https://github.com/benjaminwestern/code-scribe.git
    cd code-scribe
    ```
2.  Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Basic Usage

To convert all files with extensions specified by prompt in a directory to markdown files in the same folder, you can run the script without any arguments, the application will prompt you for input.

```bash
python main.py
```

### Command-line Arguments
You can specify arguments to override prompts

```bash
python main.py <input_directory> <output_directory> [--extensions <ext1> <ext2>] [--exclude-dir <dir1> <dir2>] [--single-file]
```

**Arguments:**
- `<input_directory>`: The path to the input directory containing source code. (Optional: if omitted, the script will prompt).
- `<output_directory>`: The path to the directory where markdown files will be created. (Optional: if omitted, creates a folder with the name of the input folder in current directory, defaults to same folder as input folder).

**Options:**
- `--extensions <ext1> <ext2>`: File extensions to include (e.g., `.py .js .md`).
- `--exclude-dir <dir1> <dir2>`: Directories to exclude (can be used multiple times).
- `--single-file`: Output all content to a single file called `all_files.txt`.

### Examples

1.  **Convert files with extensions prompted interactively**:

    ```bash
    python main.py
    ```
     The application will prompt for input directory, ouput directory and single output option.
    
2.  **Convert all `.py` and `.js` files from a directory, outputting in the same folder**:

    ```bash
    python main.py ./my_project ./my_project_output --extensions .py .js
    ```

    This will create `.txt` files for each .py or .js file, a `directory_tree.txt` in an output directory called `my_project_output`

3. **Convert all files in a directory into a single output file**:

    ```bash
     python main.py ./my_project ./my_project_output --single-file
    ```
    
    This will create one single file named `all_files.txt` containing all files in the `/my_project` folder. A `directory_tree.txt` file will also be outputted

4.  **Convert files, excluding `.git` and `node_modules` directories**:

    ```bash
     python main.py ./my_project ./my_project_output --exclude-dir .git --exclude-dir node_modules
    ```
    This will ignore both the `node_modules` and `.git` folders when searching for files.

5. **Convert with interactive prompts but specify some options**

   ```bash
    python main.py --exclude-dir node_modules --single-file
   ```

   This will prompt for an input and output directory and use the single-file option as well as ignore the `node_modules` folder.

## Output

The script generates a file tree with the following format:
```
.
├── folder
│   ├── file1.py
│   └── file2.txt
└── file3.js

1 directories, 3 files
```
This will also output the content of the files as Markdown, with syntax highlighting if the file extension is recognised.

## Notes

-  The script will prompt for input and output directories if not specified as arguments.
-  The script will prompt for file extensions and show all available in input directory if not specified as arguments.
-  This script has default ignored directories of `.git`, `.terraform` and `node_modules` but can be overridden with the `--exclude-dir` option.

## Contributing

Feel free to contribute to this project by submitting issues or pull requests.

## License

This repository is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

[Benjamin Western](https://benjaminwestern.io)