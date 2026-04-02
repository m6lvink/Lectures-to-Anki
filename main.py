'''
Lectures To Anki - Convert presentations and documents into Anki flashcards.
Author: MK 
'''

import os
import argparse
import random
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def resolveInputFolder(folderArg):
    if os.path.isabs(folderArg):
        return folderArg
    return os.path.join(BASE_DIR, folderArg)

def buildTag(fileName, tagPrefix="", tagSuffix=""):
    baseTag = os.path.splitext(fileName)[0]
    parts = []
    if tagPrefix:
        parts.append(tagPrefix.strip())
    parts.append(baseTag)
    if tagSuffix:
        parts.append(tagSuffix.strip())
    return "::".join([p for p in parts if p])

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
    return totalIn, totalOut, regCost, thinkCost

def processFiles(
    texts,
    names,
    cardType,
    useThinking,
    outputMode,
    client,
    maxChunks=None,
    outputBaseDir=None,
    tagPrefix="",
    tagSuffix=""
):
    allCards = []
    summary = {
        "files_total": len(texts),
        "files_with_cards": 0,
        "chunks_total": 0,
        "chunks_succeeded": 0,
        "chunks_failed": 0,
        "cards_valid": 0,
        "cards_invalid": 0,
        "cards_duplicates": 0,
        "output_files": [],
    }

    for text, name in zip(texts, names):
        print(f"\nGenerating cards: {name}")
        chunks = data_utils.chunkText(text, maxWords=800)
        if maxChunks and maxChunks > 0:
            chunks = chunks[:maxChunks]
        summary["chunks_total"] += len(chunks)

        update, stop, thread = progress_bar.startProgressBar(len(chunks))
        pieces = []

        for i, chunk in enumerate(chunks):
            ok, cards = api_handler.generateAnkiCards(chunk, cardType, useThinking, client)
            update(i + 1)
            if ok and cards:
                pieces.append(cards)
                summary["chunks_succeeded"] += 1
            else:
                summary["chunks_failed"] += 1
                if cards:
                    print(f"\nChunk {i + 1} failed: {cards}")

        stop.set()
        thread.join()

        if pieces:
            summary["files_with_cards"] += 1
            combined = "\n".join(pieces)
            tag = buildTag(name, tagPrefix, tagSuffix)

            if outputMode == "separate":
                ok, outPath, stats = data_utils.saveToCsv(
                    combined,
                    name,
                    cardType,
                    baseDir=outputBaseDir,
                    tagOverride=tag if (tagPrefix or tagSuffix) else None
                )
                if ok and outPath:
                    summary["output_files"].append(outPath)
                summary["cards_valid"] += stats["valid"]
                summary["cards_invalid"] += stats["invalid"]
                summary["cards_duplicates"] += stats["duplicates"]
            else:
                allCards.append((name, combined, tag))
        else:
            print(f"No cards generated for {name}")
    
    if outputMode == "combined" and allCards:
        print("\nSaving combined output...")
        ok, outPath, stats = data_utils.saveCombinedCsv(allCards, cardType, baseDir=outputBaseDir)
        if ok and outPath:
            summary["output_files"].append(outPath)
        summary["cards_valid"] += stats["valid"]
        summary["cards_invalid"] += stats["invalid"]
        summary["cards_duplicates"] += stats["duplicates"]

    return summary

def parseArgs():
    parser = argparse.ArgumentParser(description="Convert lecture materials to Anki flashcards")
    parser.add_argument("-f", "--folder", default="Presentations", help="Input folder path")
    parser.add_argument("-t", "--type", choices=["cloze", "basic"], help="Card type (skip prompt)")
    parser.add_argument("-m", "--mode", choices=["regular", "thinking"], help="API mode (skip prompt)")
    parser.add_argument("-o", "--output", choices=["separate", "combined"], help="Output mode (skip prompt)")
    parser.add_argument("-a", "--all", action="store_true", help="Process all files without selection")
    parser.add_argument("--dry-run", action="store_true", help="Extract and estimate only, no API calls")
    parser.add_argument("--max-files", type=int, default=0, help="Limit number of files processed")
    parser.add_argument("--max-chunks", type=int, default=0, help="Limit chunks per file")
    parser.add_argument("--sample", type=int, default=0, help="Randomly sample N files from selection")
    parser.add_argument("--tag-prefix", default="", help="Prefix tag for Anki rows")
    parser.add_argument("--tag-suffix", default="", help="Suffix tag for Anki rows")
    return parser.parse_args()

def main():
    args = parseArgs()

    inputFolder = resolveInputFolder(args.folder)
    files = getValidFiles(inputFolder)
    if not files:
        print(f"No supported files in '{inputFolder}'")
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

    if args.sample and args.sample > 0 and len(indices) > args.sample:
        indices = sorted(random.sample(indices, args.sample))
        print(f"Random sample enabled: selected {len(indices)} file(s)")

    if args.max_files and args.max_files > 0:
        indices = indices[:args.max_files]
        print(f"File limit enabled: processing first {len(indices)} file(s)")

    print(f"\nExtracting text from {len(indices)} file(s)...")
    texts, names = extractTextsFromFiles(inputFolder, files, indices)
    
    if not texts:
        print("No content extracted.")
        return

    totalIn, totalOut, regCost, thinkCost = showCostEstimate(texts)
    print()

    if args.dry_run:
        print("--- Dry Run Complete ---")
        print(f"Files ready: {len(texts)}")
        print(f"Estimated input tokens: {totalIn}")
        print(f"Estimated output tokens: {totalOut}")
        return

    apiKey = config_utils.loadApiKey()
    if not apiKey:
        print("Error: API key required.")
        return

    cardType = args.type.capitalize() if args.type else ui_utils.selectCardType()
    useThinking = (args.mode == "thinking") if args.mode else ui_utils.selectThinkingMode()
    
    if len(texts) > 1:
        outputMode = args.output if args.output else ui_utils.selectOutputMode()
    else:
        outputMode = "separate"

    import httpx
    from openai import OpenAI
    
    timeout = 600.0 if useThinking else 120.0
    httpClient = httpx.Client(timeout=timeout)
    client = OpenAI(api_key=apiKey, base_url="https://api.deepseek.com", http_client=httpClient)
    
    try:
        summary = processFiles(
            texts,
            names,
            cardType,
            useThinking,
            outputMode,
            client,
            maxChunks=args.max_chunks if args.max_chunks > 0 else None,
            outputBaseDir=BASE_DIR,
            tagPrefix=args.tag_prefix,
            tagSuffix=args.tag_suffix
        )
    finally:
        httpClient.close()

    selectedCost = thinkCost if useThinking else regCost
    print("\n--- Run Summary ---")
    print(f"Files processed: {summary['files_total']}")
    print(f"Files with cards: {summary['files_with_cards']}")
    print(f"Chunks total: {summary['chunks_total']}")
    print(f"Chunks succeeded: {summary['chunks_succeeded']}")
    print(f"Chunks failed: {summary['chunks_failed']}")
    print(f"Cards kept: {summary['cards_valid']}")
    print(f"Dropped invalid cards: {summary['cards_invalid']}")
    print(f"Dropped duplicate cards: {summary['cards_duplicates']}")
    print(f"Estimated run cost ({'thinking' if useThinking else 'regular'}): ${selectedCost:.4f}")
    if summary["output_files"]:
        print("Output files:")
        for outputPath in summary["output_files"]:
            print(f"- {outputPath}")
    
    print("\n--- Complete ---")

if __name__ == "__main__":
    main()