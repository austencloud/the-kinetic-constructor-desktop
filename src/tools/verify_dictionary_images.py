#!/usr/bin/env python3
"""
Dictionary Image Verification Script

This script analyzes the current state of dictionary images to determine
if they contain real kinetic sequence diagrams or blank placeholders.

Usage:
    python -m tools.verify_dictionary_images
"""

import os
import json
import time
from typing import Dict, List, Tuple
from PIL import Image


def verify_dictionary_images() -> Dict:
    """
    Verify the current state of dictionary images.
    
    Returns:
        Dictionary with analysis results
    """
    print("🔍 DICTIONARY IMAGE VERIFICATION")
    print("=" * 50)
    
    try:
        from utils.path_helpers import get_dictionary_path
        dictionary_path = get_dictionary_path()
    except ImportError:
        # Fallback for standalone execution
        dictionary_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'dictionary')
    
    print(f"📁 Dictionary path: {dictionary_path}")
    
    if not os.path.exists(dictionary_path):
        print(f"❌ Dictionary path does not exist: {dictionary_path}")
        return {"error": "Dictionary path not found"}
    
    # Analyze all images
    results = {
        "total_images": 0,
        "blank_gray_images": 0,
        "complex_images": 0,
        "with_metadata": 0,
        "without_metadata": 0,
        "recent_modifications": 0,
        "sample_analysis": [],
        "blank_samples": [],
        "complex_samples": []
    }
    
    current_time = time.time()
    
    print("\n📊 Analyzing all dictionary images...")
    
    for item in os.listdir(dictionary_path):
        item_path = os.path.join(dictionary_path, item)
        if os.path.isdir(item_path):
            png_files = [f for f in os.listdir(item_path) if f.endswith('.png')]
            
            for png_file in png_files:
                image_path = os.path.join(item_path, png_file)
                results["total_images"] += 1
                
                # Analyze individual image
                analysis = _analyze_image(image_path, current_time)
                
                # Update counters
                if analysis["is_blank_gray"]:
                    results["blank_gray_images"] += 1
                    if len(results["blank_samples"]) < 5:
                        results["blank_samples"].append(f"{item}/{png_file}")
                else:
                    results["complex_images"] += 1
                    if len(results["complex_samples"]) < 5:
                        results["complex_samples"].append(f"{item}/{png_file}")
                
                if analysis["has_metadata"]:
                    results["with_metadata"] += 1
                else:
                    results["without_metadata"] += 1
                
                if analysis["recently_modified"]:
                    results["recent_modifications"] += 1
                
                # Store sample analysis
                if len(results["sample_analysis"]) < 10:
                    results["sample_analysis"].append({
                        "path": f"{item}/{png_file}",
                        "analysis": analysis
                    })
    
    # Display results
    _display_verification_results(results)
    
    return results


def _analyze_image(image_path: str, current_time: float) -> Dict:
    """Analyze a single image file."""
    analysis = {
        "is_blank_gray": False,
        "has_metadata": False,
        "recently_modified": False,
        "color_count": 0,
        "size": None,
        "dominant_colors": []
    }
    
    try:
        # Check modification time
        mod_time = os.path.getmtime(image_path)
        analysis["recently_modified"] = (current_time - mod_time) < 3600  # 1 hour
        
        # Analyze image content
        with Image.open(image_path) as img:
            analysis["size"] = img.size
            
            # Check colors
            colors = img.getcolors(maxcolors=256*256*256)
            if colors:
                analysis["color_count"] = len(colors)
                analysis["dominant_colors"] = colors[:3]  # Top 3 colors
                
                # Check for blank gray (240, 240, 240)
                for count, color in colors:
                    if (color == (240, 240, 240, 255) or 
                        color == (240, 240, 240) or
                        (isinstance(color, tuple) and len(color) >= 3 and 
                         color[:3] == (240, 240, 240))):
                        # If this color dominates the image (>80% of pixels)
                        total_pixels = img.size[0] * img.size[1]
                        if count > total_pixels * 0.8:
                            analysis["is_blank_gray"] = True
                        break
            
            # Check metadata
            if hasattr(img, 'text') and 'metadata' in img.text:
                try:
                    metadata = json.loads(img.text['metadata'])
                    if 'sequence' in metadata:
                        analysis["has_metadata"] = True
                except:
                    pass
                    
    except Exception as e:
        analysis["error"] = str(e)
    
    return analysis


