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

def _classifyApiError(errorObj):
    errStr = str(errorObj).lower()

    if "authentication" in errStr or "invalid api key" in errStr or "unauthorized" in errStr:
        return "auth"
    if "model" in errStr and "not found" in errStr:
        return "config"
    if "bad request" in errStr or "invalid_request_error" in errStr:
        return "config"
    if "rate limit" in errStr or "too many requests" in errStr or "429" in errStr:
        return "rate_limit"
    if "timeout" in errStr or "timed out" in errStr:
        return "timeout"
    if "connection" in errStr or "temporar" in errStr or "service unavailable" in errStr:
        return "transient"
    return "unknown"

def _isRetryableError(errorKind):
    return errorKind in {"timeout", "transient", "rate_limit", "unknown"}

def generateAnkiCards(rawText, cardType="Cloze", useThinking=False, client=None, maxRetries=3):
    if client is None:
        return (False, "API client not configured.")

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

            if not getattr(responseObj, "choices", None):
                return (False, "API returned no choices.")

            firstChoice = responseObj.choices[0]
            message = getattr(firstChoice, "message", None)
            generatedContent = getattr(message, "content", None)
            generatedContent = stripMarkdownFences(generatedContent)
            if not generatedContent:
                return (False, "API returned empty content.")
            isSuccess = True
            break
            
        except KeyboardInterrupt:
            print("\nCancelled by user.")
            return (False, None)
            
        except Exception as errorObj:
            errorKind = _classifyApiError(errorObj)
            retryable = _isRetryableError(errorKind)

            if not retryable:
                if errorKind == "auth":
                    return (False, "Authentication failed. Check DEEPSEEK_API_KEY.")
                if errorKind == "config":
                    return (False, f"Configuration error: {errorObj}")
                return (False, f"Non-retryable API error: {errorObj}")

            if attempt < maxRetries - 1 and retryable:
                waitTime = 2 ** (attempt + 1)
                if errorKind == "timeout":
                    print(f"Timeout - retrying in {waitTime}s...")
                elif errorKind == "rate_limit":
                    print(f"Rate limit hit: retrying in {waitTime}s...")
                else:
                    print(f"Error - retry {attempt + 1}/{maxRetries} in {waitTime}s...")
                time.sleep(waitTime)
            else:
                if errorKind == "timeout":
                    print(f"Request timed out after {maxRetries} attempts.")
                elif errorKind == "rate_limit":
                    print(f"Rate limit persisted after {maxRetries} attempts.")
                else:
                    print(f"Failed after {maxRetries} attempts: {errorObj}")
                return (False, str(errorObj))

    return (isSuccess, generatedContent)