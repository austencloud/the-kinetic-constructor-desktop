#!/usr/bin/env python3
"""
Example of how to integrate browse tab v2 into the existing application.

This shows how the new browse tab can be used as a drop-in replacement
for the existing browse tab with minimal changes to the main application.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def integrate_browse_tab_v2():
    """
    Example of how to integrate browse tab v2 into the existing application.

    This function shows the minimal changes needed to use the new browse tab
    in place of the existing one.
    """

    print("Browse Tab v2 Integration Example")
    print("=" * 50)

    # Step 1: Import the adapter
    try:
        from browse_tab_v2.integration import create_browse_tab_v2_adapter

        print("✓ Browse tab v2 adapter imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import adapter: {e}")
        return False

    # Step 2: Create mock dependencies (in real app, these would be actual instances)
    class MockJsonManager:
        def __init__(self):
            self.dictionary_path = "dictionary.json"
            self.loader_saver = self

        def load_json_file(self, path):
            return {
                "example_sequence": {
                    "metadata": {
                        "difficulty": 3,
                        "length": 8,
                        "author": "Example Author",
                        "tags": ["example", "demo"],
                        "is_favorite": False,
                    },
                    "thumbnails": ["example.png"],
                    "beats": [{"beat": 1}, {"beat": 2}],
                }
            }

    class MockSettingsManager:
        def __init__(self):
            self.browse_settings = self

        def get_current_section(self):
            return "all"

    # Step 3: Create QApplication (required for Qt widgets)
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Step 4: Create the adapter (this replaces the old browse tab creation)
    try:
        json_manager = MockJsonManager()
        settings_manager = MockSettingsManager()

        # OLD CODE (what you would replace):
        # browse_tab = BrowseTab(json_manager, settings_manager)

        # NEW CODE (drop-in replacement):
        browse_tab_v2 = create_browse_tab_v2_adapter(
            json_manager=json_manager, settings_manager=settings_manager
        )

        print("✓ Browse tab v2 adapter created successfully")

        # The adapter provides the same interface as the old browse tab
        print("✓ Adapter provides compatible interface")

        # Step 5: Connect signals (same as old browse tab)
        def on_sequence_selected(sequence_name):
            print(f"Sequence selected: {sequence_name}")

        def on_filter_changed(filter_data):
            print(f"Filter changed: {filter_data}")

        def on_loading_changed(is_loading):
            print(f"Loading: {is_loading}")

        browse_tab_v2.sequence_selected.connect(on_sequence_selected)
        browse_tab_v2.filter_changed.connect(on_filter_changed)
        browse_tab_v2.loading_changed.connect(on_loading_changed)

        print("✓ Signals connected successfully")

        # Step 6: Use the same methods as old browse tab
        browse_tab_v2.load_sequences()
        browse_tab_v2.search_sequences("example")
        browse_tab_v2.apply_filter("difficulty", 3)

        print("✓ Methods called successfully")

        # Step 7: The adapter can be used in layouts just like the old browse tab
        # layout.addWidget(browse_tab_v2)  # Same as old browse tab

        print("✓ Integration example completed successfully")
        print("\nBenefits of the new architecture:")
        print("  • Reactive state management")
        print("  • Async data loading")
        print("  • Multi-layer caching")
        print("  • Performance monitoring")
        print("  • Modern MVVM architecture")
        print("  • Comprehensive testing")

        return True

    except Exception as e:
        print(f"✗ Integration failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def show_migration_guide():
    """Show step-by-step migration guide."""

    print("\n" + "=" * 60)
    print("MIGRATION GUIDE: Browse Tab v1 → v2")
    print("=" * 60)

    print(
        """
STEP 1: Update imports
OLD:
    from src.main_window.main_widget.browse_tab.browse_tab import BrowseTab

NEW:
    from browse_tab_v2.integration import create_browse_tab_v2_adapter

STEP 2: Update creation code
OLD:
    self.browse_tab = BrowseTab(
        json_manager=self.json_manager,
        settings_manager=self.settings_manager,
        parent=self
    )

NEW:
    self.browse_tab = create_browse_tab_v2_adapter(
        json_manager=self.json_manager,
        settings_manager=self.settings_manager,
        parent=self
    )

STEP 3: Signal connections remain the same
    self.browse_tab.sequence_selected.connect(self.on_sequence_selected)
    self.browse_tab.filter_changed.connect(self.on_filter_changed)
    self.browse_tab.loading_changed.connect(self.on_loading_changed)

STEP 4: Method calls remain the same
    self.browse_tab.load_sequences()
    self.browse_tab.search_sequences(query)
    self.browse_tab.apply_filter(filter_type, value)
    self.browse_tab.select_sequence(sequence_id)

STEP 5: Layout usage remains the same
    layout.addWidget(self.browse_tab)

That's it! The new browse tab v2 is a drop-in replacement.
"""
    )


if __name__ == "__main__":
    print("Browse Tab v2 Integration & Migration Guide")
    print("=" * 60)

    # Run integration example
    success = integrate_browse_tab_v2()

    if success:
        # Show migration guide
        show_migration_guide()

        print("\n" + "=" * 60)
        print("NEXT STEPS:")
        print("=" * 60)
        print("1. Run the standalone demo: python demo_browse_tab_v2.py")
        print("2. Test the integration in your application")
        print("3. Proceed to Phase 2 for modern UI components")
        print("4. Enjoy the improved performance and maintainability!")

    else:
        print("\n❌ Integration example failed. Please check the error messages above.")

    sys.exit(0 if success else 1)
