import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import shutil
import threading
import queue
from datetime import datetime
from pathlib import Path
import logging
from typing import Optional
import sys

class FileOrganizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("File Organizer by Date")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Configure styles
        self.setup_styles()
        
        # Variables
        self.source_dir = tk.StringVar()
        self.dest_dir = tk.StringVar()
        self.use_creation_date = tk.BooleanVar(value=False)
        self.recursive = tk.BooleanVar(value=True)
        self.organize_by_type = tk.BooleanVar(value=True)
        self.dry_run = tk.BooleanVar(value=False)
        
        # File type variables
        self.file_types_vars = {
            'images': tk.BooleanVar(value=True),
            'videos': tk.BooleanVar(value=True),
            'documents': tk.BooleanVar(value=True),
            'audio': tk.BooleanVar(value=True),
            'archives': tk.BooleanVar(value=True),
            'other': tk.BooleanVar(value=True)
        }
        
        # Supported file extensions
        self.supported_extensions = {
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.heic', '.raw'],
            'videos': ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp'],
            'documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx'],
            'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'],
            'archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2']
        }
        
        # Progress tracking
        self.total_files = 0
        self.processed_files = 0
        self.is_running = False
        
        # Threading queue for logging
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
        self.root.configure(bg='#f0f0f0')
        
        # Configure styles
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Section.TLabel', font=('Arial', 11, 'bold'))
        style.configure('Status.TLabel', font=('Arial', 10))
        
    def setup_gui(self):
        """Setup the main GUI layout"""
        # Create main container with scrollbar
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="📁 File Organizer by Date", 
                               style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Setup tabs
        self.setup_settings_tab(notebook)
        self.setup_file_types_tab(notebook)
        self.setup_preview_tab(notebook)
        self.setup_log_tab(notebook)
        
        # Progress section
        self.setup_progress_section(main_frame)
        
    def setup_settings_tab(self, notebook):
        """Setup settings tab"""
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="Settings")
        
        # Source directory
        source_frame = ttk.LabelFrame(settings_frame, text="Source Directory", padding=10)
        source_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Entry(source_frame, textvariable=self.source_dir, width=50).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(source_frame, text="Browse...", 
                  command=self.browse_source).pack(side=tk.RIGHT)
        
        # Destination directory
        dest_frame = ttk.LabelFrame(settings_frame, text="Destination Directory (Optional)", 
                                   padding=10)
        dest_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Entry(dest_frame, textvariable=self.dest_dir, width=50).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(dest_frame, text="Browse...", 
                  command=self.browse_destination).pack(side=tk.RIGHT)
        
        # Options
        options_frame = ttk.LabelFrame(settings_frame, text="Options", padding=10)
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Checkbutton(options_frame, text="Use file creation date", 
                       variable=self.use_creation_date).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Process subdirectories recursively", 
                       variable=self.recursive).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Organize by file type", 
                       variable=self.organize_by_type).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Dry run (preview only)", 
                       variable=self.dry_run).pack(anchor=tk.W)
        
        # Year filter
        year_frame = ttk.Frame(options_frame)
        year_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(year_frame, text="Filter by year (optional):").pack(side=tk.LEFT)
        self.year_var = tk.StringVar()
        ttk.Entry(year_frame, textvariable=self.year_var, width=10).pack(
            side=tk.LEFT, padx=(5, 0))
        
    def setup_file_types_tab(self, notebook):
        """Setup file types selection tab"""
        filetypes_frame = ttk.Frame(notebook)
        notebook.add(filetypes_frame, text="File Types")
        
        # File types selection
        types_frame = ttk.LabelFrame(filetypes_frame, text="Select File Types to Organize", 
                                    padding=10)
        types_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create checkboxes for each file type
        row = 0
        col = 0
        for file_type, var in self.file_types_vars.items():
            cb = ttk.Checkbutton(types_frame, text=file_type.capitalize(), 
                                variable=var)
            cb.grid(row=row, column=col, sticky=tk.W, padx=10, pady=5)
            col += 1
            if col > 2:
                col = 0
                row += 1
        
        # File extensions info
        info_frame = ttk.LabelFrame(filetypes_frame, text="Supported Extensions", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create text widget for extensions
        self.extensions_text = scrolledtext.ScrolledText(info_frame, height=10)
        self.extensions_text.pack(fill=tk.BOTH, expand=True)
        
        # Populate extensions
        self.update_extensions_display()
        
    def setup_preview_tab(self, notebook):
        """Setup preview tab"""
        preview_frame = ttk.Frame(notebook)
        notebook.add(preview_frame, text="Preview")
        
        # Preview button
        btn_frame = ttk.Frame(preview_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Generate Preview", 
                  command=self.generate_preview).pack(pady=5)
        
        # Preview treeview
        tree_frame = ttk.LabelFrame(preview_frame, text="Preview Structure", padding=10)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview
        columns = ('type', 'year', 'month', 'count')
        self.preview_tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings')
        
        # Configure columns
        self.preview_tree.heading('type', text='Type')
        self.preview_tree.heading('year', text='Year')
        self.preview_tree.heading('month', text='Month')
        self.preview_tree.heading('count', text='File Count')
        
        self.preview_tree.column('type', width=100)
        self.preview_tree.column('year', width=80)
        self.preview_tree.column('month', width=120)
        self.preview_tree.column('count', width=80)
        
        # Add scrollbar
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", 
                           command=self.preview_tree.yview)
        self.preview_tree.configure(yscrollcommand=vsb.set)
        
        # Pack tree and scrollbar
        self.preview_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Summary label
        self.preview_summary = ttk.Label(preview_frame, text="")
        self.preview_summary.pack(pady=5)
        
    def setup_log_tab(self, notebook):
        """Setup log tab"""
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="Log")
        
        # Log text widget
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Log controls
        control_frame = ttk.Frame(log_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        ttk.Button(control_frame, text="Clear Log", 
                  command=self.clear_log).pack(side=tk.LEFT)
        ttk.Button(control_frame, text="Save Log...", 
                  command=self.save_log).pack(side=tk.LEFT, padx=(10, 0))
        
    def setup_progress_section(self, parent):
        """Setup progress bar and control buttons"""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Start/Stop button
        self.start_button = ttk.Button(control_frame, text="Start Organization", 
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
        self.status_label = ttk.Label(control_frame, text="Ready", 
                                     style='Status.TLabel')
        self.status_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Progress percentage
        self.progress_percent = ttk.Label(control_frame, text="0%")
        self.progress_percent.pack(side=tk.LEFT, padx=(10, 0))
        
    def browse_source(self):
        """Browse for source directory"""
        directory = filedialog.askdirectory(title="Select Source Directory")
        if directory:
            self.source_dir.set(directory)
            if not self.dest_dir.get():
                # Suggest destination
                self.dest_dir.set(directory)
    
    def browse_destination(self):
        """Browse for destination directory"""
        directory = filedialog.askdirectory(title="Select Destination Directory")
        if directory:
            self.dest_dir.set(directory)
    
    def update_extensions_display(self):
        """Update the file extensions display"""
        self.extensions_text.delete(1.0, tk.END)
        
        for file_type, extensions in self.supported_extensions.items():
            self.extensions_text.insert(tk.END, f"\n{file_type.upper()}:\n")
            self.extensions_text.insert(tk.END, "  " + ", ".join(extensions) + "\n")
        
        self.extensions_text.insert(tk.END, "\nOTHER:\n")
        self.extensions_text.insert(tk.END, "  All other file types\n")
    
    def generate_preview(self):
        """Generate preview of how files will be organized"""
        source = self.source_dir.get()
        if not source or not os.path.exists(source):
            messagebox.showerror("Error", "Please select a valid source directory.")
            return
        
        try:
            # Clear existing tree
            for item in self.preview_tree.get_children():
                self.preview_tree.delete(item)
            
            # Generate preview
            preview_data = self.scan_for_preview(source)
            total_files = 0
            
            # Insert into tree
            for file_type in sorted(preview_data.keys()):
                type_total = 0
                type_node = self.preview_tree.insert('', 'end', 
                                                    text=file_type.capitalize(),
                                                    values=(file_type, '', '', ''))
                
                for year in sorted(preview_data[file_type].keys()):
                    year_total = 0
                    year_node = self.preview_tree.insert(type_node, 'end',
                                                        text=str(year),
                                                        values=('', year, '', ''))
                    
                    for month in sorted(preview_data[file_type][year].keys()):
                        count = preview_data[file_type][year][month]
                        year_total += count
                        self.preview_tree.insert(year_node, 'end',
                                                text=f"{month} ({count} files)",
                                                values=('', '', month, count))
                    
                    type_total += year_total
                    self.preview_tree.item(year_node, values=('', year, '', year_total))
                
                total_files += type_total
                self.preview_tree.item(type_node, values=(file_type, '', '', type_total))
            
            # Update summary
            self.preview_summary.config(
                text=f"Total files found: {total_files} in {len(preview_data)} categories"
            )
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate preview: {str(e)}")
    
    def scan_for_preview(self, source_dir):
        """Scan directory for preview"""
        source_path = Path(source_dir)
        preview_data = {}
        
        # Determine which file types to include
        active_types = [ft for ft, var in self.file_types_vars.items() if var.get()]
        
        # Scan files
        files = source_path.rglob('*') if self.recursive.get() else source_path.glob('*')
        
        for file_path in files:
            if file_path.is_file():
                # Get file type
                file_type = self.get_file_type(file_path)
                
                # Skip if type not selected
                if file_type not in active_types:
                    continue
                
                # Get date
                try:
                    year, month, month_name = self.get_file_date(file_path)
                    
                    # Initialize data structure
                    if file_type not in preview_data:
                        preview_data[file_type] = {}
                    if year not in preview_data[file_type]:
                        preview_data[file_type][year] = {}
                    
                    month_key = f"{month:02d}-{month_name}"
                    preview_data[file_type][year][month_key] = \
                        preview_data[file_type][year].get(month_key, 0) + 1
                        
                except Exception as e:
                    self.log(f"Error scanning {file_path}: {str(e)}")
        
        return preview_data
    
    def get_file_type(self, file_path):
        """Get file type from extension"""
        suffix = file_path.suffix.lower()
        
        for category, extensions in self.supported_extensions.items():
            if suffix in extensions:
                return category
        
        return 'other'
    
    def get_file_date(self, file_path):
        """Get file date information"""
        try:
            if self.use_creation_date.get():
                if os.name == 'nt':  # Windows
                    timestamp = os.path.getctime(file_path)
                else:
                    timestamp = os.path.getmtime(file_path)
            else:
                timestamp = os.path.getmtime(file_path)
            
            dt = datetime.fromtimestamp(timestamp)
            return dt.year, dt.month, dt.strftime('%B')
            
        except Exception:
            dt = datetime.now()
            return dt.year, dt.month, dt.strftime('%B')
    
    def toggle_organization(self):
        """Start or stop organization process"""
        if not self.is_running:
            self.start_organization()
        else:
            self.stop_organization()
    
    def start_organization(self):
        """Start the organization process in a separate thread"""
        source = self.source_dir.get()
        if not source or not os.path.exists(source):
            messagebox.showerror("Error", "Please select a valid source directory.")
            return
        
        # Disable UI elements
        self.is_running = True
        self.start_button.config(text="Stop Organization")
        
        # Reset progress
        self.processed_files = 0
        self.progress_var.set(0)
        self.progress_percent.config(text="0%")
        self.status_label.config(text="Scanning files...")
        
        # Start organization thread
        thread = threading.Thread(target=self.organize_files, daemon=True)
        thread.start()
    
    def stop_organization(self):
        """Stop the organization process"""
        self.is_running = False
        self.start_button.config(text="Start Organization")
        self.status_label.config(text="Stopped")
    
    def organize_files(self):
        """Main organization function to run in thread"""
        try:
            source = Path(self.source_dir.get())
            dest = Path(self.dest_dir.get()) if self.dest_dir.get() else source
            
            # Get active file types
            active_types = [ft for ft, var in self.file_types_vars.items() if var.get()]
            
            # Collect files
            if self.recursive.get():
                all_files = list(source.rglob('*'))
            else:
                all_files = list(source.glob('*'))
            
            files = [f for f in all_files if f.is_file()]
            self.total_files = len(files)
            
            self.log(f"Found {self.total_files} files to organize")
            self.status_label.config(text=f"Organizing 0/{self.total_files} files...")
            
            # Process each file
            for i, file_path in enumerate(files, 1):
                if not self.is_running:
                    break
                
                # Check file type
                file_type = self.get_file_type(file_path)
                if file_type not in active_types:
                    continue
                
                # Get year filter
                year_filter = self.year_var.get()
                if year_filter:
                    year, month, month_name = self.get_file_date(file_path)
                    if str(year) != year_filter:
                        continue
                
                # Organize file
                if not self.dry_run.get():
                    self.organize_single_file(file_path, dest, file_type)
                else:
                    self.preview_organization(file_path, dest, file_type)
                
                # Update progress
                self.processed_files += 1
                progress = (i / self.total_files) * 100
                self.progress_var.set(progress)
                self.progress_percent.config(text=f"{int(progress)}%")
                self.status_label.config(
                    text=f"Organizing {i}/{self.total_files} files..."
                )
                
                # Update UI periodically
                if i % 10 == 0:
                    self.root.update_idletasks()
            
            # Complete
            if self.is_running:
                self.status_label.config(text="Organization complete!")
                self.log(f"Organization complete! Processed {self.processed_files} files.")
                messagebox.showinfo("Complete", 
                                  f"Organization complete!\nProcessed {self.processed_files} files.")
            
        except Exception as e:
            self.log(f"Error during organization: {str(e)}", level="ERROR")
            messagebox.showerror("Error", f"Organization failed: {str(e)}")
        finally:
            self.is_running = False
            self.start_button.config(text="Start Organization")
    
    def organize_single_file(self, file_path, dest_dir, file_type):
        """Organize a single file"""
        try:
            year, month, month_name = self.get_file_date(file_path)
            
            # Create destination path
            if self.organize_by_type.get():
                dest_path = dest_dir / file_type / str(year) / f"{month:02d}-{month_name}"
            else:
                dest_path = dest_dir / str(year) / f"{month:02d}-{month_name}"
            
            dest_path.mkdir(parents=True, exist_ok=True)
            
            # Handle duplicate names
            new_file_path = dest_path / file_path.name
            counter = 1
            while new_file_path.exists():
                stem = file_path.stem
                suffix = file_path.suffix
                new_file_path = dest_path / f"{stem}_{counter}{suffix}"
                counter += 1
            
            # Move file
            shutil.move(str(file_path), str(new_file_path))
            self.log(f"Moved: {file_path.name} -> {new_file_path}")
            
        except PermissionError:
            # Try copying instead
            shutil.copy2(str(file_path), str(new_file_path))
            self.log(f"Copied (permission denied): {file_path.name}")
        except Exception as e:
            self.log(f"Error organizing {file_path.name}: {str(e)}", level="ERROR")
    
    def preview_organization(self, file_path, dest_dir, file_type):
        """Preview organization without actually moving files"""
        try:
            year, month, month_name = self.get_file_date(file_path)
            
            if self.organize_by_type.get():
                dest_path = dest_dir / file_type / str(year) / f"{month:02d}-{month_name}"
            else:
                dest_path = dest_dir / str(year) / f"{month:02d}-{month_name}"
            
            self.log(f"Would move: {file_path.name} -> {dest_path}/")
            
        except Exception as e:
            self.log(f"Error previewing {file_path.name}: {str(e)}", level="ERROR")
    
    def log(self, message, level="INFO"):
        """Add message to log queue"""
        self.log_queue.put((level, message))
    
    def monitor_log_queue(self):
        """Monitor and process log messages from queue"""
        try:
            while not self.log_queue.empty():
                level, message = self.log_queue.get_nowait()
                
                # Format message
                timestamp = datetime.now().strftime("%H:%M:%S")
                formatted = f"[{timestamp}] {level}: {message}\n"
                
                # Add to log text widget
                self.log_text.insert(tk.END, formatted)
                
                # Auto-scroll to end
                self.log_text.see(tk.END)
                
                # Color code errors
                if level == "ERROR":
                    self.log_text.tag_add("error", 
                                         f"{self.log_text.index('end-2l').split('.')[0]}.0",
                                         f"{self.log_text.index('end-2l').split('.')[0]}.end")
                    self.log_text.tag_config("error", foreground="red")
                
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
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                self.log(f"Log saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save log: {str(e)}")

def main():
    """Main function"""
    root = tk.Tk()
    app = FileOrganizerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()