#!/usr/bin/env python3
"""
Test script to verify the navigation sidebar and thumbnail layout fixes.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from browse_tab_v2.components.modern_navigation_sidebar import SectionDataExtractor
from browse_tab_v2.core.state import SequenceModel

def test_type3_letter_extraction():
    """Test Type 3 letter extraction with dash suffixes."""
    print("🧪 Testing Type 3 letter extraction...")
    
    # Create test sequences with Type 3 letters
    test_sequences = [
        SequenceModel(
            id="1", name="W-ABC", thumbnails=[], difficulty=1, length=3,
            author="Test", tags=[]
        ),
        SequenceModel(
            id="2", name="X-DEF", thumbnails=[], difficulty=2, length=4,
            author="Test", tags=[]
        ),
        SequenceModel(
            id="3", name="Y-GHI", thumbnails=[], difficulty=1, length=5,
            author="Test", tags=[]
        ),
        SequenceModel(
            id="4", name="ABCD", thumbnails=[], difficulty=3, length=4,
            author="Test", tags=[]
        ),
        SequenceModel(
            id="5", name="BCDE", thumbnails=[], difficulty=2, length=3,
            author="Test", tags=[]
        ),
        SequenceModel(
            id="6", name="Z-JKL", thumbnails=[], difficulty=1, length=6,
            author="Test", tags=[]
        ),
    ]
    
    # Test the extraction
    extractor = SectionDataExtractor()
    sections = extractor.extract_alphabetical_sections(test_sequences)
    
    print(f"📋 Extracted sections: {sections}")
    
    # Verify Type 3 letters are properly extracted
    expected_sections = ["A", "B", "W-", "X-", "Y-", "Z-"]
    
    success = True
    for expected in expected_sections:
        if expected not in sections:
            print(f"❌ Missing expected section: {expected}")
            success = False
        else:
            print(f"✅ Found expected section: {expected}")
    
    # Test individual letter extraction
    print("\n🔍 Testing individual letter extraction:")
    test_words = ["W-ABC", "X-DEF", "ABCD", "Y-GHI", "Z-JKL", "BCDE"]
    for word in test_words:
        extracted = extractor._extract_first_letter(word)
        print(f"  '{word}' -> '{extracted}'")
    
    return success

def test_section_matching():
    """Test section matching logic."""
    print("\n🎯 Testing section matching logic...")
    
    from browse_tab_v2.components.modern_navigation_sidebar import ModernNavigationSidebar
    from browse_tab_v2.core.interfaces import BrowseTabConfig
    
    config = BrowseTabConfig()
    sidebar = ModernNavigationSidebar(config)
    
    # Create test sequences
    test_sequences = [
        SequenceModel(
            id="1", name="W-ABC", thumbnails=[], difficulty=1, length=3,
            author="Test", tags=[]
        ),
        SequenceModel(
            id="2", name="W-DEF", thumbnails=[], difficulty=2, length=4,
            author="Test", tags=[]
        ),
        SequenceModel(
            id="3", name="ABCD", thumbnails=[], difficulty=1, length=5,
            author="Test", tags=[]
        ),
    ]
    
    # Update sidebar with sequences
    sidebar.update_for_sequences(test_sequences, "alphabetical")
    
    # Test section matching
    w_dash_sequences = sidebar.get_sequences_for_section("W-")
    a_sequences = sidebar.get_sequences_for_section("A")
    
    print(f"📊 Sequences for 'W-' section: {len(w_dash_sequences)}")
    for seq in w_dash_sequences:
        print(f"  - {seq.name}")
    
    print(f"📊 Sequences for 'A' section: {len(a_sequences)}")
    for seq in a_sequences:
        print(f"  - {seq.name}")
    
    # Verify correct matching
    success = True
    if len(w_dash_sequences) != 2:
        print(f"❌ Expected 2 sequences for 'W-', got {len(w_dash_sequences)}")
        success = False
    else:
        print("✅ Correct number of sequences for 'W-' section")
    
    if len(a_sequences) != 1:
        print(f"❌ Expected 1 sequence for 'A', got {len(a_sequences)}")
        success = False
    else:
        print("✅ Correct number of sequences for 'A' section")
    
    return success

def test_grid_layout_fixes():
    """Test grid layout fixes for 25% width scaling."""
    print("\n📐 Testing grid layout fixes...")
    
    from browse_tab_v2.components.responsive_thumbnail_grid import ResponsiveThumbnailGrid
    from browse_tab_v2.core.interfaces import BrowseTabConfig
    
    config = BrowseTabConfig()
    grid = ResponsiveThumbnailGrid(config)
    
    # Test column calculation
    grid._calculate_optimal_columns()
    
    print(f"📏 Column count: {grid._column_count}")
    
    if grid._column_count == 4:
        print("✅ Grid correctly set to 4 columns for 25% width scaling")
        return True
    else:
        print(f"❌ Expected 4 columns, got {grid._column_count}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting navigation and layout fixes tests...\n")
    
    results = []
    
    # Test Type 3 letter extraction
    results.append(test_type3_letter_extraction())
    
    # Test section matching
    results.append(test_section_matching())
    
    # Test grid layout fixes
    results.append(test_grid_layout_fixes())
    
    # Summary
    print(f"\n📊 Test Results:")
    print(f"✅ Passed: {sum(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}")
    
    if all(results):
        print("\n🎉 All tests passed! Navigation and layout fixes are working correctly.")
        return 0
    else:
        print("\n⚠️ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
