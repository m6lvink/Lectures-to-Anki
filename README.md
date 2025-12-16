# Lectures to Anki

This tool automates the process of extracting high-yield concepts from lecture slides, textbooks, and notes, converting them into Anki flashcards. It supports PDF, PPTX, and TXT files, and can generate both Basic and Cloze deletion format cards.

## Prerequisites

* Python 3.8 or higher
* `pip` package manager

## Installation

1.  **Install Dependencies**
    Open your terminal or command prompt and run:
    ```bash
    pip install openai pypdf python-pptx python-dotenv
    ```

2.  **Project Structure**
    Ensure your directory looks like this:
    ```text
    /ProjectRoot
      ├── main.py
      ├── api_handler.py
      ├── file_parser.py
      ├── data_utils.py
      ├── .env.example              <-- Template File
      └── Presentations/            <-- Put files here
    ```

## Configuration

1.  **Create Config File**
    Locate the file named `.env.example`. Copy this file to `.env` (remove the `.example` extension).

2.  **Add API Key**
    Open the newly created `.env` file in a text editor and replace `PUT KEY HERE` with your actual DeepSeek API key:
    ```env
    DEEPSEEK_API_KEY=sk-...
    ```

## Usage

1.  **Prepare Files**
    Place your lecture slides (`.pptx`), documents (`.pdf`), or raw notes (`.txt`) into the `Presentations` folder.

2.  **Run the Tool**
    Execute the main script from your terminal:
    ```bash
    python main.py
    ```

3.  **Select Card Type**
    Choose between Cloze deletion cards or Basic (front/back) cards.

4.  **Select Thinking Mode (Optional)**
    Optionally enable DeepSeek thinking mode for enhanced card generation. The tool will display an estimated cost before processing.

5.  **Select Files**
    The CLI will list all available files. Enter the index number of the file you wish to process. You can select multiple files by separating them with commas (e.g., `1, 3, 5`).

6.  **Import to Anki**
    The generated files will be saved in the `Output` folder as CSVs.
    * Open Anki.
    * Go to **File -> Import**.
    * Select the generated `.csv` file.
    * Ensure the Note Type matches your selection (**Cloze** or **Basic**).

## Outputs

All generated files are automatically saved in a folder named `Output`.

* **File Naming:** If you process `Biology_Lecture_1.pdf`, the output will be `Biology_Lecture_1_cards.csv`.
* **Format:** The files are standard CSVs with a single column containing the card content.

**Example Content (Cloze):**
```text
The {{c1::mitochondria}} is known as the powerhouse of the cell.
In Python, the {{c1::def}} keyword is used to define a function.
The {{c1::Treaty of Versailles}} was signed in {{c2::1919}}.

**Example Content (Basic):**
```text
What is the powerhouse of the cell?	The mitochondria
What keyword is used to define a function in Python?	def
When was the Treaty of Versailles signed?	1919
```

## Features

* **Card Type Selection:** Choose between Cloze deletion or Basic (front/back) card formats
* **DeepSeek Thinking Mode:** Optional enhanced generation mode with cost estimation
* **Batch Processing:** Process multiple files in a single run
* **Multiple File Formats:** Supports PDF, PPTX, and TXT files

