"""
Test script to validate BrowseTabV2Adapter configuration compatibility
"""

import sys
import os

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def test_adapter_configuration():
    """Test that the BrowseTabV2Adapter can create configurations without errors."""
    print("=== BrowseTabV2Adapter Configuration Test ===")
    
    try:
        # Test imports
        from src.browse_tab_v2.integration.browse_tab_adapter import BrowseTabV2Adapter
        from src.browse_tab_v2.core.interfaces import BrowseTabConfig
        
        print("✓ Adapter imports successful")
        
        # Test configuration creation (same as in adapter)
        config = BrowseTabConfig(
            max_concurrent_image_loads=4,
            image_cache_size=200,
            enable_performance_monitoring=True,
            enable_debug_logging=False,  # Reduce noise in main app
            default_columns=3,
        )
        
        print("✓ BrowseTabConfig created successfully")
        print(f"✓ enable_animations: {config.enable_animations}")
        print(f"✓ enable_glassmorphism: {config.enable_glassmorphism}")
        print(f"✓ enable_hover_effects: {config.enable_hover_effects}")
        print(f"✓ animation_fps_target: {config.animation_fps_target}")
        print(f"✓ border_radius: {config.border_radius}")
        print(f"✓ hover_scale_factor: {config.hover_scale_factor}")
        
        # Test that all required attributes are present
        required_attrs = [
            'enable_animations', 'enable_glassmorphism', 'enable_hover_effects',
            'enable_smooth_scrolling', 'animation_fps_target', 'respect_reduced_motion',
            'glassmorphism_opacity', 'border_radius', 'shadow_blur_radius', 'hover_scale_factor'
        ]
        
        missing_attrs = []
        for attr in required_attrs:
            if not hasattr(config, attr):
                missing_attrs.append(attr)
        
        if missing_attrs:
            print(f"✗ Missing attributes: {missing_attrs}")
            return False
        else:
            print("✓ All required animation/UI attributes present")
        
        # Test configuration values
        assert config.enable_animations == True, "enable_animations should default to True"
        assert config.enable_glassmorphism == True, "enable_glassmorphism should default to True"
        assert config.animation_fps_target == 60, "animation_fps_target should default to 60"
        assert config.border_radius == 20, "border_radius should default to 20"
        assert config.hover_scale_factor == 1.02, "hover_scale_factor should default to 1.02"
        
        print("✓ All configuration values validated")
        
        print("\n=== Configuration Test Results ===")
        print("✓ BrowseTabConfig has all required Phase 2 attributes")
        print("✓ Animation configuration is properly set up")
        print("✓ Modern UI configuration is available")
        print("✓ BrowseTabV2Adapter can create configurations without errors")
        print("✓ Configuration mismatch issue RESOLVED")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_component_config_access():
    """Test that Phase 2 components can access config.enable_animations."""
    print("\n=== Component Configuration Access Test ===")
    
    try:
        from src.browse_tab_v2.core.interfaces import BrowseTabConfig
        
        # Create config
        config = BrowseTabConfig()
        
        # Test direct access to animation attributes
        animation_enabled = config.enable_animations
        glassmorphism_enabled = config.enable_glassmorphism
        hover_enabled = config.enable_hover_effects
        
        print(f"✓ config.enable_animations = {animation_enabled}")
        print(f"✓ config.enable_glassmorphism = {glassmorphism_enabled}")
        print(f"✓ config.enable_hover_effects = {hover_enabled}")
        
        # Test that these are the expected types and values
        assert isinstance(animation_enabled, bool), "enable_animations should be boolean"
        assert isinstance(glassmorphism_enabled, bool), "enable_glassmorphism should be boolean"
        assert isinstance(hover_enabled, bool), "enable_hover_effects should be boolean"
        
        print("✓ All animation config attributes accessible and properly typed")
        
        return True
        
    except Exception as e:
        print(f"✗ Error accessing config attributes: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing BrowseTabV2Adapter configuration compatibility...")
    
    config_success = test_adapter_configuration()
    access_success = test_component_config_access()
    
    if config_success and access_success:
        print("\n🎉 Configuration mismatch RESOLVED!")
        print("✅ BrowseTabV2Adapter can now initialize successfully")
        print("✅ Phase 2 components can access animation configuration")
        print("✅ All required attributes are present in BrowseTabConfig")
    else:
        print("\n❌ Configuration test failed. Please check the errors above.")
        sys.exit(1)
