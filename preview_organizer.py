#!/usr/bin/env python3
"""
Preview script to show how files would be organized
"""
import os
from datetime import datetime
from collections import defaultdict
from pathlib import Path
import argparse

def preview_organization(source_dir, use_creation_date=False):
    """Preview how files would be organized"""
    source_path = Path(source_dir)
    
    if not source_path.exists():
        print(f"Error: Directory '{source_dir}' does not exist")
        return
    
    # Dictionary to store organization preview
    preview = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    
    # Scan files
    for file_path in source_path.rglob('*'):
        if file_path.is_file():
            # Get file date
            try:
                timestamp = os.path.getmtime(file_path)
                if use_creation_date and os.name == 'nt':
                    timestamp = os.path.getctime(file_path)
                
                dt = datetime.fromtimestamp(timestamp)
                year = dt.year
                month = dt.month
                month_name = dt.strftime('%B')
                
                # Get file type from extension
                ext = file_path.suffix.lower()
                file_type = 'other'
                if ext in ['.jpg', '.jpeg', '.png', '.gif']:
                    file_type = 'images'
                elif ext in ['.mp4', '.mov', '.avi']:
                    file_type = 'videos'
                elif ext in ['.pdf', '.doc', '.docx']:
                    file_type = 'documents'
                
                # Add to preview
                preview[file_type][year][f"{month:02d}-{month_name}"].append(file_path.name)
                
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
    
    # Display preview
    print("\n" + "="*60)
    print("ORGANIZATION PREVIEW")
    print("="*60)
    
    total_files = 0
    for file_type in sorted(preview.keys()):
        print(f"\n{file_type.upper()}:")
        print("-" * 40)
        type_count = 0
        
        for year in sorted(preview[file_type].keys()):
            print(f"  {year}:")
            for month in sorted(preview[file_type][year].keys()):
                files = preview[file_type][year][month]
                print(f"    {month}: {len(files)} files")
                type_count += len(files)
        
        print(f"  Total: {type_count} files")
        total_files += type_count
    
    print(f"\n{'='*60}")
    print(f"TOTAL FILES TO ORGANIZE: {total_files}")
    print("="*60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Preview file organization')
    parser.add_argument('source', help='Source directory to preview')
    parser.add_argument('--use-creation-date', action='store_true',
                       help='Use creation date instead of modification date')
    
    args = parser.parse_args()
    preview_organization(args.source, args.use_creation_date)