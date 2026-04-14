import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import shutil
import threading
import queue
from datetime import datetime
from pathlib import Path
import re
import sys

class SmartFileOrganizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart File Organizer - Multiple Date Sources")
        self.root.geometry("1000x750")
        self.root.minsize(900, 650)
        
        # Configure styles
        self.setup_styles()
        
        # Variables
        self.source_dir = tk.StringVar()
        self.date_priority = tk.StringVar(value="filename_first")  # filename_first, metadata_first, combined
        self.fallback_date = tk.StringVar(value="modified")  # modified, created
        self.organize_by = tk.StringVar(value="year_month")
        self.action_type = tk.StringVar(value="move")
        self.dry_run = tk.BooleanVar(value=True)
        self.recursive = tk.BooleanVar(value=False)
        
        # Filename date patterns
        self.date_patterns = {
            "YYYY-MM-DD": r'(\d{4})[-_\.](\d{2})[-_\.](\d{2})',
            "YYYY_MM_DD": r'(\d{4})[-_\.](\d{2})[-_\.](\d{2})',
            "DD-MM-YYYY": r'(\d{2})[-_\.](\d{2})[-_\.](\d{4})',
            "MM-DD-YYYY": r'(\d{2})[-_\.](\d{2})[-_\.](\d{4})',
            "YYYYMMDD": r'(\d{4})(\d{2})(\d{2})',
            "YYYY-MM": r'(\d{4})[-_\.](\d{2})',
            "YYYY_MM": r'(\d{4})[-_\.](\d{2})',
            "MM-YYYY": r'(\d{2})[-_\.](\d{4})',
            "Month YYYY": r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s,_-]+(\d{4})',
            "YYYY Month": r'(\d{4})[\s,_-]+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*'
        }
        
        # Active patterns
        self.active_patterns = {}
        for pattern in self.date_patterns.keys():
            self.active_patterns[pattern] = tk.BooleanVar(value=True)
        
        # File format variables
        self.file_formats = {
            'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.heic'],
            'Videos': ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm', '.m4v'],
            'Documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx'],
            'Audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'],
            'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2']
        }
        
        self.format_vars = {}
        for category in self.file_formats.keys():
            self.format_vars[category] = tk.BooleanVar(value=True)
        
        self.custom_extensions = tk.StringVar(value="")
        
        # Progress tracking
        self.total_files = 0
        self.processed_files = 0
        self.is_running = False
        
        # Statistics
        self.stats = {
            'by_filename': 0,
            'by_metadata': 0,
            'no_date': 0,
            'skipped': 0,
            'errors': 0,
            'folders_created': 0
        }
        
        # Threading queue
        self.log_queue = queue.Queue()
        
        # Setup GUI
        self.setup_gui()
        
        # Start log monitor
        self.monitor_log_queue()
        
    def setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        self.root.configure(bg='#f5f5f5')
        
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), foreground='#2c3e50')
        style.configure('Header.TLabel', font=('Arial', 11, 'bold'), foreground='#34495e')
        style.configure('Status.TLabel', font=('Arial', 10), foreground='#7f8c8d')
        
        style.configure('Accent.TButton', background='#3498db', foreground='white')
        style.map('Accent.TButton', background=[('active', '#2980b9')])
        
        style.configure('Green.TButton', background='#2ecc71', foreground='white')
        style.map('Green.TButton', background=[('active', '#27ae60')])
        
    def setup_gui(self):
        """Setup the main GUI layout"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Title
        title_label = ttk.Label(main_frame, 
                               text="🧠 Smart File Organizer - Multiple Date Sources",
                               style='Title.TLabel')
        title_label.pack(pady=(0, 15))
        
        # Create notebook
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Setup tabs
        self.setup_date_source_tab(notebook)
        self.setup_formats_tab(notebook)
        self.setup_preview_tab(notebook)
        self.setup_log_tab(notebook)
        
        # Progress section
        self.setup_progress_section(main_frame)
        
    def setup_date_source_tab(self, notebook):
        """Setup date source configuration tab"""
        date_tab = ttk.Frame(notebook)
        notebook.add(date_tab, text="📅 Date Sources")
        
        # Create scrollable frame
        canvas = tk.Canvas(date_tab)
        scrollbar = ttk.Scrollbar(date_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Folder selection
        folder_frame = ttk.LabelFrame(scrollable_frame, text="Folder Selection", padding=15)
        folder_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(folder_frame, text="Select folder to organize:").pack(anchor=tk.W, pady=(0, 5))
        
        entry_frame = ttk.Frame(folder_frame)
        entry_frame.pack(fill=tk.X, pady=5)
        
        ttk.Entry(entry_frame, textvariable=self.source_dir, width=50).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(entry_frame, text="Browse...", 
                  command=self.browse_folder).pack(side=tk.RIGHT)
        
        # Date priority settings
        priority_frame = ttk.LabelFrame(scrollable_frame, text="Date Source Priority", padding=15)
        priority_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(priority_frame, text="How to determine date for organizing files:",
                 font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        priority_options = [
            ("filename_first", "📝 Filename First - Use date from filename if available, otherwise use file date"),
            ("metadata_first", "💾 File Date First - Use file date, check filename as backup"),
            ("combined", "🔄 Combined - Use filename for year/month, file date for day if needed")
        ]
        
        for value, text in priority_options:
            frame = ttk.Frame(priority_frame)
            frame.pack(fill=tk.X, padx=20, pady=2)
            ttk.Radiobutton(frame, text=text, variable=self.date_priority, 
                          value=value).pack(anchor=tk.W)
        
        # Fallback date type
        fallback_frame = ttk.LabelFrame(scrollable_frame, text="Fallback Date Type", padding=15)
        fallback_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(fallback_frame, text="When using file dates, use:").pack(anchor=tk.W, pady=(0, 5))
        
        ttk.Radiobutton(fallback_frame, text="Modified Date", 
                       variable=self.fallback_date, value="modified").pack(anchor=tk.W, padx=20, pady=2)
        ttk.Radiobutton(fallback_frame, text="Creation Date", 
                       variable=self.fallback_date, value="created").pack(anchor=tk.W, padx=20, pady=2)
        
        # Filename date patterns
        pattern_frame = ttk.LabelFrame(scrollable_frame, text="Filename Date Patterns", padding=15)
        pattern_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(pattern_frame, text="Look for these date patterns in filenames:",
                 font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        # Pattern checkboxes in grid
        pattern_grid = ttk.Frame(pattern_frame)
        pattern_grid.pack(fill=tk.X, padx=10)
        
        patterns = list(self.active_patterns.keys())
        for i, pattern in enumerate(patterns):
            row = i // 3
            col = i % 3
            cb = ttk.Checkbutton(pattern_grid, text=pattern, 
                                variable=self.active_patterns[pattern])
            cb.grid(row=row, column=col, sticky=tk.W, padx=10, pady=2, ipadx=5)
        
        # Pattern examples
        example_frame = ttk.LabelFrame(scrollable_frame, text="Pattern Examples", padding=15)
        example_frame.pack(fill=tk.X, padx=10, pady=10)
        
        examples = [
            "photo_2023-07-15.jpg → Year: 2023, Month: 07",
            "report_15-07-2023.pdf → Year: 2023, Month: 07",
            "vacation_20230715.mp4 → Year: 2023, Month: 07",
            "invoice_07-2023.pdf → Year: 2023, Month: 07",
            "project_July_2023.docx → Year: 2023, Month: 07"
        ]
        
        for example in examples:
            ttk.Label(example_frame, text=f"• {example}", font=('Arial', 9)).pack(anchor=tk.W, pady=1)
        
        # Test button
        test_frame = ttk.Frame(scrollable_frame)
        test_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(test_frame, text="🔍 Test Date Detection", 
                  command=self.test_date_detection).pack()
        
    def setup_formats_tab(self, notebook):
        """Setup file formats tab"""
        formats_tab = ttk.Frame(notebook)
        notebook.add(formats_tab, text="📄 File Formats")
        
        # Create scrollable frame
        canvas = tk.Canvas(formats_tab)
        scrollbar = ttk.Scrollbar(formats_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Organization settings
        org_frame = ttk.LabelFrame(scrollable_frame, text="Organization Settings", padding=15)
        org_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Folder structure
        ttk.Label(org_frame, text="Create folders by:").pack(anchor=tk.W, pady=(0, 5))
        
        org_options = [
            ("year_month", "Year/Month (e.g., 2023/07-July)"),
            ("year_only", "Year only (e.g., 2023)"),
            ("month_only", "Month only (e.g., 07-July)")
        ]
        
        for value, text in org_options:
            ttk.Radiobutton(org_frame, text=text, variable=self.organize_by, 
                          value=value).pack(anchor=tk.W, padx=20, pady=2)
        
        # File action
        ttk.Label(org_frame, text="File action:").pack(anchor=tk.W, pady=(10, 5))
        
        action_options = [
            ("move", "Move files to organized folders"),
            ("copy", "Copy files (keep originals)")
        ]
        
        for value, text in action_options:
            ttk.Radiobutton(org_frame, text=text, variable=self.action_type, 
                          value=value).pack(anchor=tk.W, padx=20, pady=2)
        
        # Options
        ttk.Label(org_frame, text="Options:").pack(anchor=tk.W, pady=(10, 5))
        
        ttk.Checkbutton(org_frame, text="Process subfolders recursively", 
                       variable=self.recursive).pack(anchor=tk.W, padx=20, pady=2)
        ttk.Checkbutton(org_frame, text="Dry run (preview only, no changes)", 
                       variable=self.dry_run).pack(anchor=tk.W, padx=20, pady=2)
        
        # File formats selection
        formats_frame = ttk.LabelFrame(scrollable_frame, text="File Formats to Organize", padding=15)
        formats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(formats_frame, text="Select file formats:").pack(anchor=tk.W, pady=(0, 10))
        
        # Format checkboxes in grid
        format_grid = ttk.Frame(formats_frame)
        format_grid.pack(fill=tk.X, padx=10)
        
        categories = list(self.file_formats.keys())
        for i, category in enumerate(categories):
            row = i // 2
            col = i % 2
            frame = ttk.Frame(format_grid)
            frame.grid(row=row, column=col, sticky=tk.W, padx=10, pady=5)
            
            cb = ttk.Checkbutton(frame, text=category, variable=self.format_vars[category])
            cb.pack(side=tk.LEFT)
            
            ext_count = len(self.file_formats[category])
            ttk.Label(frame, text=f"({ext_count} formats)", foreground="#666666").pack(side=tk.LEFT, padx=(5, 0))
        
        # Custom extensions
        custom_frame = ttk.LabelFrame(scrollable_frame, text="Custom Extensions", padding=15)
        custom_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(custom_frame, text="Additional extensions (comma-separated):").pack(anchor=tk.W, pady=(0, 5))
        ttk.Entry(custom_frame, textvariable=self.custom_extensions, width=50).pack(fill=tk.X, pady=5)
        
    def setup_preview_tab(self, notebook):
        """Setup preview tab"""
        preview_tab = ttk.Frame(notebook)
        notebook.add(preview_tab, text="👁️ Preview")
        
        # Preview controls
        control_frame = ttk.Frame(preview_tab)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(control_frame, text="📊 Scan Folder", 
                  command=self.scan_folder, style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="🔄 Clear", 
                  command=self.clear_preview).pack(side=tk.LEFT, padx=5)
        
        # Preview treeview
        tree_container = ttk.Frame(preview_tab)
        tree_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Create treeview
        columns = ('filename', 'date_source', 'year', 'month', 'new_location', 'format')
        self.preview_tree = ttk.Treeview(tree_container, columns=columns, 
                                        show='headings', height=15)
        
        # Configure columns
        column_configs = [
            ('filename', 'Filename', 150),
            ('date_source', 'Date Source', 120),
            ('year', 'Year', 60),
            ('month', 'Month', 80),
            ('new_location', 'New Location', 200),
            ('format', 'Format', 80)
        ]
        
        for col_id, heading, width in column_configs:
            self.preview_tree.heading(col_id, text=heading)
            self.preview_tree.column(col_id, width=width, minwidth=50)
        
        # Add scrollbars
        vsb = ttk.Scrollbar(tree_container, orient="vertical", 
                           command=self.preview_tree.yview)
        hsb = ttk.Scrollbar(tree_container, orient="horizontal",
                           command=self.preview_tree.xview)
        self.preview_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        self.preview_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        
        # Summary frame
        summary_frame = ttk.Frame(preview_tab)
        summary_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.summary_label = ttk.Label(summary_frame, 
                                      text="Click 'Scan Folder' to preview organization")
        self.summary_label.pack(side=tk.LEFT)
        
        # Statistics label
        self.stats_label = ttk.Label(summary_frame, text="", font=('Arial', 9))
        self.stats_label.pack(side=tk.RIGHT)
        
    def setup_log_tab(self, notebook):
        """Setup log tab"""
        log_tab = ttk.Frame(notebook)
        notebook.add(log_tab, text="📋 Log")
        
        # Log text widget
        self.log_text = scrolledtext.ScrolledText(log_tab, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Log controls
        control_frame = ttk.Frame(log_tab)
        control_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(control_frame, text="🧹 Clear Log", 
                  command=self.clear_log).pack(side=tk.LEFT)
        ttk.Button(control_frame, text="💾 Save Log...", 
                  command=self.save_log).pack(side=tk.LEFT, padx=10)
        
    def setup_progress_section(self, parent):
        """Setup progress bar and control buttons"""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Start/Stop button
        self.start_button = ttk.Button(control_frame, text="🚀 Start Smart Organization", 
                                      command=self.toggle_organization,
                                      style='Accent.TButton')
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(control_frame, 
                                           variable=self.progress_var,
                                           length=300)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Status label
        self.status_label = ttk.Label(control_frame, text="✅ Ready", 
                                     style='Status.TLabel')
        self.status_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Progress percentage
        self.progress_percent = ttk.Label(control_frame, text="0%")
        self.progress_percent.pack(side=tk.LEFT, padx=(10, 0))
        
    def browse_folder(self):
        """Browse for folder"""
        directory = filedialog.askdirectory(title="Select Folder to Organize")
        if directory:
            self.source_dir.set(directory)
            self.log(f"Selected folder: {directory}")
    
    def extract_date_from_filename(self, filename):
        """Extract date from filename using active patterns"""
        stem = Path(filename).stem.lower()
        
        month_names = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        
        # Check each active pattern
        for pattern_name, var in self.active_patterns.items():
            if not var.get():
                continue
            
            pattern = self.date_patterns.get(pattern_name)
            if not pattern:
                continue
            
            match = re.search(pattern, stem, re.IGNORECASE)
            if match:
                try:
                    if pattern_name in ["YYYY-MM-DD", "YYYY_MM_DD", "YYYYMMDD"]:
                        year = int(match.group(1))
                        month = int(match.group(2))
                        return year, month, f"filename:{pattern_name}"
                    
                    elif pattern_name in ["DD-MM-YYYY", "MM-DD-YYYY"]:
                        year = int(match.group(3))
                        month = int(match.group(2) if pattern_name == "DD-MM-YYYY" else match.group(1))
                        return year, month, f"filename:{pattern_name}"
                    
                    elif pattern_name in ["YYYY-MM", "YYYY_MM"]:
                        year = int(match.group(1))
                        month = int(match.group(2))
                        return year, month, f"filename:{pattern_name}"
                    
                    elif pattern_name == "MM-YYYY":
                        year = int(match.group(2))
                        month = int(match.group(1))
                        return year, month, f"filename:{pattern_name}"
                    
                    elif pattern_name == "Month YYYY":
                        month_str = match.group(1).lower()[:3]
                        year = int(match.group(2))
                        month = month_names.get(month_str)
                        if month:
                            return year, month, f"filename:{pattern_name}"
                    
                    elif pattern_name == "YYYY Month":
                        year = int(match.group(1))
                        month_str = match.group(2).lower()[:3]
                        month = month_names.get(month_str)
                        if month:
                            return year, month, f"filename:{pattern_name}"
                            
                except (ValueError, IndexError):
                    continue
        
        return None, None, None
    
    def get_file_metadata_date(self, file_path):
        """Get date from file metadata"""
        try:
            if self.fallback_date.get() == "created":
                if os.name == 'nt':  # Windows
                    timestamp = os.path.getctime(file_path)
                else:  # Unix/Linux/Mac
                    try:
                        timestamp = file_path.stat().st_birthtime
                    except AttributeError:
                        timestamp = os.path.getmtime(file_path)
            else:  # modified
                timestamp = os.path.getmtime(file_path)
            
            dt = datetime.fromtimestamp(timestamp)
            return dt.year, dt.month, f"metadata:{self.fallback_date.get()}"
            
        except Exception:
            return None, None, None
    
    def get_date_for_file(self, file_path):
        """
        Get date for file based on priority settings
        Returns: (year, month, source_info)
        """
        # Extract from filename
        filename_year, filename_month, filename_source = self.extract_date_from_filename(file_path.name)
        
        # Get from metadata
        meta_year, meta_month, meta_source = self.get_file_metadata_date(file_path)
        
        # Apply priority logic
        priority = self.date_priority.get()
        
        if priority == "filename_first":
            if filename_year and filename_month:
                return filename_year, filename_month, filename_source
            elif meta_year and meta_month:
                return meta_year, meta_month, meta_source
            else:
                return None, None, None
                
        elif priority == "metadata_first":
            if meta_year and meta_month:
                return meta_year, meta_month, meta_source
            elif filename_year and filename_month:
                return filename_year, filename_month, filename_source
            else:
                return None, None, None
                
        elif priority == "combined":
            # Use filename for year/month if available
            if filename_year and filename_month:
                return filename_year, filename_month, filename_source
            elif meta_year and meta_month:
                return meta_year, meta_month, meta_source
            else:
                return None, None, None
        
        return None, None, None
    
    def test_date_detection(self):
        """Test date detection on sample filenames"""
        test_window = tk.Toplevel(self.root)
        test_window.title("Date Detection Test")
        test_window.geometry("600x500")
        
        test_frame = ttk.Frame(test_window, padding=15)
        test_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(test_frame, text="Test Date Detection on Sample Filenames:",
                 font=('Arial', 11, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        # Sample filenames
        samples = [
            "photo_2023-07-15_beach.jpg",
            "report_15-07-2023_final.pdf",
            "video_20230715_party.mp4",
            "invoice_07-2023.pdf",
            "vacation_July_2023.jpg",
            "file_without_date.txt"
        ]
        
        results_text = scrolledtext.ScrolledText(test_frame, height=15)
        results_text.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Test each sample
        for filename in samples:
            # Extract from filename
            year, month, source = self.extract_date_from_filename(filename)
            
            results_text.insert(tk.END, f"\n📝 {filename}\n")
            
            if year and month:
                month_name = datetime(2000, month, 1).strftime('%B')
                results_text.insert(tk.END, f"   Filename date: {year}-{month:02d} ({month_name})\n")
                results_text.insert(tk.END, f"   Source: {source}\n")
            else:
                results_text.insert(tk.END, f"   No date found in filename\n")
            
            # Simulate metadata dates
            results_text.insert(tk.END, f"   Simulated metadata: 2026-01 (current year)\n")
            
            # Show what would happen
            priority = self.date_priority.get()
            if year and month:
                results_text.insert(tk.END, f"   🎯 Using: {year}-{month:02d} (from filename)\n")
            else:
                results_text.insert(tk.END, f"   🎯 Using: 2026-01 (from metadata)\n")
            
            results_text.insert(tk.END, f"   Folder: 2026/01-January/\n")
            results_text.insert(tk.END, "-" * 50 + "\n")
    
    def get_selected_extensions(self):
        """Get list of selected file extensions"""
        extensions = []
        
        # Add extensions from selected categories
        for category, var in self.format_vars.items():
            if var.get():
                extensions.extend(self.file_formats[category])
        
        # Add custom extensions
        custom_exts = [ext.strip().lower() for ext in self.custom_extensions.get().split(',') if ext.strip()]
        extensions.extend(custom_exts)
        
        return list(set(extensions))
    
    def scan_folder(self):
        """Scan folder and show preview"""
        source = self.source_dir.get()
        if not source or not os.path.exists(source):
            messagebox.showerror("Error", "Please select a valid folder.")
            return
        
        try:
            # Clear existing preview
            self.clear_preview()
            
            # Reset stats
            self.stats = {k: 0 for k in self.stats}
            
            # Get selected extensions
            selected_extensions = self.get_selected_extensions()
            if not selected_extensions:
                messagebox.showwarning("Warning", "No file formats selected.")
                return
            
            # Scan files
            source_path = Path(source)
            if self.recursive.get():
                all_files = list(source_path.rglob('*'))
            else:
                all_files = list(source_path.glob('*'))
            
            files = [f for f in all_files if f.is_file()]
            total_files = len(files)
            
            # Process files for preview
            for file_path in files[:100]:  # Limit preview
                # Check file extension
                if file_path.suffix.lower() not in selected_extensions:
                    self.stats['skipped'] += 1
                    continue
                
                # Get date for file
                year, month, source_info = self.get_date_for_file(file_path)
                
                if year and month:
                    # Update stats
                    if 'filename' in source_info:
                        self.stats['by_filename'] += 1
                    else:
                        self.stats['by_metadata'] += 1
                    
                    # Determine new location
                    month_name = datetime(2000, month, 1).strftime('%B')
                    dest_path = file_path.parent
                    
                    organize_by = self.organize_by.get()
                    if organize_by == "year_month":
                        dest_path = dest_path / str(year) / f"{month:02d}-{month_name}"
                    elif organize_by == "year_only":
                        dest_path = dest_path / str(year)
                    elif organize_by == "month_only":
                        dest_path = dest_path / f"{month:02d}-{month_name}"
                    
                    # Format source for display
                    if 'filename' in source_info:
                        display_source = "Filename"
                    else:
                        display_source = "File Date"
                    
                    # Add to preview
                    self.preview_tree.insert('', 'end', values=(
                        file_path.name,
                        display_source,
                        str(year),
                        f"{month:02d}-{month_name}",
                        str(dest_path.relative_to(source_path) if dest_path.is_relative_to(source_path) else dest_path),
                        file_path.suffix
                    ))
                    
                else:
                    self.stats['no_date'] += 1
            
            # Update summary
            self.summary_label.config(
                text=f"📊 Preview: {self.stats['by_filename'] + self.stats['by_metadata']} files will be organized"
            )
            
            self.stats_label.config(
                text=f"Filename: {self.stats['by_filename']} | "
                     f"File Date: {self.stats['by_metadata']} | "
                     f"No Date: {self.stats['no_date']}"
            )
            
            self.log(f"Scan complete: {total_files} files found")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan folder: {str(e)}")
    
    def clear_preview(self):
        """Clear the preview tree"""
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        self.summary_label.config(text="Preview cleared")
        self.stats_label.config(text="")
    
    def toggle_organization(self):
        """Start or stop organization process"""
        if not self.is_running:
            self.start_organization()
        else:
            self.stop_organization()
    
    def start_organization(self):
        """Start the organization process"""
        source = self.source_dir.get()
        if not source or not os.path.exists(source):
            messagebox.showerror("Error", "Please select a valid folder.")
            return
        
        # Get selected extensions
        selected_extensions = self.get_selected_extensions()
        if not selected_extensions:
            messagebox.showwarning("Warning", "No file formats selected.")
            return
        
        # Confirm if moving files
        if not self.dry_run.get() and self.action_type.get() == "move":
            response = messagebox.askyesno(
                "Confirm Move",
                f"This will organize files based on:\n"
                f"• Priority: {self.date_priority.get()}\n"
                f"• File formats: {len(selected_extensions)} selected\n"
                f"• Action: Move (originals will be removed)\n\n"
                f"Are you sure?"
            )
            if not response:
                return
        
        # Reset stats
        self.stats = {k: 0 for k in self.stats}
        
        # Start organization thread
        self.is_running = True
        self.start_button.config(text="⏹️ Stop Organization")
        
        thread = threading.Thread(target=self.organize_files, 
                                 args=(source, selected_extensions), daemon=True)
        thread.start()
    
    def stop_organization(self):
        """Stop the organization process"""
        self.is_running = False
        self.start_button.config(text="🚀 Start Smart Organization")
        self.status_label.config(text="⏹️ Stopped")
    
    def organize_files(self, source, selected_extensions):
        """Organize files in a separate thread"""
        try:
            source_path = Path(source)
            
            # Get file list
            if self.recursive.get():
                all_files = list(source_path.rglob('*'))
            else:
                all_files = list(source_path.glob('*'))
            
            files = [f for f in all_files if f.is_file()]
            self.total_files = len(files)
            
            self.log(f"🚀 Starting smart organization of {self.total_files} files")
            self.log(f"📁 Source folder: {source_path}")
            self.log(f"🎯 Date priority: {self.date_priority.get()}")
            self.log(f"📝 File formats: {len(selected_extensions)} selected")
            self.log(f"⚡ Action: {self.action_type.get()}")
            self.log(f"👁️ Mode: {'Dry Run' if self.dry_run.get() else 'Live'}")
            self.log("-" * 50)
            
            self.status_label.config(text=f"🔄 Processing 0/{self.total_files} files...")
            
            # Process files
            for i, file_path in enumerate(files, 1):
                if not self.is_running:
                    self.log("⏹️ Organization stopped by user")
                    break
                
                # Update progress
                progress = (i / self.total_files) * 100
                self.progress_var.set(progress)
                self.progress_percent.config(text=f"{int(progress)}%")
                self.status_label.config(text=f"🔄 Processing {i}/{self.total_files} files...")
                
                # Process file
                self.process_file(file_path, selected_extensions, source_path, i)
                
                # Update UI periodically
                if i % 10 == 0:
                    self.root.update_idletasks()
            
            # Finalize
            if self.is_running:
                self.show_summary()
            
        except Exception as e:
            self.log(f"❌ Organization failed: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Organization failed: {str(e)}")
        finally:
            self.is_running = False
            self.start_button.config(text="🚀 Start Smart Organization")
    
    def process_file(self, file_path, selected_extensions, source_path, file_num):
        """Process a single file"""
        try:
            # Check file extension
            if file_path.suffix.lower() not in selected_extensions:
                self.stats['skipped'] += 1
                return
            
            # Get date for file
            year, month, source_info = self.get_date_for_file(file_path)
            
            if not year or not month:
                self.stats['no_date'] += 1
                return
            
            # Update stats
            if 'filename' in source_info:
                self.stats['by_filename'] += 1
            else:
                self.stats['by_metadata'] += 1
            
            # Create destination path
            month_name = datetime(2000, month, 1).strftime('%B')
            dest_path = file_path.parent
            
            organize_by = self.organize_by.get()
            if organize_by == "year_month":
                dest_path = dest_path / str(year) / f"{month:02d}-{month_name}"
            elif organize_by == "year_only":
                dest_path = dest_path / str(year)
            elif organize_by == "month_only":
                dest_path = dest_path / f"{month:02d}-{month_name}"
            
            # Skip if destination is same as source
            if dest_path == file_path.parent:
                self.stats['skipped'] += 1
                return
            
            # Create destination directory if needed
            if not self.dry_run.get():
                dest_path.mkdir(parents=True, exist_ok=True)
                if not dest_path.exists():
                    self.stats['folders_created'] += 1
            
            # Prepare destination file path
            dest_file = dest_path / file_path.name
            
            # Handle duplicates
            counter = 1
            while dest_file.exists() and not self.dry_run.get():
                stem = file_path.stem
                suffix = file_path.suffix
                dest_file = dest_path / f"{stem}_{counter}{suffix}"
                counter += 1
            
            # Determine source for log
            if 'filename' in source_info:
                date_source = "filename"
            else:
                date_source = "file date"
            
            # Perform action
            if self.dry_run.get():
                # Dry run - just log
                action = "Would organize"
                rel_path = dest_path.relative_to(source_path) if dest_path.is_relative_to(source_path) else dest_path
                self.log(f"👁️ #{file_num}: {action} {file_path.name} (source: {date_source}) → {rel_path}/")
                
            elif self.action_type.get() == "copy":
                # Copy file
                shutil.copy2(str(file_path), str(dest_file))
                action = "Copied"
                rel_path = dest_path.relative_to(source_path) if dest_path.is_relative_to(source_path) else dest_path
                self.log(f"📋 #{file_num}: {action} {file_path.name} (source: {date_source}) → {rel_path}/")
                
            else:
                # Move file
                shutil.move(str(file_path), str(dest_file))
                action = "Moved"
                rel_path = dest_path.relative_to(source_path) if dest_path.is_relative_to(source_path) else dest_path
                self.log(f"🚚 #{file_num}: {action} {file_path.name} (source: {date_source}) → {rel_path}/")
            
        except PermissionError as e:
            self.stats['errors'] += 1
            self.log(f"⚠️ #{file_num}: Permission error for {file_path.name}: {str(e)}", "WARNING")
        except Exception as e:
            self.stats['errors'] += 1
            self.log(f"❌ #{file_num}: Error processing {file_path.name}: {str(e)}", "ERROR")
    
    def show_summary(self):
        """Show organization summary"""
        self.status_label.config(text="✅ Organization complete!")
        
        summary = (
            f"\n🎉 SMART ORGANIZATION SUMMARY\n"
            f"{'='*50}\n"
            f"Total files scanned: {self.total_files}\n"
            f"Organized by filename date: {self.stats['by_filename']}\n"
            f"Organized by file date: {self.stats['by_metadata']}\n"
            f"No date found: {self.stats['no_date']}\n"
            f"Skipped: {self.stats['skipped']}\n"
            f"Folders created: {self.stats['folders_created']}\n"
            f"Errors: {self.stats['errors']}\n"
            f"{'='*50}\n"
        )
        
        self.log(summary)
        
        # Show message box
        if self.dry_run.get():
            messagebox.showinfo(
                "👁️ Dry Run Complete",
                f"Dry run completed!\n\n"
                f"• Files with dates in names: {self.stats['by_filename']}\n"
                f"• Files using file dates: {self.stats['by_metadata']}\n"
                f"• Files without dates: {self.stats['no_date']}\n"
                f"• Would create: {self.stats['folders_created']} folders"
            )
        else:
            action = "copied" if self.action_type.get() == "copy" else "moved"
            messagebox.showinfo(
                "✅ Organization Complete",
                f"Smart organization completed!\n\n"
                f"• Total files: {self.total_files}\n"
                f"• Files {action}: {self.stats['by_filename'] + self.stats['by_metadata']}\n"
                f"• Using filename dates: {self.stats['by_filename']}\n"
                f"• Using file dates: {self.stats['by_metadata']}\n"
                f"• Folders created: {self.stats['folders_created']}"
            )
    
    def log(self, message, level="INFO"):
        """Add message to log queue"""
        self.log_queue.put((level, message))
    
    def monitor_log_queue(self):
        """Monitor and process log messages"""
        try:
            while not self.log_queue.empty():
                level, message = self.log_queue.get_nowait()
                
                # Format message
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # Add to log text widget
                self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
                self.log_text.see(tk.END)
                
                # Color code
                if level == "ERROR":
                    self.log_text.tag_add("error", "end-2l", "end-1c")
                    self.log_text.tag_config("error", foreground="red")
                elif level == "WARNING":
                    self.log_text.tag_add("warning", "end-2l", "end-1c")
                    self.log_text.tag_config("warning", foreground="orange")
                    
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.monitor_log_queue)
    
    def clear_log(self):
        """Clear the log window"""
        self.log_text.delete(1.0, tk.END)
    
    def save_log(self):
        """Save log to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"smart_organizer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                self.log(f"💾 Log saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save log: {str(e)}")

def main():
    """Main function"""
    root = tk.Tk()
    app = SmartFileOrganizerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()