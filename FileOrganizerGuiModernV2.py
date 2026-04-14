import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import shutil
import threading
import queue
from datetime import datetime
from pathlib import Path
import sys

class FileOrganizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("File Organizer - Sort by Date")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Configure styles
        self.setup_styles()
        
        # Variables
        self.source_dir = tk.StringVar()
        self.date_type = tk.StringVar(value="modified")  # "modified" or "creation"
        self.organize_by = tk.StringVar(value="year_month")  # "year_month", "year_only", "month_only"
        self.action_type = tk.StringVar(value="move")  # "move" or "copy"
        self.dry_run = tk.BooleanVar(value=False)
        self.recursive = tk.BooleanVar(value=False)
        
        # File format variables (with common extensions)
        self.file_formats = {
            'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'],
            'Videos': ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm'],
            'Documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx'],
            'Audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'],
            'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz'],
            'Code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.php']
        }
        
        # File format checkboxes
        self.format_vars = {}
        for category in self.file_formats.keys():
            self.format_vars[category] = tk.BooleanVar(value=True)
        
        # Custom extensions
        self.custom_extensions = tk.StringVar(value="")
        
        # Progress tracking
        self.total_files = 0
        self.processed_files = 0
        self.is_running = False
        
        # Statistics
        self.stats = {
            'organized': 0,
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
        
        # Configure colors
        self.root.configure(bg='#f5f5f5')
        
        # Configure styles
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), foreground='#2c3e50')
        style.configure('Header.TLabel', font=('Arial', 11, 'bold'), foreground='#34495e')
        style.configure('Status.TLabel', font=('Arial', 10), foreground='#7f8c8d')
        
        style.configure('Accent.TButton', background='#3498db', foreground='white')
        style.map('Accent.TButton', background=[('active', '#2980b9')])
        
        style.configure('Green.TButton', background='#2ecc71', foreground='white')
        style.map('Green.TButton', background=[('active', '#27ae60')])
        
        style.configure('TFrame', background='#f5f5f5')
        style.configure('TLabelframe', background='#ffffff', relief='solid', borderwidth=1)
        style.configure('TLabelframe.Label', background='#ffffff', font=('Arial', 10, 'bold'))
        
    def setup_gui(self):
        """Setup the main GUI layout"""
        # Create main container with notebook
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = ttk.Label(title_frame, 
                               text="📂 File Organizer - Sort by Date",
                               style='Title.TLabel')
        title_label.pack()
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.setup_main_tab(notebook)
        self.setup_formats_tab(notebook)
        self.setup_preview_tab(notebook)
        self.setup_log_tab(notebook)
        
        # Progress section at bottom
        self.setup_progress_section(main_frame)
        
    def setup_main_tab(self, notebook):
        """Setup main configuration tab"""
        main_tab = ttk.Frame(notebook)
        notebook.add(main_tab, text="⚙️ Settings")
        
        # Create scrollable frame
        canvas = tk.Canvas(main_tab)
        scrollbar = ttk.Scrollbar(main_tab, orient="vertical", command=canvas.yview)
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
        
        # Date type selection
        date_frame = ttk.LabelFrame(scrollable_frame, text="Date Type", padding=15)
        date_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(date_frame, text="Sort files by:").pack(anchor=tk.W, pady=(0, 5))
        
        date_radio_frame = ttk.Frame(date_frame)
        date_radio_frame.pack(fill=tk.X, padx=20)
        
        ttk.Radiobutton(date_radio_frame, text="Modified Date", 
                       variable=self.date_type, value="modified").pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(date_radio_frame, text="Creation Date", 
                       variable=self.date_type, value="creation").pack(anchor=tk.W, pady=2)
        
        # Organization type
        org_frame = ttk.LabelFrame(scrollable_frame, text="Organization Structure", padding=15)
        org_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(org_frame, text="Create folders by:").pack(anchor=tk.W, pady=(0, 5))
        
        org_radio_frame = ttk.Frame(org_frame)
        org_radio_frame.pack(fill=tk.X, padx=20)
        
        ttk.Radiobutton(org_radio_frame, text="Year/Month (e.g., 2023/07-July)", 
                       variable=self.organize_by, value="year_month").pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(org_radio_frame, text="Year only (e.g., 2023)", 
                       variable=self.organize_by, value="year_only").pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(org_radio_frame, text="Month only (e.g., 07-July)", 
                       variable=self.organize_by, value="month_only").pack(anchor=tk.W, pady=2)
        
        # File action
        action_frame = ttk.LabelFrame(scrollable_frame, text="File Action", padding=15)
        action_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(action_frame, text="What to do with files:").pack(anchor=tk.W, pady=(0, 5))
        
        action_radio_frame = ttk.Frame(action_frame)
        action_radio_frame.pack(fill=tk.X, padx=20)
        
        ttk.Radiobutton(action_radio_frame, text="Move files to organized folders", 
                       variable=self.action_type, value="move").pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(action_radio_frame, text="Copy files (keep originals)", 
                       variable=self.action_type, value="copy").pack(anchor=tk.W, pady=2)
        
        # Options
        options_frame = ttk.LabelFrame(scrollable_frame, text="Options", padding=15)
        options_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Checkbutton(options_frame, text="Process subfolders recursively", 
                       variable=self.recursive).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(options_frame, text="Dry run (preview only, no changes)", 
                       variable=self.dry_run).pack(anchor=tk.W, pady=2)
        
        # Year filtering
        year_frame = ttk.LabelFrame(scrollable_frame, text="Year Filtering (Optional)", padding=15)
        year_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.year_filter_var = tk.StringVar(value="all")
        ttk.Radiobutton(year_frame, text="All years", 
                       variable=self.year_filter_var, value="all").pack(anchor=tk.W, pady=2)
        
        specific_frame = ttk.Frame(year_frame)
        specific_frame.pack(fill=tk.X, padx=20, pady=2)
        ttk.Radiobutton(specific_frame, text="Specific year:", 
                       variable=self.year_filter_var, value="specific").pack(side=tk.LEFT)
        self.specific_year_var = tk.StringVar()
        ttk.Entry(specific_frame, textvariable=self.specific_year_var, width=10).pack(side=tk.LEFT, padx=5)
        
        range_frame = ttk.Frame(year_frame)
        range_frame.pack(fill=tk.X, padx=20, pady=2)
        ttk.Radiobutton(range_frame, text="Range:", 
                       variable=self.year_filter_var, value="range").pack(side=tk.LEFT)
        self.year_from_var = tk.StringVar()
        self.year_to_var = tk.StringVar()
        ttk.Entry(range_frame, textvariable=self.year_from_var, width=6).pack(side=tk.LEFT, padx=5)
        ttk.Label(range_frame, text="to").pack(side=tk.LEFT)
        ttk.Entry(range_frame, textvariable=self.year_to_var, width=6).pack(side=tk.LEFT, padx=5)
        
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
        
        # Format categories
        formats_frame = ttk.LabelFrame(scrollable_frame, text="Select File Formats to Organize", padding=15)
        formats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(formats_frame, text="Check the file formats you want to organize:").pack(anchor=tk.W, pady=(0, 10))
        
        # Create checkboxes in a grid
        categories = list(self.file_formats.keys())
        grid_frame = ttk.Frame(formats_frame)
        grid_frame.pack(fill=tk.X, padx=10)
        
        for i, category in enumerate(categories):
            row = i // 2
            col = i % 2
            
            frame = ttk.Frame(grid_frame)
            frame.grid(row=row, column=col, sticky=tk.W, padx=10, pady=5, ipadx=5)
            
            cb = ttk.Checkbutton(frame, text=category, variable=self.format_vars[category])
            cb.pack(side=tk.LEFT)
            
            # Show extensions count
            ext_count = len(self.file_formats[category])
            ttk.Label(frame, text=f"({ext_count} formats)", foreground="#666666").pack(side=tk.LEFT, padx=(5, 0))
        
        # Format details
        details_frame = ttk.LabelFrame(scrollable_frame, text="Format Details", padding=15)
        details_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Text widget to show extensions
        self.extensions_text = scrolledtext.ScrolledText(details_frame, height=8, wrap=tk.WORD)
        self.extensions_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Update button
        ttk.Button(details_frame, text="Update Extensions View", 
                  command=self.update_extensions_view).pack(pady=(10, 0))
        
        # Custom extensions
        custom_frame = ttk.LabelFrame(scrollable_frame, text="Custom Extensions", padding=15)
        custom_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(custom_frame, text="Add custom extensions (comma-separated, e.g., .md, .json, .xml):").pack(anchor=tk.W, pady=(0, 5))
        
        ttk.Entry(custom_frame, textvariable=self.custom_extensions, width=50).pack(fill=tk.X, pady=5)
        ttk.Label(custom_frame, text="Note: Custom extensions will be organized regardless of selected categories above.", 
                 foreground="#666666", font=('Arial', 9)).pack(anchor=tk.W, pady=(5, 0))
        
        # Initialize extensions view
        self.update_extensions_view()
        
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
        
        # Create treeview with columns
        columns = ('filename', 'date', 'new_location', 'format', 'action')
        self.preview_tree = ttk.Treeview(tree_container, columns=columns, 
                                        show='headings', height=15)
        
        # Configure columns
        column_configs = [
            ('filename', 'Filename', 150),
            ('date', 'Date', 100),
            ('new_location', 'New Location', 200),
            ('format', 'Format', 80),
            ('action', 'Action', 100)
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
        self.start_button = ttk.Button(control_frame, text="🚀 Start Organization", 
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
    
    def update_extensions_view(self):
        """Update the extensions display text"""
        self.extensions_text.delete(1.0, tk.END)
        
        # Get selected categories
        selected_categories = [cat for cat, var in self.format_vars.items() if var.get()]
        
        if not selected_categories:
            self.extensions_text.insert(tk.END, "No file formats selected. All files will be skipped.")
            return
        
        # Get custom extensions
        custom_exts = [ext.strip().lower() for ext in self.custom_extensions.get().split(',') if ext.strip()]
        
        # Display extensions
        all_extensions = []
        
        for category in selected_categories:
            extensions = self.file_formats[category]
            self.extensions_text.insert(tk.END, f"\n{category}:\n")
            self.extensions_text.insert(tk.END, "  " + ", ".join(extensions) + "\n")
            all_extensions.extend(extensions)
        
        if custom_exts:
            self.extensions_text.insert(tk.END, f"\nCustom Extensions:\n")
            self.extensions_text.insert(tk.END, "  " + ", ".join(custom_exts) + "\n")
            all_extensions.extend(custom_exts)
        
        # Summary
        self.extensions_text.insert(tk.END, f"\n{'='*40}\n")
        self.extensions_text.insert(tk.END, f"Total extensions to organize: {len(all_extensions)}\n")
        self.extensions_text.insert(tk.END, f"Categories selected: {len(selected_categories)}\n")
        
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
        
        return list(set(extensions))  # Remove duplicates
    
    def get_file_date(self, file_path):
        """Get date from file based on selected date type"""
        try:
            if self.date_type.get() == "creation":
                # Try to get creation date
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
            return dt.year, dt.month, dt.day
            
        except Exception as e:
            self.log(f"Error getting date for {file_path}: {str(e)}", "WARNING")
            return None, None, None
    
    def pass_year_filter(self, year):
        """Check if year passes the filter"""
        filter_type = self.year_filter_var.get()
        
        if filter_type == "all":
            return True
        elif filter_type == "specific":
            specific_year = self.specific_year_var.get()
            if specific_year and specific_year.isdigit():
                return year == int(specific_year)
            return True
        elif filter_type == "range":
            year_from = self.year_from_var.get()
            year_to = self.year_to_var.get()
            if year_from and year_from.isdigit() and year_to and year_to.isdigit():
                return int(year_from) <= year <= int(year_to)
            return True
        
        return True
    
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
            self.stats = {'organized': 0, 'skipped': 0, 'errors': 0, 'folders_created': 0}
            
            # Get selected extensions
            selected_extensions = self.get_selected_extensions()
            if not selected_extensions:
                messagebox.showwarning("Warning", "No file formats selected. Please select at least one file format.")
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
            for file_path in files[:100]:  # Limit preview to 100 files for performance
                # Check file extension
                if file_path.suffix.lower() not in selected_extensions:
                    self.stats['skipped'] += 1
                    continue
                
                # Get file date
                year, month, day = self.get_file_date(file_path)
                
                if year and month:
                    # Check year filter
                    if not self.pass_year_filter(year):
                        self.stats['skipped'] += 1
                        continue
                    
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
                    
                    # Determine action
                    if self.dry_run.get():
                        action = "Preview"
                    elif self.action_type.get() == "copy":
                        action = "Copy"
                    else:
                        action = "Move"
                    
                    # Add to preview
                    date_str = f"{year}-{month:02d}-{day:02d}" if day else f"{year}-{month:02d}"
                    self.preview_tree.insert('', 'end', values=(
                        file_path.name,
                        date_str,
                        str(dest_path.relative_to(source_path) if dest_path.is_relative_to(source_path) else dest_path),
                        file_path.suffix,
                        action
                    ))
                    
                    self.stats['organized'] += 1
                else:
                    self.stats['skipped'] += 1
            
            # Update summary
            self.summary_label.config(
                text=f"📊 Preview: {self.stats['organized']} files will be organized | "
                     f"Total files in folder: {total_files}"
            )
            
            self.log(f"Scan complete: {self.stats['organized']} files to organize out of {total_files}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan folder: {str(e)}")
    
    def clear_preview(self):
        """Clear the preview tree"""
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        self.summary_label.config(text="Preview cleared")
    
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
            messagebox.showwarning("Warning", "No file formats selected. Please select at least one file format.")
            return
        
        # Confirm if not dry run and moving files
        if not self.dry_run.get() and self.action_type.get() == "move":
            response = messagebox.askyesno(
                "Confirm Move",
                f"This will MOVE {len(selected_extensions)} file types to organized folders.\n"
                f"Original files will be removed from their current locations.\n\n"
                f"Are you sure you want to proceed?\n"
                f"Consider using 'Copy' mode or 'Dry run' first."
            )
            if not response:
                return
        
        # Reset stats
        self.stats = {'organized': 0, 'skipped': 0, 'errors': 0, 'folders_created': 0}
        
        # Start organization thread
        self.is_running = True
        self.start_button.config(text="⏹️ Stop Organization")
        
        thread = threading.Thread(target=self.organize_files, args=(source, selected_extensions), daemon=True)
        thread.start()
    
    def stop_organization(self):
        """Stop the organization process"""
        self.is_running = False
        self.start_button.config(text="🚀 Start Organization")
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
            
            self.log(f"🚀 Starting organization of {self.total_files} files")
            self.log(f"📁 Source folder: {source_path}")
            self.log(f"📅 Date type: {self.date_type.get()}")
            self.log(f"📋 File formats: {len(selected_extensions)} selected")
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
            self.start_button.config(text="🚀 Start Organization")
    
    def process_file(self, file_path, selected_extensions, source_path, file_num):
        """Process a single file"""
        try:
            # Check file extension
            if file_path.suffix.lower() not in selected_extensions:
                self.stats['skipped'] += 1
                return
            
            # Get file date
            year, month, day = self.get_file_date(file_path)
            
            if not year or not month:
                self.stats['skipped'] += 1
                return
            
            # Check year filter
            if not self.pass_year_filter(year):
                self.stats['skipped'] += 1
                return
            
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
            
            # Perform action
            if self.dry_run.get():
                # Dry run - just log
                action = "Would organize"
                rel_path = dest_path.relative_to(source_path) if dest_path.is_relative_to(source_path) else dest_path
                self.log(f"👁️ #{file_num}: {action} {file_path.name} → {rel_path}/")
                self.stats['organized'] += 1
                
            elif self.action_type.get() == "copy":
                # Copy file
                shutil.copy2(str(file_path), str(dest_file))
                action = "Copied"
                rel_path = dest_path.relative_to(source_path) if dest_path.is_relative_to(source_path) else dest_path
                self.log(f"📋 #{file_num}: {action} {file_path.name} → {rel_path}/")
                self.stats['organized'] += 1
                
            else:
                # Move file
                shutil.move(str(file_path), str(dest_file))
                action = "Moved"
                rel_path = dest_path.relative_to(source_path) if dest_path.is_relative_to(source_path) else dest_path
                self.log(f"🚚 #{file_num}: {action} {file_path.name} → {rel_path}/")
                self.stats['organized'] += 1
            
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
            f"\n🎉 ORGANIZATION SUMMARY\n"
            f"{'='*40}\n"
            f"Total files scanned: {self.total_files}\n"
            f"Successfully organized: {self.stats['organized']}\n"
            f"Folders created: {self.stats['folders_created']}\n"
            f"Skipped: {self.stats['skipped']}\n"
            f"Errors: {self.stats['errors']}\n"
            f"{'='*40}\n"
        )
        
        self.log(summary)
        
        # Show message box
        if self.dry_run.get():
            messagebox.showinfo(
                "👁️ Dry Run Complete",
                f"Dry run completed!\n\n"
                f"• Total files: {self.total_files}\n"
                f"• Would organize: {self.stats['organized']}\n"
                f"• Would create: {self.stats['folders_created']} folders\n"
                f"• Would skip: {self.stats['skipped']}\n"
                f"• Errors: {self.stats['errors']}"
            )
        else:
            action = "copied" if self.action_type.get() == "copy" else "moved"
            messagebox.showinfo(
                "✅ Organization Complete",
                f"Organization completed successfully!\n\n"
                f"• Total files processed: {self.total_files}\n"
                f"• Files {action}: {self.stats['organized']}\n"
                f"• Folders created: {self.stats['folders_created']}\n"
                f"• Files skipped: {self.stats['skipped']}\n"
                f"• Errors: {self.stats['errors']}"
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
            initialfile=f"file_organizer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
    app = FileOrganizerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()