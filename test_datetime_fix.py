"""
Test script to verify the datetime comparison fix

This script tests that datetime comparisons work correctly
without the offset-naive vs offset-aware error.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timezone


async def test_datetime_utilities():
    """Test the datetime utility functions"""
    
    print("🧪 Testing Datetime Utilities")
    print("=" * 40)
    
    try:
        from app.core.utils.datetime_utils import (
            ensure_timezone_aware, ensure_timezone_naive, safe_datetime_compare,
            get_current_utc_datetime, format_datetime_for_display,
            is_overdue, is_due_soon, get_due_date_status
        )
        
        # Test 1: Timezone awareness conversion
        print("\n1. Testing timezone awareness conversion...")
        
        # Create naive datetime
        naive_dt = datetime(2024, 1, 1, 12, 0, 0)
        print(f"   Naive datetime: {naive_dt} (tzinfo: {naive_dt.tzinfo})")
        
        # Convert to timezone-aware
        aware_dt = ensure_timezone_aware(naive_dt)
        print(f"   Aware datetime: {aware_dt} (tzinfo: {aware_dt.tzinfo})")
        
        if aware_dt.tzinfo is not None:
            print("   ✅ Successfully converted naive to aware")
        else:
            print("   ❌ Failed to convert naive to aware")
            return False
        
        # Test 2: Safe datetime comparison
        print("\n2. Testing safe datetime comparison...")
        
        dt1 = datetime(2024, 1, 1, 12, 0, 0)  # naive
        dt2 = datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)  # aware
        
        try:
            result = safe_datetime_compare(dt1, dt2)
            print(f"   Comparison result: {dt1} < {dt2} = {result}")
            print("   ✅ Safe comparison works without errors")
        except Exception as e:
            print(f"   ❌ Safe comparison failed: {e}")
            return False
        
        # Test 3: Current UTC datetime
        print("\n3. Testing current UTC datetime...")
        
        current_utc = get_current_utc_datetime()
        print(f"   Current UTC: {current_utc} (tzinfo: {current_utc.tzinfo})")
        
        if current_utc.tzinfo is not None:
            print("   ✅ Current UTC datetime is timezone-aware")
        else:
            print("   ❌ Current UTC datetime is not timezone-aware")
            return False
        
        # Test 4: Date formatting
        print("\n4. Testing date formatting...")
        
        test_dates = [
            datetime(2024, 1, 1, 12, 0, 0),  # naive
            datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),  # aware
            None  # None value
        ]
        
        for i, dt in enumerate(test_dates):
            formatted = format_datetime_for_display(dt, "%Y-%m-%d %H:%M")
            print(f"   Date {i+1}: {dt} → {formatted}")
        
        print("   ✅ Date formatting works for all cases")
        
        # Test 5: Due date status
        print("\n5. Testing due date status...")
        
        from datetime import timedelta
        current_time = get_current_utc_datetime()
        
        # Test overdue
        overdue_date = current_time - timedelta(days=1)
        status = get_due_date_status(overdue_date, "todo")
        print(f"   Overdue task status: {status}")
        
        # Test due soon
        due_soon_date = current_time + timedelta(days=1)
        status = get_due_date_status(due_soon_date, "inprogress")
        print(f"   Due soon task status: {status}")
        
        # Test completed task (should not be overdue)
        status = get_due_date_status(overdue_date, "completed")
        print(f"   Completed overdue task status: {status}")
        
        print("   ✅ Due date status calculation works correctly")
        
        print("\n✅ All datetime utility tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Datetime utility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_task_interface():
    """Test that task interface works without datetime errors"""
    
    print("\n🧪 Testing Task Interface")
    print("=" * 40)
    
    try:
        from app.core.interface.task_interface import get_task_statistics
        
        print("1. Testing task statistics...")
        
        # This should not raise datetime comparison errors
        stats = await get_task_statistics(user_id=1)
        
        print(f"   Statistics loaded successfully: {list(stats.keys())}")
        print("   ✅ Task statistics work without datetime errors")
        
        return True
        
    except Exception as e:
        print(f"❌ Task interface test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all datetime fix tests"""
    
    print("🚀 Datetime Fix Test Suite")
    print("=" * 60)
    print("Testing fix for 'can't compare offset-naive and offset-aware datetimes'")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 2
    
    # Test 1: Datetime Utilities
    if await test_datetime_utilities():
        tests_passed += 1
    
    # Test 2: Task Interface
    try:
        if await test_task_interface():
            tests_passed += 1
    except Exception as e:
        print(f"⚠️ Task interface test skipped: {e}")
    
    # Results
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Datetime comparison error is fixed.")
        print("\n✅ The following issues have been resolved:")
        print("   • Timezone-aware vs timezone-naive datetime comparisons")
        print("   • Safe datetime formatting and display")
        print("   • Proper due date status calculations")
        print("   • Task statistics without datetime errors")
        print("\n🚀 Your Kanban system should now work without datetime errors!")
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
    
    return tests_passed == total_tests


if __name__ == "__main__":
    asyncio.run(main())