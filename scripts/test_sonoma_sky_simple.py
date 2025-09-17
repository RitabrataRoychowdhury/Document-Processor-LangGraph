#!/usr/bin/env python3
"""
Simple test to verify Sonoma Sky Alpha API connectivity.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("⚠️ python-dotenv not available, trying to load .env manually")
    # Manual .env loading
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
        print("✅ Manually loaded .env file")

try:
    from openai import OpenAI
    print("✅ OpenAI library is available")
except ImportError:
    print("❌ OpenAI library not found. Installing...")
    os.system("pip install openai")
    from openai import OpenAI

def test_sonoma_sky_api():
    """Test Sonoma Sky Alpha API with simple text request."""
    
    # Check API key
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in environment")
        print("Please set the API key: export OPENROUTER_API_KEY=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")
        return False
    
    print(f"✅ API Key found: {api_key[:20]}...")
    
    try:
        # Create OpenAI client for OpenRouter
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        
        print("🤖 Testing Sonoma Sky Alpha model...")
        
        # Make a simple API call
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://qme-system.local",
                "X-Title": "QME Document Extraction System",
            },
            model="openrouter/sonoma-sky-alpha",
            messages=[
                {
                    "role": "user",
                    "content": "Please respond with a JSON object containing 'status': 'success' and 'message': 'Sonoma Sky Alpha is working correctly'"
                }
            ],
            max_tokens=100,
            temperature=0.1
        )
        
        response_content = completion.choices[0].message.content
        print(f"📝 Response: {response_content}")
        
        # Check if response contains expected content
        if "success" in response_content.lower():
            print("✅ Sonoma Sky Alpha is working correctly!")
            return True
        else:
            print("⚠️ Unexpected response format, but API is responding")
            return True
            
    except Exception as e:
        print(f"❌ Error testing Sonoma Sky Alpha: {str(e)}")
        return False

def test_vision_capability():
    """Test Sonoma Sky Alpha vision capability with a sample image."""
    
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        return False
    
    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        
        print("👁️ Testing Sonoma Sky Alpha vision capabilities...")
        
        # Test with a sample image URL (as shown in OpenRouter docs)
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://qme-system.local",
                "X-Title": "QME Document Extraction System",
            },
            model="openrouter/sonoma-sky-alpha",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "What do you see in this image? Respond briefly."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
                            }
                        }
                    ]
                }
            ],
            max_tokens=150
        )
        
        response_content = completion.choices[0].message.content
        print(f"👁️ Vision Response: {response_content}")
        
        if len(response_content) > 10:  # Got a meaningful response
            print("✅ Sonoma Sky Alpha vision capabilities are working!")
            return True
        else:
            print("⚠️ Vision response seems too short")
            return False
            
    except Exception as e:
        print(f"❌ Error testing vision capabilities: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Sonoma Sky Alpha Simple Test")
    print("=" * 40)
    
    # Test basic API
    text_success = test_sonoma_sky_api()
    print()
    
    # Test vision if basic API works
    if text_success:
        vision_success = test_vision_capability()
    else:
        vision_success = False
    
    print("\n" + "=" * 40)
    print("📊 Test Results:")
    print(f"  Text API: {'✅ PASS' if text_success else '❌ FAIL'}")
    print(f"  Vision API: {'✅ PASS' if vision_success else '❌ FAIL'}")
    
    if text_success and vision_success:
        print("🎉 Sonoma Sky Alpha is fully operational!")
    elif text_success:
        print("⚠️ Text API working, vision needs verification")
    else:
        print("❌ API connection failed - check your API key")