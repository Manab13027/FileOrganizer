"""
Additional styles for the File Organizer GUI
"""
import tkinter as tk
from tkinter import ttk

def configure_styles():
    """Configure custom styles for the application"""
    style = ttk.Style()
    
    # Configure colors
    bg_color = '#f0f0f0'
    accent_color = '#4a86e8'
    
    # Configure ttk styles
    style.configure('Accent.TButton',
                   background=accent_color,
                   foreground='white',
                   borderwidth=1,
                   focuscolor='none')
    style.map('Accent.TButton',
              background=[('active', '#3a76d8'), ('pressed', '#2a66c8')])
    
    # Configure treeview
    style.configure('Treeview',
                   background='white',
                   foreground='black',
                   fieldbackground='white',
                   rowheight=25)
    style.configure('Treeview.Heading',
                   background='#e0e0e0',
                   foreground='black',
                   relief='flat',
                   font=('Arial', 10, 'bold'))
    style.map('Treeview',
              background=[('selected', accent_color)],
              foreground=[('selected', 'white')])
    
    # Configure notebook
    style.configure('TNotebook.Tab',
                   padding=[10, 5],
                   font=('Arial', 10))
    
    # Configure labelframe
    style.configure('TLabelframe',
                   background=bg_color)
    style.configure('TLabelframe.Label',
                   background=bg_color,
                   font=('Arial', 10, 'bold'))