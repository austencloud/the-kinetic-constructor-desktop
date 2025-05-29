"""
Thumbnail Box Factory for Modern Integration.

This factory provides a clean interface for creating and migrating between
different thumbnail box implementations while maintaining backward compatibility.
"""

from typing import TYPE_CHECKING, Union
from .thumbnail_box import ThumbnailBox
from .modern_thumbnail_box_integrated import ModernThumbnailBoxIntegrated

if TYPE_CHECKING:
    from main_window.main_widget.browse_tab.browse_tab import BrowseTab


class ThumbnailBoxFactory:
    """
    Factory for creating and managing thumbnail box instances.
    
    Provides methods for:
    - Creating modern integrated thumbnail boxes
    - Migrating existing thumbnail boxes
    - Maintaining backward compatibility
    """
    
    @staticmethod
    def create_integrated_thumbnail_box(
        browse_tab: "BrowseTab", 
        word: str, 
        thumbnails: list[str], 
        in_sequence_viewer: bool = False
    ) -> ModernThumbnailBoxIntegrated:
        """
        Create modern integrated thumbnail box with glassmorphism styling.
        
        Args:
            browse_tab: Parent browse tab
            word: Word associated with thumbnails
            thumbnails: List of thumbnail paths
            in_sequence_viewer: Whether in sequence viewer mode
            
        Returns:
            Modern integrated thumbnail box instance
        """
        return ModernThumbnailBoxIntegrated(
            browse_tab=browse_tab,
            word=word,
            thumbnails=thumbnails,
            in_sequence_viewer=in_sequence_viewer
        )
    
    @staticmethod
    def create_legacy_thumbnail_box(
        browse_tab: "BrowseTab", 
        word: str, 
        thumbnails: list[str], 
        in_sequence_viewer: bool = False
    ) -> ThumbnailBox:
        """
        Create legacy thumbnail box for backward compatibility.
        
        Args:
            browse_tab: Parent browse tab
            word: Word associated with thumbnails
            thumbnails: List of thumbnail paths
            in_sequence_viewer: Whether in sequence viewer mode
            
        Returns:
            Legacy thumbnail box instance
        """
        return ThumbnailBox(
            browse_tab=browse_tab,
            word=word,
            thumbnails=thumbnails,
            in_sequence_viewer=in_sequence_viewer
        )
    
    @staticmethod
    def migrate_to_modern(
        existing_box: ThumbnailBox
    ) -> ModernThumbnailBoxIntegrated:
        """
        Migrate existing thumbnail box to modern version.
        
        Args:
            existing_box: Existing thumbnail box to migrate
            
        Returns:
            New modern thumbnail box with same state
        """
        return ModernThumbnailBoxIntegrated(
            browse_tab=existing_box.browse_tab,
            word=existing_box.word,
            thumbnails=existing_box.state.thumbnails,
            in_sequence_viewer=existing_box.in_sequence_viewer
        )
    
    @staticmethod
    def create_thumbnail_box(
        browse_tab: "BrowseTab", 
        word: str, 
        thumbnails: list[str], 
        in_sequence_viewer: bool = False,
        use_modern: bool = True
    ) -> Union[ThumbnailBox, ModernThumbnailBoxIntegrated]:
        """
        Create thumbnail box with option for modern or legacy version.
        
        Args:
            browse_tab: Parent browse tab
            word: Word associated with thumbnails
            thumbnails: List of thumbnail paths
            in_sequence_viewer: Whether in sequence viewer mode
            use_modern: Whether to use modern integrated version
            
        Returns:
            Thumbnail box instance (modern or legacy)
        """
        if use_modern:
            return ThumbnailBoxFactory.create_integrated_thumbnail_box(
                browse_tab, word, thumbnails, in_sequence_viewer
            )
        else:
            return ThumbnailBoxFactory.create_legacy_thumbnail_box(
                browse_tab, word, thumbnails, in_sequence_viewer
            )
    
    @staticmethod
    def get_thumbnail_box_type(thumbnail_box) -> str:
        """
        Get the type of thumbnail box.
        
        Args:
            thumbnail_box: Thumbnail box instance
            
        Returns:
            Type string ('modern' or 'legacy')
        """
        if isinstance(thumbnail_box, ModernThumbnailBoxIntegrated):
            return 'modern'
        elif isinstance(thumbnail_box, ThumbnailBox):
            return 'legacy'
        else:
            return 'unknown'
    
    @staticmethod
    def validate_thumbnail_box_compatibility(thumbnail_box) -> bool:
        """
        Validate that thumbnail box has required interface.
        
        Args:
            thumbnail_box: Thumbnail box to validate
            
        Returns:
            True if compatible, False otherwise
        """
        required_methods = [
            'get_current_index',
            'set_current_index', 
            'update_thumbnails',
            'show_nav_buttons',
            'hide_nav_buttons',
            'get_word',
            'get_thumbnails'
        ]
        
        for method in required_methods:
            if not hasattr(thumbnail_box, method):
                return False
                
        return True


class ThumbnailBoxMigrationHelper:
    """
    Helper class for migrating thumbnail boxes in bulk operations.
    """
    
    @staticmethod
    def migrate_all_in_scroll_widget(scroll_widget, use_modern: bool = True):
        """
        Migrate all thumbnail boxes in a scroll widget.
        
        Args:
            scroll_widget: Scroll widget containing thumbnail boxes
            use_modern: Whether to migrate to modern version
        """
        migrated_boxes = {}
        
        for word, thumbnail_box in scroll_widget.thumbnail_boxes.items():
            if use_modern and not isinstance(thumbnail_box, ModernThumbnailBoxIntegrated):
                # Migrate to modern version
                new_box = ThumbnailBoxFactory.migrate_to_modern(thumbnail_box)
                migrated_boxes[word] = new_box
            elif not use_modern and isinstance(thumbnail_box, ModernThumbnailBoxIntegrated):
                # Migrate to legacy version (if needed)
                new_box = ThumbnailBoxFactory.create_legacy_thumbnail_box(
                    thumbnail_box.browse_tab,
                    thumbnail_box.word,
                    thumbnail_box.state.thumbnails,
                    thumbnail_box.in_sequence_viewer
                )
                migrated_boxes[word] = new_box
        
        # Update scroll widget with migrated boxes
        scroll_widget.thumbnail_boxes.update(migrated_boxes)
        
        return len(migrated_boxes)
    
    @staticmethod
    def get_migration_statistics(scroll_widget) -> dict:
        """
        Get statistics about thumbnail box types in scroll widget.
        
        Args:
            scroll_widget: Scroll widget to analyze
            
        Returns:
            Dictionary with migration statistics
        """
        stats = {
            'total': len(scroll_widget.thumbnail_boxes),
            'modern': 0,
            'legacy': 0,
            'unknown': 0
        }
        
        for thumbnail_box in scroll_widget.thumbnail_boxes.values():
            box_type = ThumbnailBoxFactory.get_thumbnail_box_type(thumbnail_box)
            if box_type in stats:
                stats[box_type] += 1
        
        stats['migration_needed'] = stats['legacy']
        stats['modern_percentage'] = (stats['modern'] / stats['total'] * 100) if stats['total'] > 0 else 0
        
        return stats
