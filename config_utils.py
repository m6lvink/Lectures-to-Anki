import getpass
import os
from dotenv import load_dotenv

PLACEHOLDER_VALUES = {"your_key_here", "PUT KEY HERE", ""}

def loadApiKey():
    # Load .env near this script so caller CWD doesnt mattr
    baseDir = os.path.dirname(os.path.abspath(__file__))
    envPath = os.path.join(baseDir, ".env")
    load_dotenv(dotenv_path=envPath)
    
    apiKey = os.environ.get("DEEPSEEK_API_KEY")
    
    if not apiKey or apiKey in PLACEHOLDER_VALUES:
        print("No API key found in environment or .env file")
        apiKey = getpass.getpass("Enter DeepSeek API Key: ").strip()
        
        if not apiKey:
            return None
        
    return apiKey

