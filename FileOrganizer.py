import os
import shutil
import argparse
from datetime import datetime
from pathlib import Path
import logging
from typing import List, Tuple, Optional
import sys

class FileOrganizer:
    def __init__(self, source_dir: str, dest_dir: Optional[str] = None, 
                 use_creation_date: bool = False, dry_run: bool = False):
        """
        Initialize the file organizer
        
        Args:
            source_dir: Directory containing files to organize
            dest_dir: Directory where organized files will be placed (optional)
            use_creation_date: If True, use file creation date, otherwise use modification date
            dry_run: If True, only show what would be done without actually moving files
        """
        self.source_dir = Path(source_dir).resolve()
        self.dest_dir = Path(dest_dir).resolve() if dest_dir else self.source_dir
        self.use_creation_date = use_creation_date
        self.dry_run = dry_run
        
        # Setup logging
        self.setup_logging()
        
        # Supported file extensions (customizable)
        self.supported_extensions = {
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'],
            'videos': ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm'],
            'documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx'],
            'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'],
            'archives': ['.zip', '.rar', '.7z', '.tar', '.gz']
        }
    
    def setup_logging(self):
        """Configure logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('file_organizer.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_file_date(self, file_path: Path) -> Tuple[int, int, str]:
        """
        Get year, month, and month name from file date
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (year, month, month_name)
        """
        try:
            if self.use_creation_date:
                # Try to get creation time (platform dependent)
                if os.name == 'nt':  # Windows
                    timestamp = os.path.getctime(file_path)
                else:  # Unix/Mac - creation time not reliably available
                    timestamp = os.path.getmtime(file_path)
            else:
                # Use modification time (default)
                timestamp = os.path.getmtime(file_path)
            
            dt = datetime.fromtimestamp(timestamp)
            return dt.year, dt.month, dt.strftime('%B')
            
        except Exception as e:
            self.logger.error(f"Error getting date for {file_path}: {e}")
            # Return current date as fallback
            dt = datetime.now()
            return dt.year, dt.month, dt.strftime('%B')
    
    def get_file_type(self, file_path: Path) -> str:
        """
        Categorize file based on extension
        
        Args:
            file_path: Path to the file
            
        Returns:
            File type category
        """
        suffix = file_path.suffix.lower()
        
        for category, extensions in self.supported_extensions.items():
            if suffix in extensions:
                return category
        
        return 'other'
    
    def organize_file(self, file_path: Path) -> Optional[Path]:
        """
        Organize a single file by date
        
        Args:
            file_path: Path to the file to organize
            
        Returns:
            New path if moved, None otherwise
        """
        if not file_path.is_file():
            return None
        
        try:
            # Get file date information
            year, month, month_name = self.get_file_date(file_path)
            
            # Get file type
            file_type = self.get_file_type(file_path)
            
            # Create destination directory structure
            dest_path = self.dest_dir / file_type / str(year) / f"{month:02d}-{month_name}"
            
            if not self.dry_run:
                dest_path.mkdir(parents=True, exist_ok=True)
            
            # Create new filename (prevent overwrites)
            counter = 1
            new_file_path = dest_path / file_path.name
            while new_file_path.exists() and not self.dry_run:
                stem = file_path.stem
                suffix = file_path.suffix
                new_file_path = dest_path / f"{stem}_{counter}{suffix}"
                counter += 1
            
            # Move or copy the file
            if not self.dry_run:
                try:
                    shutil.move(str(file_path), str(new_file_path))
                    action = "Moved"
                except PermissionError:
                    shutil.copy2(str(file_path), str(new_file_path))
                    action = "Copied"
            else:
                action = "Would move"
            
            self.logger.info(f"{action}: {file_path} -> {new_file_path}")
            return new_file_path
            
        except Exception as e:
            self.logger.error(f"Error organizing {file_path}: {e}")
            return None
    
    def organize_directory(self, recursive: bool = False):
        """
        Organize all files in the source directory
        
        Args:
            recursive: If True, process subdirectories recursively
        """
        self.logger.info(f"Starting organization of: {self.source_dir}")
        self.logger.info(f"Destination: {self.dest_dir}")
        self.logger.info(f"Dry run: {self.dry_run}")
        self.logger.info(f"Using {'creation' if self.use_creation_date else 'modification'} date")
        
        try:
            if recursive:
                # Process all files recursively
                files = list(self.source_dir.rglob('*'))
            else:
                # Process only files in the source directory
                files = list(self.source_dir.glob('*'))
            
            # Filter out directories
            files = [f for f in files if f.is_file()]
            
            self.logger.info(f"Found {len(files)} files to organize")
            
            # Organize each file
            organized_count = 0
            for file_path in files:
                result = self.organize_file(file_path)
                if result:
                    organized_count += 1
            
            self.logger.info(f"Successfully organized {organized_count}/{len(files)} files")
            
            # Summary report
            self.generate_summary()
            
        except Exception as e:
            self.logger.error(f"Error organizing directory: {e}")
    
    def generate_summary(self):
        """Generate a summary of organization results"""
        if self.dry_run or not self.dest_dir.exists():
            return
        
        summary = []
        for file_type in self.supported_extensions.keys():
            type_dir = self.dest_dir / file_type
            if type_dir.exists():
                for year_dir in sorted(type_dir.iterdir()):
                    if year_dir.is_dir():
                        for month_dir in sorted(year_dir.iterdir()):
                            if month_dir.is_dir():
                                file_count = len(list(month_dir.glob('*')))
                                if file_count > 0:
                                    summary.append(
                                        f"{file_type.capitalize()}/{year_dir.name}/{month_dir.name}: {file_count} files"
                                    )
        
        if summary:
            self.logger.info("\n" + "="*50)
            self.logger.info("ORGANIZATION SUMMARY:")
            self.logger.info("="*50)
            for line in summary:
                self.logger.info(line)


def main():
    """Main function with command-line interface"""
    parser = argparse.ArgumentParser(
        description='Organize files by year and month of creation/modification',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/source
  %(prog)s /path/to/source /path/to/destination --use-creation-date
  %(prog)s /path/to/source --recursive --dry-run
  %(prog)s /path/to/source --file-type images --year 2023
        """
    )
    
    parser.add_argument('source', help='Source directory containing files to organize')
    parser.add_argument('destination', nargs='?', help='Destination directory (optional)')
    parser.add_argument('--use-creation-date', action='store_true',
                       help='Use file creation date instead of modification date')
    parser.add_argument('--recursive', '-r', action='store_true',
                       help='Process subdirectories recursively')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without actually moving files')
    parser.add_argument('--file-type', choices=['images', 'videos', 'documents', 'audio', 'archives', 'all'],
                       default='all', help='Organize specific file types only')
    parser.add_argument('--year', type=int, help='Organize files from specific year only')
    
    args = parser.parse_args()
    
    # Validate source directory
    if not os.path.exists(args.source):
        print(f"Error: Source directory '{args.source}' does not exist")
        sys.exit(1)
    
    # Create organizer instance
    organizer = FileOrganizer(
        source_dir=args.source,
        dest_dir=args.destination,
        use_creation_date=args.use_creation_date,
        dry_run=args.dry_run
    )
    
    # Filter by file type if specified
    if args.file_type != 'all':
        organizer.supported_extensions = {
            args.file_type: organizer.supported_extensions[args.file_type]
        }
    
    # Start organization
    organizer.organize_directory(recursive=args.recursive)


if __name__ == "__main__":
    main()