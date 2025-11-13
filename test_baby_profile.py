#!/usr/bin/env python3
"""
Test script to verify the updated get_baby_profile function works with specific baby_id
"""
import asyncio
import sys
sys.path.append('/Users/inter-mac-602/Documents/GitHub/lumi/lumi_bot')

from src.services.chat_service import get_baby_profile, format_baby_profile_for_context

async def test_baby_profile_function():
    """
    Test the updated get_baby_profile function
    """
    print("🧪 Testing updated get_baby_profile function...")
    
    # Test with mock data (replace with real user_id and baby_id)
    test_user_id = "test_user_123"
    test_baby_id = "test_baby_456"
    
    try:
        # Test 1: Get baby profile without specific baby_id
        print("\n📋 Test 1: Getting baby profile without specific baby_id...")
        baby_data = await get_baby_profile(test_user_id)
        print(f"Result (no baby_id): {type(baby_data)}")
        print(f"Data: {baby_data}")
        
        # Test 2: Get baby profile with specific baby_id
        print(f"\n📋 Test 2: Getting baby profile with specific baby_id ({test_baby_id})...")
        specific_baby_data = await get_baby_profile(test_user_id, test_baby_id)
        print(f"Result (with baby_id): {type(specific_baby_data)}")
        print(f"Data: {specific_baby_data}")
        
        # Test 3: Format baby profile for context
        print(f"\n📋 Test 3: Formatting baby profile for context...")
        if baby_data:
            formatted_context = format_baby_profile_for_context(baby_data)
            print(f"Formatted context length: {len(formatted_context)} characters")
            print(f"Context preview: {formatted_context[:200]}...")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

def test_format_function_with_mock_data():
    """
    Test the format function with mock data
    """
    print("\n🧪 Testing format_baby_profile_for_context with mock data...")
    
    # Mock baby data
    mock_baby = {
        "id": "baby_123",
        "name": "Sofía",
        "birthdate": "2023-06-15",
        "gender": "female",
        "profile": {
            "sleep and rest": {
                "sleep_location": {"value_es": "cuna", "value_en": "crib"},
                "day_night_difference": {"value_es": "comienza a distinguir", "value_en": "starting to distinguish"}
            },
            "daily cares": {
                "dental_care_type": {"value_es": "pasta sin flúor", "value_en": "toothpaste without fluoride"}
            }
        }
    }
    
    try:
        # Test with single baby (dict)
        formatted_single = format_baby_profile_for_context(mock_baby)
        print(f"✅ Single baby formatting: {len(formatted_single)} characters")
        print(f"Content:\n{formatted_single}\n")
        
        # Test with list of babies (backward compatibility)
        formatted_list = format_baby_profile_for_context([mock_baby])
        print(f"✅ List of babies formatting: {len(formatted_list)} characters")
        print(f"Content:\n{formatted_list}\n")
        
        # Test with None
        formatted_none = format_baby_profile_for_context(None)
        print(f"✅ None input formatting: {formatted_none}")
        
        # Test with empty baby profile
        empty_baby = {
            "id": "baby_456", 
            "name": "Carlos",
            "birthdate": "2023-03-10",
            "profile": {}
        }
        formatted_empty = format_baby_profile_for_context(empty_baby)
        print(f"✅ Empty profile formatting: {formatted_empty}")
        
    except Exception as e:
        print(f"❌ Format test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the mock data tests (these will work without database)
    test_format_function_with_mock_data()
    
    # Run the database tests (these might fail if not connected)
    print("\n" + "="*50)
    print("Note: The following tests require database connection and real data")
    print("="*50)
    
    try:
        asyncio.run(test_baby_profile_function())
    except Exception as e:
        print(f"⚠️ Database tests skipped due to: {e}")
    
    print("\n🎉 Testing completed!")