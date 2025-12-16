import re
import time

PRICING = {
    "thinking": {"input": 0.55, "output": 2.19},
    "regular": {"input": 0.14, "output": 0.28}
}

def estimateCost(inputTokens, outputTokens, useThinking):
    rates = PRICING["thinking"] if useThinking else PRICING["regular"]
    inputCost = (inputTokens / 1000000) * rates["input"]
    outputCost = (outputTokens / 1000000) * rates["output"]
    return inputCost + outputCost

def estimateTokensFromText(text):
    wordCount = len(text.split())
    return (int(wordCount * 1.3), int(wordCount * 0.5))

def getSystemPrompt(cardType):
    basePrompt = """You are an expert academic scholar in the specific field of the provided text. 
First, analyze the input to determine the domain (e.g., Biology, Computer Science, History, Physics).
Then, adopt the persona of a rigorous professor in that field.

Your goal is to extract high-yield information from the source material (textbook, notes, or slides) and convert it into Anki flashcards.

RULES:
1. IGNORE non-content text: administrative details, due dates, assignments, syllabus info, headers/footers, or casual conversation.
2. FOCUS on: definitions, complex mechanisms, cause-and-effect relationships, and core principles.
3. OUTPUT: Return ONLY a raw text list of cards separated by newlines. No conversational filler."""
    
    if cardType == "Cloze":
        return basePrompt + "\n4. FORMAT: strictly Anki Cloze: {{c1::Hidden Answer}}."
    else:
        return basePrompt + "\n4. FORMAT: Basic cards with front and back separated by a tab character. Format: FrontText\tBackText"

def stripMarkdownFences(text):
    if not text:
        return text
    pattern = r'^```[\w]*\n?|```$'
    cleaned = re.sub(pattern, '', text, flags=re.MULTILINE)
    return cleaned.strip()

def generateAnkiCards(rawText, apiKey, cardType="Cloze", useThinking=False, client=None, maxRetries=3):
    systemPrompt = getSystemPrompt(cardType)
    userMessage = "Here is the material: \n" + rawText
    modelName = "deepseek-reasoner" if useThinking else "deepseek-chat"
    
    generatedContent = None
    isSuccess = False
    
    for attempt in range(maxRetries):
        try:
            responseObj = client.chat.completions.create(
                model=modelName,
                messages=[
                    {"role": "system", "content": systemPrompt},
                    {"role": "user", "content": userMessage}
                ],
                stream=False
            )
            
            generatedContent = responseObj.choices[0].message.content
            generatedContent = stripMarkdownFences(generatedContent)
            isSuccess = True
            break
            
        except KeyboardInterrupt:
            print("\nCancelled by user.")
            return (False, None)
            
        except Exception as errorObj:
            errStr = str(errorObj).lower()
            isTimeout = "timeout" in errStr or "timed out" in errStr
            
            if attempt < maxRetries - 1:
                waitTime = 2 ** (attempt + 1)
                if isTimeout:
                    print(f"Timeout - retrying in {waitTime}s...")
                else:
                    print(f"Error - retry {attempt + 1}/{maxRetries} in {waitTime}s...")
                time.sleep(waitTime)
            else:
                if isTimeout:
                    print(f"Request timed out after {maxRetries} attempts.")
                else:
                    print(f"Failed after {maxRetries} attempts: {errorObj}")
                isSuccess = False

    return (isSuccess, generatedContent)