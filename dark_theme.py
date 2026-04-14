"""
Dark theme for the File Organizer
"""
import tkinter as tk
from tkinter import ttk

class DarkTheme:
    """Apply dark theme to the application"""
    
    COLORS = {
        'bg': '#2b2b2b',
        'fg': '#ffffff',
        'accent': '#4a86e8',
        'frame_bg': '#3c3c3c',
        'entry_bg': '#404040',
        'entry_fg': '#ffffff',
        'button_bg': '#404040',
        'button_fg': '#ffffff',
        'tree_bg': '#404040',
        'tree_fg': '#ffffff',
        'tree_sel_bg': '#4a86e8',
        'tree_sel_fg': '#ffffff',
        'tab_bg': '#3c3c3c',
        'tab_fg': '#ffffff',
        'tab_sel_bg': '#4a86e8',
        'tab_sel_fg': '#ffffff'
    }
    
    @classmethod
    def apply(cls, root):
        """Apply dark theme to root window and all widgets"""
        # Configure root window
        root.configure(bg=cls.COLORS['bg'])
        
        # Configure ttk styles
        style = ttk.Style()
        
        # Configure styles for all widgets
        style.configure('.',
                       background=cls.COLORS['bg'],
                       foreground=cls.COLORS['fg'],
                       fieldbackground=cls.COLORS['entry_bg'],
                       insertcolor=cls.COLORS['fg'])
        
        # Specific widget styles
        style.configure('TLabel',
                       background=cls.COLORS['bg'],
                       foreground=cls.COLORS['fg'])
        
        style.configure('TFrame',
                       background=cls.COLORS['frame_bg'])
        
        style.configure('TLabelframe',
                       background=cls.COLORS['frame_bg'])
        
        style.configure('TLabelframe.Label',
                       background=cls.COLORS['frame_bg'],
                       foreground=cls.COLORS['fg'])
        
        style.configure('TEntry',
                       fieldbackground=cls.COLORS['entry_bg'],
                       foreground=cls.COLORS['entry_fg'])
        
        style.configure('TButton',
                       background=cls.COLORS['button_bg'],
                       foreground=cls.COLORS['button_fg'])
        
        style.configure('TCheckbutton',
                       background=cls.COLORS['bg'],
                       foreground=cls.COLORS['fg'])
        
        style.configure('TRadiobutton',
                       background=cls.COLORS['bg'],
                       foreground=cls.COLORS['fg'])
        
        style.configure('TNotebook',
                       background=cls.COLORS['bg'],
                       tabmargins=[2, 5, 2, 0])
        
        style.configure('TNotebook.Tab',
                       background=cls.COLORS['tab_bg'],
                       foreground=cls.COLORS['tab_fg'],
                       padding=[10, 5])
        
        style.map('TNotebook.Tab',
                  background=[('selected', cls.COLORS['tab_sel_bg'])],
                  foreground=[('selected', cls.COLORS['tab_sel_fg'])])
        
        style.configure('Treeview',
                       background=cls.COLORS['tree_bg'],
                       foreground=cls.COLORS['tree_fg'],
                       fieldbackground=cls.COLORS['tree_bg'])
        
        style.configure('Treeview.Heading',
                       background=cls.COLORS['tab_bg'],
                       foreground=cls.COLORS['tab_fg'])
        
        style.map('Treeview',
                  background=[('selected', cls.COLORS['tree_sel_bg'])],
                  foreground=[('selected', cls.COLORS['tree_sel_fg'])])
        
        style.configure('Horizontal.TProgressbar',
                       background=cls.COLORS['accent'],
                       troughcolor=cls.COLORS['frame_bg'])