def _display_verification_results(results: Dict) -> None:
    """Display the verification results."""
    print("\n📊 VERIFICATION RESULTS")
    print("=" * 50)
    
    total = results["total_images"]
    blank = results["blank_gray_images"]
    complex_imgs = results["complex_images"]
    with_meta = results["with_metadata"]
    without_meta = results["without_metadata"]
    recent = results["recent_modifications"]
    
    print(f"📈 Total images analyzed: {total}")
    print(f"🔲 Blank gray images: {blank} ({blank/total*100:.1f}%)")
    print(f"🎨 Complex images: {complex_imgs} ({complex_imgs/total*100:.1f}%)")
    print(f"📋 With metadata: {with_meta} ({with_meta/total*100:.1f}%)")
    print(f"❓ Without metadata: {without_meta} ({without_meta/total*100:.1f}%)")
    print(f"🕒 Recently modified: {recent}")
    
    # Status assessment
    print(f"\n🎯 STATUS ASSESSMENT:")
    if blank > total * 0.8:
        print("❌ CRITICAL: Most images are blank gray rectangles")
        print("💡 Dictionary regeneration is REQUIRED")
    elif blank > total * 0.5:
        print("⚠️  WARNING: Many images are blank gray rectangles")
        print("💡 Dictionary regeneration is RECOMMENDED")
    elif blank > 0:
        print("⚠️  MIXED: Some images are blank, some are complex")
        print("💡 Partial regeneration may be needed")
    else:
        print("✅ GOOD: No blank gray images detected")
        print("💡 Images appear to contain real content")
    
    # Show samples
    if results["blank_samples"]:
        print(f"\n🔲 BLANK IMAGE SAMPLES:")
        for sample in results["blank_samples"]:
            print(f"   {sample}")
    
    if results["complex_samples"]:
        print(f"\n🎨 COMPLEX IMAGE SAMPLES:")
        for sample in results["complex_samples"]:
            print(f"   {sample}")
    
    # Recent modifications
    if recent > 0:
        print(f"\n🕒 RECENT ACTIVITY:")
        print(f"   {recent} images modified in the last hour")
        print("   This suggests regeneration activity")
    
    # Detailed sample analysis
    if results["sample_analysis"]:
        print(f"\n🔍 DETAILED SAMPLE ANALYSIS:")
        for i, sample in enumerate(results["sample_analysis"][:5]):
            path = sample["path"]
            analysis = sample["analysis"]
            print(f"\n   Sample {i+1}: {path}")
            print(f"      Size: {analysis.get('size', 'unknown')}")
            print(f"      Colors: {analysis.get('color_count', 0)}")
            print(f"      Blank gray: {'Yes' if analysis.get('is_blank_gray') else 'No'}")
            print(f"      Metadata: {'Yes' if analysis.get('has_metadata') else 'No'}")
            print(f"      Recent: {'Yes' if analysis.get('recently_modified') else 'No'}")


def quick_verification() -> bool:
    """
    Quick verification to check if regeneration is needed.
    
    Returns:
        True if images appear to be real diagrams, False if blank/placeholder
    """
    print("🚀 QUICK VERIFICATION")
    print("-" * 30)
    
    results = verify_dictionary_images()
    
    if "error" in results:
        return False
    
    total = results["total_images"]
    blank = results["blank_gray_images"]
    
    if total == 0:
        print("❌ No images found")
        return False
    
    blank_percentage = (blank / total) * 100
    
    print(f"\n🎯 QUICK RESULT: {blank_percentage:.1f}% blank images")
    
    if blank_percentage > 80:
        print("❌ REGENERATION REQUIRED: Most images are blank")
        return False
    elif blank_percentage > 20:
        print("⚠️  REGENERATION RECOMMENDED: Many images are blank")
        return False
    else:
        print("✅ IMAGES LOOK GOOD: Low blank percentage")
        return True


if __name__ == "__main__":
    verify_dictionary_images()
