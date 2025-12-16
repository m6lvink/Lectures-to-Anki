'''
Lectures To Anki - Convert presentations and documents into Anki flashcards.
Author: MK 
'''

import os
import argparse
import file_parser
import api_handler
import data_utils
import progress_bar
import ui_utils
import config_utils

SUPPORTED_EXTENSIONS = {".pdf", ".pptx", ".txt"}
PARSERS = {
    ".pdf": file_parser.extractPdfText,
    ".pptx": file_parser.extractPptxText,
    ".txt": file_parser.extractTxtText
}

def getValidFiles(folder):
    if not os.path.exists(folder):
        return []
    return [f for f in os.listdir(folder) if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS]

def displayFileMenu(files):
    print("\n--- Available Files ---")
    for i, name in enumerate(files, 1):
        print(f"{i}. {name}")
    print("-" * 24)

def extractTextsFromFiles(folder, files, indices):
    texts, names = [], []
    
    for idx in indices:
        name = files[idx]
        path = os.path.join(folder, name)
        ext = os.path.splitext(name)[1].lower()
        
        print(f"Reading: {name}")
        
        parser = PARSERS.get(ext)
        if not parser:
            print(f"Skipped (unsupported): {name}")
            continue
            
        content = parser(path)
        if content and content.strip():
            texts.append(content)
            names.append(name)
        else:
            print(f"Skipped (empty): {name}")
    
    return texts, names

def showCostEstimate(texts):
    totalIn, totalOut = 0, 0
    for t in texts:
        inp, out = api_handler.estimateTokensFromText(t)
        totalIn += inp
        totalOut += out
    
    regCost = api_handler.estimateCost(totalIn, totalOut, False)
    thinkCost = api_handler.estimateCost(totalIn, totalOut, True)
    
    print(f"\n--- Estimated Cost ---")
    print(f"Regular mode: ${regCost:.4f}")
    print(f"Thinking mode: ${thinkCost:.4f}")

def processFiles(texts, names, cardType, useThinking, outputMode, client):
    from openai import OpenAI
    import httpx
    
    allCards = []
    
    for text, name in zip(texts, names):
        print(f"\nGenerating cards: {name}")
        chunks = data_utils.chunkText(text, maxWords=800)
        update, stop, thread = progress_bar.startProgressBar(len(chunks))
        pieces = []

        for i, chunk in enumerate(chunks):
            ok, cards = api_handler.generateAnkiCards(chunk, None, cardType, useThinking, client)
            update(i + 1)
            if ok and cards:
                pieces.append(cards)

        stop.set()
        thread.join()

        if pieces:
            combined = "\n".join(pieces)
            if outputMode == "separate":
                data_utils.saveToCsv(combined, name, cardType)
            else:
                allCards.append((name, combined))
        else:
            print(f"No cards generated for {name}")
    
    if outputMode == "combined" and allCards:
        print("\nSaving combined output...")
        data_utils.saveCombinedCsv(allCards, cardType)

def parseArgs():
    parser = argparse.ArgumentParser(description="Convert lecture materials to Anki flashcards")
    parser.add_argument("-f", "--folder", default="Presentations", help="Input folder path")
    parser.add_argument("-t", "--type", choices=["cloze", "basic"], help="Card type (skip prompt)")
    parser.add_argument("-m", "--mode", choices=["regular", "thinking"], help="API mode (skip prompt)")
    parser.add_argument("-o", "--output", choices=["separate", "combined"], help="Output mode (skip prompt)")
    parser.add_argument("-a", "--all", action="store_true", help="Process all files without selection")
    return parser.parse_args()

def main():
    args = parseArgs()
    
    apiKey = config_utils.loadApiKey()
    if not apiKey:
        print("Error: API key required.")
        return

    files = getValidFiles(args.folder)
    if not files:
        print(f"No supported files in '{args.folder}'")
        return

    if args.all:
        indices = list(range(len(files)))
        print(f"Processing all {len(files)} file(s)...")
    else:
        displayFileMenu(files)
        print("Select files: 1 | 1,3,5 | 1-5 | 1-3,7")
        userInput = input("Selection [all]: ").strip()
        
        if not userInput:
            indices = list(range(len(files)))
        else:
            indices = data_utils.parseUserSelection(userInput, len(files))
        
        if not indices:
            print("No valid selection.")
            return

    print(f"\nExtracting text from {len(indices)} file(s)...")
    texts, names = extractTextsFromFiles(args.folder, files, indices)
    
    if not texts:
        print("No content extracted.")
        return

    showCostEstimate(texts)
    print()

    cardType = args.type.capitalize() if args.type else ui_utils.selectCardType()
    useThinking = (args.mode == "thinking") if args.mode else ui_utils.selectThinkingMode()
    
    if len(texts) > 1:
        outputMode = args.output if args.output else ui_utils.selectOutputMode()
    else:
        outputMode = "separate"

    from openai import OpenAI
    import httpx
    
    timeout = 600.0 if useThinking else 120.0
    httpClient = httpx.Client(timeout=timeout)
    client = OpenAI(api_key=apiKey, base_url="https://api.deepseek.com", http_client=httpClient)
    
    try:
        processFiles(texts, names, cardType, useThinking, outputMode, client)
    finally:
        httpClient.close()
    
    print("\n--- Complete ---")

if __name__ == "__main__":
    main()