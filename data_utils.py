import os
import csv
import re

def ensureOutputFolder(baseDir=None):
    if baseDir is None:
        baseDir = os.path.dirname(os.path.abspath(__file__))
    targetFolder = os.path.join(baseDir, "Output")
    if not os.path.exists(targetFolder):
        os.makedirs(targetFolder)
    return targetFolder

def _isValidCloze(lineItem):
    return bool(re.search(r"\{\{c\d+::.+?\}\}", lineItem))

def _isValidBasic(lineItem):
    if "\t" not in lineItem:
        return False
    front, back = lineItem.split("\t", 1)
    return bool(front.strip()) and bool(back.strip())

def _normalizeLineForDedup(lineItem):
    return re.sub(r"\s+", " ", lineItem).strip().lower()

def cleanCardLines(cardContent, cardType="Cloze"):
    cardType = (cardType or "Cloze").capitalize()
    validLines = []
    seen = set()
    invalidCount = 0
    duplicateCount = 0

    for lineItem in cardContent.split("\n"):
        lineItem = lineItem.strip()
        if not lineItem:
            continue

        isValid = _isValidBasic(lineItem) if cardType == "Basic" else _isValidCloze(lineItem)
        if not isValid:
            invalidCount += 1
            continue

        lineKey = _normalizeLineForDedup(lineItem)
        if lineKey in seen:
            duplicateCount += 1
            continue

        seen.add(lineKey)
        validLines.append(lineItem)

    stats = {
        "valid": len(validLines),
        "invalid": invalidCount,
        "duplicates": duplicateCount,
    }
    return validLines, stats

def saveToCsv(cardContent, originalFileName, cardType="Cloze", baseDir=None, tagOverride=None):
    baseName = os.path.splitext(originalFileName)[0]
    outputName = baseName + "_cards.csv"
    targetFolder = ensureOutputFolder(baseDir)
    outputPath = os.path.join(targetFolder, outputName)
    
    try:
        cleanLines, stats = cleanCardLines(cardContent, cardType)
        with open(outputPath, mode='w', newline='', encoding='utf-8-sig') as fileObj:
            csvWriter = csv.writer(fileObj)

            for lineItem in cleanLines:
                if cardType == "Basic" and "\t" in lineItem:
                    parts = lineItem.split("\t", 1)
                    row = [parts[0], parts[1] if len(parts) > 1 else ""]
                    if tagOverride:
                        row.append(tagOverride)
                    csvWriter.writerow(row)
                else:
                    row = [lineItem]
                    if tagOverride:
                        row.append(tagOverride)
                    csvWriter.writerow(row)
        
        print(f"Saved: {outputPath}")
        print(
            f"Validation: kept={stats['valid']}, "
            f"dropped_invalid={stats['invalid']}, dropped_duplicates={stats['duplicates']}"
        )
        return True, outputPath, stats
        
    except Exception as errorObj:
        print(f"Write Error: {errorObj}")
        return False, None, {"valid": 0, "invalid": 0, "duplicates": 0}

def parseUserSelection(inputString, totalCount):
    seen = set()
    result = []
    
    for part in inputString.split(","):
        part = part.strip()
        
        if "-" in part and not part.startswith("-"):
            rangeParts = part.split("-")
            if len(rangeParts) == 2 and rangeParts[0].isdigit() and rangeParts[1].isdigit():
                start = int(rangeParts[0]) - 1
                end = int(rangeParts[1]) - 1
                for idx in range(start, end + 1):
                    if 0 <= idx < totalCount and idx not in seen:
                        seen.add(idx)
                        result.append(idx)
                continue
        
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < totalCount and idx not in seen:
                seen.add(idx)
                result.append(idx)
    
    return result

def chunkText(text, maxWords=800):
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n+', text) if p.strip()]
    if not paragraphs:
        return [""]

    chunks = []
    currentChunkParts = []
    currentWordCount = 0

    for paragraph in paragraphs:
        paragraphWords = paragraph.split()
        paragraphLen = len(paragraphWords)

        if paragraphLen > maxWords:
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            oversizedPart = []
            oversizedCount = 0
            for sentence in sentences:
                sentenceLen = len(sentence.split())
                if oversizedPart and oversizedCount + sentenceLen > maxWords:
                    if currentChunkParts:
                        chunks.append("\n\n".join(currentChunkParts))
                        currentChunkParts = []
                        currentWordCount = 0
                    chunks.append(" ".join(oversizedPart))
                    oversizedPart = []
                    oversizedCount = 0
                oversizedPart.append(sentence)
                oversizedCount += sentenceLen

            if oversizedPart:
                if currentWordCount + oversizedCount > maxWords and currentChunkParts:
                    chunks.append("\n\n".join(currentChunkParts))
                    currentChunkParts = []
                    currentWordCount = 0
                currentChunkParts.append(" ".join(oversizedPart))
                currentWordCount += oversizedCount
            continue

        if currentWordCount + paragraphLen > maxWords and currentChunkParts:
            chunks.append("\n\n".join(currentChunkParts))
            currentChunkParts = []
            currentWordCount = 0

        currentChunkParts.append(paragraph)
        currentWordCount += paragraphLen

    if currentChunkParts:
        chunks.append("\n\n".join(currentChunkParts))

    return chunks if chunks else [""]

def saveCombinedCsv(allCardsData, cardType, outputFileName="combined_cards.csv", baseDir=None):
    targetFolder = ensureOutputFolder(baseDir)
    outputPath = os.path.join(targetFolder, outputFileName)
    
    try:
        aggregateStats = {"valid": 0, "invalid": 0, "duplicates": 0}
        with open(outputPath, mode='w', newline='', encoding='utf-8-sig') as fileObj:
            csvWriter = csv.writer(fileObj)
            
            for item in allCardsData:
                if len(item) == 3:
                    fileName, cardContent, tag = item
                else:
                    fileName, cardContent = item
                    tag = os.path.splitext(fileName)[0]
                cleanLines, stats = cleanCardLines(cardContent, cardType)
                aggregateStats["valid"] += stats["valid"]
                aggregateStats["invalid"] += stats["invalid"]
                aggregateStats["duplicates"] += stats["duplicates"]

                for line in cleanLines:
                    if cardType == "Cloze":
                        csvWriter.writerow([line, tag])
                    else:
                        parts = line.split("\t", 1)
                        front = parts[0]
                        back = parts[1] if len(parts) > 1 else ""
                        csvWriter.writerow([front, back, tag])
        
        print(f"Saved: {outputPath}")
        print(
            f"Validation: kept={aggregateStats['valid']}, "
            f"dropped_invalid={aggregateStats['invalid']}, dropped_duplicates={aggregateStats['duplicates']}"
        )
        return True, outputPath, aggregateStats
        
    except Exception as e:
        print(f"Write Error: {e}")
        return False, None, {"valid": 0, "invalid": 0, "duplicates": 0}