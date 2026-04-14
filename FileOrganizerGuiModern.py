"""
Modern version with additional features
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from tkinter import font as tkfont
import os
import shutil
import threading
import queue
from datetime import datetime
from pathlib import Path
import json
from PIL import Image, ImageTk
import platform

class ModernFileOrganizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("📁 Smart File Organizer")
        self.root.geometry("1000x750")
        
        # Set application icon (if available)
        self.set_icon()
        
        # Variables
        self.config_file = Path.home() / '.file_organizer_config.json'
        self.settings = self.load_settings()
        
        # Setup UI
        self.setup_ui()
        
        # Load saved settings
        self.load_saved_settings()
        
    def set_icon(self):
        """Set application icon"""
        try:
            # Try to load an icon file
            icon_path = Path("icon.png")
            if icon_path.exists():
                self.root.iconphoto(False, tk.PhotoImage(file=str(icon_path)))
        except:
            pass
    
    def setup_ui(self):
        """Setup modern UI"""
        # Configure styles
        self.setup_styles()
        
        # Create main container
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        self.create_header()
        
        # Main content area
        self.create_main_content()
        
        # Footer
        self.create_footer()
    
    def setup_styles(self):
        """Configure modern styles"""
        style = ttk.Style()
        
        # Use system theme
        if platform.system() == 'Windows':
            style.theme_use('vista')
        elif platform.system() == 'Darwin':
            style.theme_use('aqua')
        else:
            style.theme_use('clam')
        
        # Custom colors
        self.colors = {
            'primary': '#007acc',
            'secondary': '#2d2d30',
            'accent': '#68217a',
            'success': '#107c10',
            'warning': '#ffb900',
            'danger': '#e81123',
            'light': '#f3f3f3',
            'dark': '#1e1e1e'
        }
        
        # Configure custom styles
        style.configure('Primary.TButton',
                       background=self.colors['primary'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 10))
        
        style.map('Primary.TButton',
                 background=[('active', '#106ebe'), ('pressed', '#005a9e')])
        
        style.configure('Title.TLabel',
                       font=('Segoe UI', 24, 'bold'),
                       foreground=self.colors['primary'])
        
        style.configure('Subtitle.TLabel',
                       font=('Segoe UI', 11),
                       foreground=self.colors['secondary'])
    
    def create_header(self):
        """Create application header"""
        header_frame = ttk.Frame(self.main_container)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Title
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(title_frame, text="Smart File Organizer", 
                               style='Title.TLabel')
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = ttk.Label(title_frame, 
                                  text="Organize files by date automatically",
                                  style='Subtitle.TLabel')
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0), pady=8)
        
        # Theme toggle
        self.dark_mode = tk.BooleanVar(value=False)
        theme_btn = ttk.Checkbutton(title_frame, text="🌙 Dark Mode",
                                   variable=self.dark_mode,
                                   command=self.toggle_theme)
        theme_btn.pack(side=tk.RIGHT)
    
    def create_main_content(self):
        """Create main content area"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.setup_quick_start_tab()
        self.setup_advanced_tab()
        self.setup_stats_tab()
        self.setup_batch_tab()
    
    def setup_quick_start_tab(self):
        """Setup quick start tab"""
        quick_frame = ttk.Frame(self.notebook)
        self.notebook.add(quick_frame, text="🚀 Quick Start")
        
        # Simple interface for quick organization
        ttk.Label(quick_frame, text="Quick File Organization", 
                 font=('Segoe UI', 14, 'bold')).pack(pady=20)
        
        # Source selection
        source_frame = ttk.Frame(quick_frame)
        source_frame.pack(fill=tk.X, padx=50, pady=10)
        
        ttk.Label(source_frame, text="Source Folder:").pack(side=tk.LEFT)
        self.source_var = tk.StringVar()
        ttk.Entry(source_frame, textvariable=self.source_var, 
                 width=40).pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        ttk.Button(source_frame, text="Browse", 
                  command=self.browse_source).pack(side=tk.LEFT)
        
        # Quick organize button
        ttk.Button(quick_frame, text="Organize Now", 
                  style='Primary.TButton',
                  command=self.quick_organize).pack(pady=30)
        
        # Quick stats
        self.quick_stats_label = ttk.Label(quick_frame, text="")
        self.quick_stats_label.pack()
    
    def setup_advanced_tab(self):
        """Setup advanced tab (similar to original)"""
        # ... (similar to previous implementation)
        pass
    
    def setup_stats_tab(self):
        """Setup statistics tab"""
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="📊 Statistics")
        
        # Statistics display
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=20)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Refresh button
        ttk.Button(stats_frame, text="Refresh Statistics",
                  command=self.update_stats).pack(pady=10)
    
    def setup_batch_tab(self):
        """Setup batch operations tab"""
        batch_frame = ttk.Frame(self.notebook)
        self.notebook.add(batch_frame, text="⚙️ Batch")
        
        # Multiple source folders
        ttk.Label(batch_frame, text="Batch Operations", 
                 font=('Segoe UI', 14, 'bold')).pack(pady=10)
        
        # Source listbox
        list_frame = ttk.Frame(batch_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.batch_listbox = tk.Listbox(list_frame, height=10)
        self.batch_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Listbox controls
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(side=tk.RIGHT, padx=(10, 0))
        
        ttk.Button(btn_frame, text="Add", 
                  command=self.add_batch_folder).pack(pady=5)
        ttk.Button(btn_frame, text="Remove", 
                  command=self.remove_batch_folder).pack(pady=5)
        ttk.Button(btn_frame, text="Clear", 
                  command=self.clear_batch_folders).pack(pady=5)
        
        # Batch organize button
        ttk.Button(batch_frame, text="Organize All", 
                  style='Primary.TButton',
                  command=self.batch_organize).pack(pady=20)
    
    def create_footer(self):
        """Create application footer"""
        footer_frame = ttk.Frame(self.main_container)
        footer_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(footer_frame, 
                                           variable=self.progress_var,
                                           mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(footer_frame, text="Ready")
        self.status_label.pack()
    
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        # Implement theme switching
        pass
    
    def browse_source(self):
        """Browse for source folder"""
        folder = filedialog.askdirectory(title="Select Source Folder")
        if folder:
            self.source_var.set(folder)
    
    def quick_organize(self):
        """Quick organization with default settings"""
        source = self.source_var.get()
        if not source or not os.path.exists(source):
            messagebox.showerror("Error", "Please select a valid source folder.")
            return
        
        # Run organization in thread
        thread = threading.Thread(target=self.run_quick_organize, 
                                 args=(source,), daemon=True)
        thread.start()
    
    def run_quick_organize(self, source):
        """Run quick organization"""
        try:
            # Implement organization logic
            self.update_status("Organizing...")
            
            # Simulate progress
            for i in range(101):
                if not self.is_running:
                    break
                self.progress_var.set(i)
                self.root.after(10)
            
            self.update_status("Complete!")
            
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
    
    def update_status(self, message):
        """Update status label"""
        self.status_label.config(text=message)
    
    def load_settings(self):
        """Load saved settings"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_settings(self):
        """Save current settings"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except:
            pass
    
    def load_saved_settings(self):
        """Load saved settings into UI"""
        if 'last_source' in self.settings:
            self.source_var.set(self.settings['last_source'])
    
    def add_batch_folder(self):
        """Add folder to batch list"""
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            self.batch_listbox.insert(tk.END, folder)
    
    def remove_batch_folder(self):
        """Remove selected folder from batch list"""
        selection = self.batch_listbox.curselection()
        if selection:
            self.batch_listbox.delete(selection)
    
    def clear_batch_folders(self):
        """Clear all batch folders"""
        self.batch_listbox.delete(0, tk.END)
    
    def batch_organize(self):
        """Organize all batch folders"""
        folders = self.batch_listbox.get(0, tk.END)
        if not folders:
            messagebox.showinfo("Info", "No folders selected.")
            return
        
        # Confirm
        if not messagebox.askyesno("Confirm", 
                                  f"Organize {len(folders)} folders?"):
            return
        
        # Process each folder
        for folder in folders:
            if os.path.exists(folder):
                # Process folder
                pass

def main():
    """Main function"""
    root = tk.Tk()
    app = ModernFileOrganizerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()