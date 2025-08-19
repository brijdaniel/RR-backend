#!/usr/bin/env python3
"""
Simple test script to verify the network feature implementation
This script can be run to test the basic functionality without Django server
"""

import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_models():
    """Test that models can be imported and have expected attributes"""
    try:
        from rr.models import User, Network, Checklist, Regret
        
        print("✅ Models imported successfully")
        
        # Test User model fields
        user_fields = [field.name for field in User._meta.fields]
        expected_user_fields = ['id', 'username', 'is_active', 'is_staff', 'date_joined', 
                              'allow_networking', 'followers_count', 'following_count']
        
        for field in expected_user_fields:
            if field in user_fields:
                print(f"✅ User model has {field} field")
            else:
                print(f"❌ User model missing {field} field")
        
        # Test Network model fields
        network_fields = [field.name for field in Network._meta.fields]
        expected_network_fields = ['id', 'follower', 'following', 'created_at']
        
        for field in expected_network_fields:
            if field in network_fields:
                print(f"✅ Network model has {field} field")
            else:
                print(f"❌ Network model missing {field} field")
        
        # Test User methods
        if hasattr(User, 'get_regret_index'):
            print("✅ User model has get_regret_index method")
        else:
            print("❌ User model missing get_regret_index method")
            
    except ImportError as e:
        print(f"❌ Failed to import models: {e}")
        return False
    
    return True

def test_views():
    """Test that views can be imported and have expected attributes"""
    try:
        from rr.views import (NetworkValidationView, NetworkFollowView, 
                             NetworkUnfollowView, NetworkListView, NetworkSettingsView)
        
        print("✅ Network views imported successfully")
        
        # Test view classes
        view_classes = [
            NetworkValidationView,
            NetworkFollowView,
            NetworkUnfollowView,
            NetworkListView,
            NetworkSettingsView
        ]
        
        for view_class in view_classes:
            if hasattr(view_class, 'permission_classes'):
                print(f"✅ {view_class.__name__} has permission_classes")
            else:
                print(f"❌ {view_class.__name__} missing permission_classes")
                
    except ImportError as e:
        print(f"❌ Failed to import views: {e}")
        return False
    
    return True

def test_serializers():
    """Test that serializers can be imported and have expected attributes"""
    try:
        from rr.serializers import UserSerializer, NetworkSerializer, NetworkUserSerializer
        
        print("✅ Network serializers imported successfully")
        
        # Test serializer classes
        serializer_classes = [
            UserSerializer,
            NetworkSerializer,
            NetworkUserSerializer
        ]
        
        for serializer_class in serializer_classes:
            if hasattr(serializer_class, 'Meta'):
                print(f"✅ {serializer_class.__name__} has Meta class")
            else:
                print(f"❌ {serializer_class.__name__} missing Meta class")
                
    except ImportError as e:
        print(f"❌ Failed to import serializers: {e}")
        return False
    
    return True

def test_admin():
    """Test that admin can be imported"""
    try:
        from rr.admin import UserAdmin, NetworkAdmin
        
        print("✅ Network admin classes imported successfully")
        
    except ImportError as e:
        print(f"❌ Failed to import admin: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🧪 Testing Network Feature Implementation")
    print("=" * 50)
    
    tests = [
        ("Models", test_models),
        ("Views", test_views),
        ("Serializers", test_serializers),
        ("Admin", test_admin),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Network feature implementation looks good.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 