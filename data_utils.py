import os
import csv
import re

def ensureOutputFolder():
    targetFolder = "Output"
    if not os.path.exists(targetFolder):
        os.makedirs(targetFolder)
    return targetFolder

def saveToCsv(cardContent, originalFileName, cardType="Cloze"):
    baseName = os.path.splitext(originalFileName)[0]
    outputName = baseName + "_cards.csv"
    targetFolder = ensureOutputFolder()
    outputPath = os.path.join(targetFolder, outputName)
    
    try:
        with open(outputPath, mode='w', newline='', encoding='utf-8-sig') as fileObj:
            csvWriter = csv.writer(fileObj)
            linesList = cardContent.split("\n")
            
            for lineItem in linesList:
                lineItem = lineItem.strip()
                if not lineItem:
                    continue
                    
                if cardType == "Basic" and "\t" in lineItem:
                    parts = lineItem.split("\t", 1)
                    csvWriter.writerow([parts[0], parts[1] if len(parts) > 1 else ""])
                else:
                    csvWriter.writerow([lineItem])
        
        print(f"Saved: {outputPath}")
        return True
        
    except Exception as errorObj:
        print(f"Write Error: {errorObj}")
        return False

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
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    currentChunk = []
    currentWordCount = 0
    
    for sentence in sentences:
        sentenceWords = sentence.split()
        sentenceLen = len(sentenceWords)
        
        if currentWordCount + sentenceLen > maxWords and currentChunk:
            chunks.append(" ".join(currentChunk))
            currentChunk = []
            currentWordCount = 0
        
        currentChunk.append(sentence)
        currentWordCount += sentenceLen
    
    if currentChunk:
        chunks.append(" ".join(currentChunk))
    
    return chunks if chunks else [""]

def saveCombinedCsv(allCardsData, cardType, outputFileName="combined_cards.csv"):
    targetFolder = ensureOutputFolder()
    outputPath = os.path.join(targetFolder, outputFileName)
    
    try:
        with open(outputPath, mode='w', newline='', encoding='utf-8-sig') as fileObj:
            csvWriter = csv.writer(fileObj)
            
            for fileName, cardContent in allCardsData:
                tag = os.path.splitext(fileName)[0]
                
                for line in cardContent.split("\n"):
                    line = line.strip()
                    if not line:
                        continue
                        
                    if cardType == "Cloze":
                        csvWriter.writerow([line, tag])
                    else:
                        parts = line.split("\t", 1)
                        front = parts[0]
                        back = parts[1] if len(parts) > 1 else ""
                        csvWriter.writerow([front, back, tag])
        
        print(f"Saved: {outputPath}")
        return True
        
    except Exception as e:
        print(f"Write Error: {e}")
        return False