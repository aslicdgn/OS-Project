import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import tkinter as tk
from tkinter import ttk, messagebox
from process.pcb import PCB
from process.manager import ProcessManager
from process.power_scheduler import PowerAwareScheduler
from memory.memory_manager import MemoryManager
from filesystem.mobile_fs import FileSystem
from concurrency.background_tasks import CameraTask, MusicTask, SchedulerTask, PhotoConsumer
import cv2
from PIL import Image, ImageTk
import re
import io
import pygame
import base64
from ui.themes import get_light_theme, get_dark_theme
from ui.icons import ICONS

class OSVisualizer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mini Mobile OS - Single User")
        self.geometry("1080x600")

        self.theme = 'light'
        self.theme_colors = get_light_theme()

        self.scheduler = PowerAwareScheduler()
        self.process_manager = ProcessManager(self.scheduler)
        self.memory = MemoryManager()
        self.fs = FileSystem()

        self.bg_camera = CameraTask(self.fs, log_fn=self.log_message)
        self.bg_music = MusicTask(self.memory, pid=99)
        self.bg_scheduler = SchedulerTask(self.scheduler)
        self.bg_consumer = PhotoConsumer(log_fn=self.log_message, update_fn=self.increment_processed_count)

        self.setup_toolbar()

        self.status_frame = ttk.Frame(self)
        self.status_frame.pack(fill="x", padx=10, pady=(10, 0))


        self.setup_ui()
        self.refresh()

        self.processed_count = 0
        self.photo_counter = 1

    def switch_theme(self):
        if self.theme == 'light':
            self.theme = 'dark'
            self.theme_colors = get_dark_theme()
        else:
            self.theme = 'light'
            self.theme_colors = get_light_theme()
        self.apply_theme()

    def apply_theme(self):
        c = self.theme_colors
        self.configure(bg=c['bg'])
        # ttk için stil tanımla
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Status.TFrame', background=c['status_bg'])
        style.configure('Status.TLabel', background=c['status_bg'], foreground=c['status_fg'])
        style.configure('TLabel', background=c['bg'], foreground=c['fg'])
        style.configure('TButton', background=c['bg'], foreground=c['fg'])
        style.configure('TLabelframe', background=c['bg'], foreground=c['fg'])
        style.configure('TLabelframe.Label', background=c['bg'], foreground=c['fg'])
        style.configure('Info.TLabelframe', background=c['bg'], foreground=c['fg'])
        style.configure('Info.TLabelframe.Label', background=c['bg'], foreground=c['fg'])
        # ttk tabanlı widget'larda stil uygula
        if hasattr(self, 'info_frame'):
            self.info_frame.configure(style='Info.TLabelframe')
        # Klasik tk widget'larda doğrudan renk uygula
        if hasattr(self, 'process_text'):
            self.process_text.configure(bg=c['bg'], fg=c['fg'])
        if hasattr(self, 'memory_canvas'):
            self.memory_canvas.configure(bg=c['bg'])
        if hasattr(self, 'file_text'):
            self.file_text.configure(bg=c['bg'], fg=c['fg'])
        if hasattr(self, 'log_text'):
            self.log_text.configure(bg='#222' if self.theme=='dark' else 'black', fg=c['fg'])
        # Tema düğmesi ikonu
        if hasattr(self, 'theme_btn'):
            self.theme_btn.configure(text=ICONS['theme_dark'] if self.theme=='dark' else ICONS['theme_light'])

    def setup_toolbar(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(side="top", fill="x")

        btn_block_view = ttk.Button(toolbar, text="View Block Storage", command=self.show_block_storage)
        btn_block_view.pack(side="left", padx=5)


    def increment_processed_count(self):
        self.processed_count += 1
        if hasattr(self, 'processed_label'):
            self.processed_label.config(text=f"Processed Photos: {self.processed_count}")
            
    def show_block_storage(self):
        """Show block storage visualization window with detailed information"""
        if hasattr(self, 'block_window') and self.block_window.winfo_exists():
            self.block_window.lift()
            return
            
        self.block_window = tk.Toplevel(self)
        self.block_window.title("Storage Visualization")
        self.block_window.geometry("1200x800")
        
        
        notebook = ttk.Notebook(self.block_window)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        
        block_tab = ttk.Frame(notebook)
        notebook.add(block_tab, text="Block Storage")
        
       
        stats_frame = ttk.LabelFrame(block_tab, text="Storage Statistics")
        stats_frame.pack(fill='x', pady=(0, 10), padx=5)
        
      
        block_storage = self.fs.storage if hasattr(self.fs, 'storage') else None
        block_cache = self.fs.cache if hasattr(self.fs, 'cache') else None
        
        if not block_storage:
            ttk.Label(stats_frame, text="Block storage not initialized").pack(pady=10)
            return
       
        total_blocks = len(block_storage.blocks)
        total_size = sum(len(block) for block in block_storage.blocks.values())
        block_size = getattr(block_storage, 'BLOCK_SIZE', 512)
        
       
        cache_hits = getattr(block_cache, 'hits', 0) if block_cache else 0
        cache_misses = getattr(block_cache, 'misses', 0) if block_cache else 0
        cache_size = len(block_cache.cache) if block_cache else 0
        cache_capacity = getattr(block_cache, 'capacity', 0) if block_cache else 0
        
        # Display stats in a grid
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill='x', padx=10, pady=5)
        
        # Storage stats
        ttk.Label(stats_grid, text="Storage:", font=('Arial', 9, 'bold')).grid(row=0, column=0, sticky='w')
        ttk.Label(stats_grid, text=f"• Total Blocks: {total_blocks}").grid(row=0, column=1, sticky='w', padx=10)
        ttk.Label(stats_grid, text=f"• Used: {total_size} / {total_blocks * block_size} bytes").grid(row=0, column=2, sticky='w', padx=10)
        ttk.Label(stats_grid, text=f"• Block Size: {block_size} bytes").grid(row=0, column=3, sticky='w', padx=10)
        
        # Cache stats
        if block_cache:
            ttk.Label(stats_grid, text="\nCache:", font=('Arial', 9, 'bold')).grid(row=1, column=0, sticky='w', pady=(10,0))
            ttk.Label(stats_grid, text=f"• Size: {cache_size}/{cache_capacity} blocks").grid(row=1, column=1, sticky='w', padx=10)
            hit_ratio = cache_hits / (cache_hits + cache_misses) if (cache_hits + cache_misses) > 0 else 0
            ttk.Label(stats_grid, text=f"• Hit Ratio: {hit_ratio:.1%}").grid(row=1, column=2, sticky='w', padx=10)
        
        # Block visualization frame
        vis_frame = ttk.LabelFrame(block_tab, text="Block Storage Map")
        vis_frame.pack(fill='both', expand=True, padx=5)
        
        # Create canvas with scrollbar
        canvas = tk.Canvas(vis_frame, bg='white')
        scrollbar = ttk.Scrollbar(vis_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Display blocks in a grid (4 columns)
        columns = 4
        row = col = 0
        
        # Get all files and their blocks
        file_blocks = {}
        def collect_file_blocks(directory, path=""):
            for name, file in directory.files.items():
                if hasattr(file, 'blocks'):
                    file_path = f"{path}/{name}" if path else name
                    file_blocks[file_path] = {
                        'blocks': file.blocks,
                        'encrypted': self.fs.is_encrypted(name) if hasattr(self.fs, 'is_encrypted') else False,
                        'size': getattr(file, 'size', 0)
                    }
            for name, subdir in directory.subdirectories.items():
                new_path = f"{path}/{name}" if path else name
                collect_file_blocks(subdir, new_path)
        
        collect_file_blocks(self.fs.root)
        
        # Create a mapping of block_id to file names
        block_to_files = {}
        for file_path, data in file_blocks.items():
            for block_id in data['blocks']:
                if block_id not in block_to_files:
                    block_to_files[block_id] = []
                block_to_files[block_id].append(file_path)
        
        # Display blocks
        for block_id, block in block_storage.blocks.items():
            # Create block frame
            block_frame = ttk.Frame(scrollable_frame, width=280, height=140, 
                                  relief='solid', padding=5)
            block_frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
            
            # Block header
            header_frame = ttk.Frame(block_frame)
            header_frame.pack(fill='x')
            
            # Block ID (truncated) with copy button
            short_id = f"{block_id[:6]}...{block_id[-2:]}"
            ttk.Label(header_frame, text=f"Block: {short_id}", font=('Arial', 8, 'bold')).pack(side='left')
            
            # Cache indicator
            in_cache = block_cache and block_id in block_cache.cache if block_cache else False
            cache_icon = "✓" if in_cache else "✗"
            cache_color = "green" if in_cache else "gray"
            ttk.Label(header_frame, text=f"Cache: {cache_icon}", 
                     foreground=cache_color, font=('Arial', 8)).pack(side='right', padx=5)
            
            # Block info
            block_size = len(block)
            usage_ratio = min(block_size / block_size, 1.0)
            
            # Files using this block
            files_using = block_to_files.get(block_id, [])
            files_text = "\n".join([f"• {f}" for f in files_using[:2]])
            if len(files_using) > 2:
                files_text += f"\n• ...and {len(files_using)-2} more"
            
            ttk.Label(block_frame, text=f"Size: {block_size} B", 
                     font=('Arial', 8)).pack(anchor='w')
            
            # Visual usage bar
            usage_frame = ttk.Frame(block_frame, height=15)
            usage_frame.pack(fill='x', pady=2)
            
            canvas = tk.Canvas(usage_frame, height=15, bg='#f0f0f0', 
                            highlightthickness=0)
            canvas.pack(fill='x')
            canvas.create_rectangle(0, 0, 200 * usage_ratio, 15, 
                                 fill='#4CAF50', outline='')
            canvas.create_text(100, 7, text=f"{usage_ratio:.0%} full", 
                            fill='black' if usage_ratio < 0.5 else 'white')
            
            # Files using this block
            if files_using:
                ttk.Label(block_frame, text="Used by:", 
                         font=('Arial', 7, 'bold')).pack(anchor='w', pady=(5,0))
                ttk.Label(block_frame, text=files_text if files_using else "(Free)", 
                         font=('Arial', 7), wraplength=250, justify='left').pack(anchor='w')
            
            
            col = (col + 1) % columns
            if col == 0:
                row += 1
        
    
        for i in range(columns):
            scrollable_frame.columnconfigure(i, weight=1)
        
        # Tab 2: File System Tree
        fs_tab = ttk.Frame(notebook)
        notebook.add(fs_tab, text="File System")
        
     
        tree_frame = ttk.Frame(fs_tab)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
     
        tree_scroll_y = ttk.Scrollbar(tree_frame)
        tree_scroll_y.pack(side='right', fill='y')
        
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient='horizontal')
        tree_scroll_x.pack(side='bottom', fill='x')
        
        # Create the tree
        tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll_y.set, 
                          xscrollcommand=tree_scroll_x.set)
        tree.pack(fill='both', expand=True)
      
        tree_scroll_y.config(command=tree.yview)
        tree_scroll_x.config(command=tree.xview)
        
       
        tree['columns'] = ('type', 'size', 'created', 'encrypted')
        tree.column('#0', width=300, minwidth=150)
        tree.column('type', width=100, anchor='w')
        tree.column('size', width=100, anchor='e')
        tree.column('created', width=150, anchor='w')
        tree.column('encrypted', width=80, anchor='center')
        
        tree.heading('#0', text='Name', anchor='w')
        tree.heading('type', text='Type', anchor='w')
        tree.heading('size', text='Size', anchor='e')
        tree.heading('created', text='Created', anchor='w')
        tree.heading('encrypted', text='Encrypted', anchor='center')
        
       
        def add_directory(directory, parent=''):
            dir_id = tree.insert(parent, 'end', text=directory.name, 
                              values=('Directory', '', directory.created_at, ''))
            
           
            for name, subdir in directory.subdirectories.items():
                add_directory(subdir, dir_id)
            
            # Add files
            for name, file in directory.files.items():
                is_encrypted = self.fs.is_encrypted(name) if hasattr(self.fs, 'is_encrypted') else False
                tree.insert(dir_id, 'end', text=name,
                           values=('File', f"{getattr(file, 'size', 0)} B", 
                                 getattr(file, 'created_at', ''), 
                                 '✓' if is_encrypted else '✗'))
        
        add_directory(self.fs.root)
        
        # Add a close button
        btn_frame = ttk.Frame(self.block_window)
        btn_frame.pack(fill='x', pady=(0, 10))
        
        refresh_btn = ttk.Button(btn_frame, text="Refresh", 
                               command=lambda: self.refresh_block_view())
        refresh_btn.pack(side='left', padx=5)
        
        close_btn = ttk.Button(btn_frame, text="Close", 
                             command=self.block_window.destroy)
        close_btn.pack(side='right', padx=5)
        
        # Store references
        self.block_window.tree = tree
        
    def refresh_block_view(self):
        """Refresh the block storage view"""
        if hasattr(self, 'block_window') and self.block_window.winfo_exists():
            self.block_window.destroy()
            self.show_block_storage()


    def fs_go_back(self):
        if len(self.fs.path_stack) > 1:
            self.fs.cd("..")
            self.update_file_display()


    def setup_ui(self):
        # Status Bar
        self.status_frame = ttk.Frame(self)
        self.status_frame.pack(fill="x", padx=10, pady=(10, 0))

        # Modern ikonlu status bar - büyük, renkli ve bold
        status_font = ("Segoe UI", 12, "bold")
        icon_font = ("Segoe UI Emoji", 16, "bold")
        self.clock_icon = ttk.Label(self.status_frame, text=ICONS['clock'], font=icon_font, foreground="#1976d2")
        self.clock_icon.pack(side="left", padx=(2,0))
        self.bg_status = ttk.Label(self.status_frame, text=f"{ICONS['process']} Background Tasks: Stopped",
                                 foreground="#d32f2f", font=status_font, relief="sunken", padding=5)
        self.bg_status.pack(side="left", padx=2)
        self.mem_status = ttk.Label(self.status_frame, text=f"{ICONS['memory']} Memory: 0/0 KB",
                                  font=status_font, relief="sunken", padding=5, foreground="#388e3c")
        self.mem_status.pack(side="left", padx=2)
        self.proc_status = ttk.Label(self.status_frame, text=f"{ICONS['process']} Processes: 0",
                                   font=status_font, relief="sunken", padding=5, foreground="#1976d2")
        self.proc_status.pack(side="left", padx=2)
        self.network_icon = ttk.Label(self.status_frame, text=ICONS['network'], font=icon_font, foreground="#0288d1")
        self.network_icon.pack(side="right", padx=(0,2))
        self.battery_icon = ttk.Label(self.status_frame, text=ICONS['battery'], font=icon_font, foreground="#fbc02d")
        self.battery_icon.pack(side="right", padx=(0,2))
       
        self.theme_btn = ttk.Button(self.status_frame, text=ICONS['theme_light'], width=3, command=self.switch_theme)
        self.theme_btn.pack(side="right", padx=(0,2))
       
   
        self.apply_theme()


        self.time_status = ttk.Label(self.status_frame, text="System Time: 00:00:00",
                                   relief="sunken", padding=5)
        self.time_status.pack(side="right", padx=2)

        self.info_frame = ttk.LabelFrame(self, text="System State")
        self.info_frame.pack(fill="both", expand=True, padx=10, pady=5)

        top_panel = ttk.Frame(self.info_frame)
        top_panel.pack(fill="both", expand=True)

        proc_frame = ttk.LabelFrame(top_panel, text="Processes")
        proc_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.process_text = tk.Text(proc_frame, height=10, width=50)
        self.process_text.pack(fill="both", expand=True, padx=5, pady=5)

        mem_frame = ttk.LabelFrame(top_panel, text="Memory")
        mem_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        
        self.memory_canvas = tk.Canvas(mem_frame, height=150, bg='white')
        self.memory_canvas.pack(fill="both", expand=True, padx=5, pady=5)

       
        self.mem_stats = ttk.Label(mem_frame, text="Total: 0 KB | Used: 0 KB | Free: 0 KB")
        self.mem_stats.pack(fill="x", padx=5, pady=(0, 5))

        bottom_panel = ttk.Frame(self.info_frame)
        bottom_panel.pack(fill="both", expand=True)

    
        fs_frame = ttk.LabelFrame(bottom_panel, text="File System")
        fs_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        
        style = ttk.Style()
        style.configure('Modern.Vertical.TScrollbar', gripcount=0, background='#b0bec5', troughcolor='#eceff1', bordercolor='#90a4ae', lightcolor='#eceff1', darkcolor='#90a4ae', arrowcolor='#1976d2')
        
        self.fs_tree = ttk.Treeview(fs_frame, columns=("type",), show="tree")
        vsb = ttk.Scrollbar(fs_frame, orient="vertical", command=self.fs_tree.yview, style='Modern.Vertical.TScrollbar')
        self.fs_tree.configure(yscrollcommand=vsb.set)
        self.fs_tree.pack(side="left", fill="both", expand=True, padx=2, pady=2)
        vsb.pack(side="left", fill="y")
        self.fs_tree.bind("<<TreeviewSelect>>", self.on_fs_select)
        
        nav_frame = ttk.Frame(fs_frame)
        nav_frame.pack(side="top", fill="x", pady=(2,0))
        self.fs_path_label = ttk.Label(nav_frame, text="/", font=("Segoe UI", 9, "italic"))
        self.fs_path_label.pack(side="left", padx=4)
   
        ttk.Label(nav_frame, text="🔍 Search:").pack(side="left", padx=(10,2))
        self.fs_search_var = tk.StringVar()
        fs_search_entry = ttk.Entry(nav_frame, textvariable=self.fs_search_var, width=16)
        fs_search_entry.pack(side="left", padx=(0,4))
        self.fs_search_var.trace_add('write', lambda *args: self.update_file_display())
        back_btn = ttk.Button(nav_frame, text="⬅️ Back", command=self.fs_go_back, style="Modern.TButton")
        back_btn.pack(side="right", padx=2)
        new_folder_btn = ttk.Button(nav_frame, text="📁 New Folder", command=self.create_folder_popup, style="Modern.TButton")
        new_folder_btn.pack(side="right", padx=2)
        self._add_tooltip(new_folder_btn, "Create new folder")
        self._add_tooltip(back_btn, "Go to parent directory")
     
        self.fs_detail = tk.Text(fs_frame, height=8, width=30, state='disabled')
        log_vsb = ttk.Scrollbar(fs_frame, orient="vertical", command=self.fs_detail.yview, style='Modern.Vertical.TScrollbar')
        self.fs_detail.configure(yscrollcommand=log_vsb.set)
        self.fs_detail.pack(side="right", fill="both", expand=False, padx=2, pady=2)
        log_vsb.pack(side="right", fill="y")
      
        self.camera_frame = ttk.Frame(fs_frame, height=120)
        self.camera_frame.pack_propagate(False)
        self.camera_frame.pack(side="top", fill="x", padx=2, pady=5)
        self.camera_label = tk.Label(self.camera_frame)
        self.camera_label.pack(fill="both", expand=True)
       
        btn_frame = ttk.Frame(fs_frame)
        btn_frame.pack(side="bottom", fill="x", pady=2)
        style = ttk.Style()
        style.configure("Modern.TButton", font=("Segoe UI", 10, "bold"), padding=6, foreground="#222", background="#e0e0e0", borderwidth=0, focusthickness=3, focuscolor="#aaa")
        style.map("Modern.TButton",
                  background=[('active', '#b3e5fc'), ('!active', '#e0e0e0')],
                  relief=[('pressed', 'sunken'), ('!pressed', 'raised')])
        style.configure('Hovered.TButton', background='#b3e5fc', foreground="#1976d2", font=("Segoe UI", 10, "bold"))
        new_file_btn = ttk.Button(btn_frame, text="➕ New File", command=self.create_file_popup, style="Modern.TButton")
        new_file_btn.pack(side="left", padx=2)
        del_file_btn = ttk.Button(btn_frame, text="🗑️ Delete", command=self.delete_selected_file, style="Modern.TButton")
        del_file_btn.pack(side="left", padx=2)
        self._add_tooltip(new_file_btn, "Create new file")
        self._add_tooltip(del_file_btn, "Delete selected file")
  
        def hover_on(e, btn): btn.configure(style='Hovered.TButton')
        def hover_off(e, btn): btn.configure(style='Modern.TButton')
        new_file_btn.bind('<Enter>', lambda e: hover_on(e, new_file_btn))
        new_file_btn.bind('<Leave>', lambda e: hover_off(e, new_file_btn))
        del_file_btn.bind('<Enter>', lambda e: hover_on(e, del_file_btn))
        del_file_btn.bind('<Leave>', lambda e: hover_off(e, del_file_btn))
        new_folder_btn.bind('<Enter>', lambda e: hover_on(e, new_folder_btn))
        new_folder_btn.bind('<Leave>', lambda e: hover_off(e, new_folder_btn))
        back_btn.bind('<Enter>', lambda e: hover_on(e, back_btn))
        back_btn.bind('<Leave>', lambda e: hover_off(e, back_btn))
  
        def on_tree_motion(event):
            row = self.fs_tree.identify_row(event.y)
            for iid in self.fs_tree.get_children():
                self.fs_tree.item(iid, tags=())
            if row:
                self.fs_tree.tag_configure('hover', background='#e3f2fd')
                self.fs_tree.item(row, tags=('hover',))
        def on_tree_leave(event):
            for iid in self.fs_tree.get_children():
                self.fs_tree.item(iid, tags=())
        self.fs_tree.bind('<Motion>', on_tree_motion)
        self.fs_tree.bind('<Leave>', on_tree_leave)
        self.fs_tree.bind("<Double-1>", self.on_tree_double_click)


        # System Log Panel
        log_frame = ttk.LabelFrame(bottom_panel, text="System Log")
        log_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)


        self.processed_label = ttk.Label(log_frame, text="Processed Photos: 0")
        self.processed_label.pack(anchor="w", padx=5, pady=(0, 2))

        self.log_text = tk.Text(log_frame, height=8, width=50, state='disabled',
                               bg='black', fg='lightgray')
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Controls Frame
        self.control_frame = ttk.LabelFrame(self, text="Controls")
        self.control_frame.pack(fill="x", padx=10, pady=5)
        ctrl_style = ttk.Style()
        ctrl_style.configure("Ctrl.TButton", font=("Segoe UI", 10, "bold"), padding=6, foreground="#222", background="#e0e0e0", borderwidth=0)
        ctrl_style.map("Ctrl.TButton",
            background=[('active', '#e3f2fd'), ('!active', '#e0e0e0')],
            relief=[('pressed', 'sunken'), ('!pressed', 'raised')])
        ctrl_style.configure('Ctrl.Hovered.TButton', background='#e3f2fd', foreground="#1976d2", font=("Segoe UI", 10, "bold"), padding=6, borderwidth=0)
      
        app_frame = ttk.Frame(self.control_frame)
        app_frame.pack(side="left", padx=(0, 10))
        ttk.Label(app_frame, text="📱 Applications:", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 5))
        cam_btn = ttk.Button(app_frame, text="📷 Launch Camera", command=self.launch_camera, style="Ctrl.TButton")
        cam_btn.pack(side="left", padx=2)
        mus_btn = ttk.Button(app_frame, text="🎵 Launch Music", command=self.launch_music, style="Ctrl.TButton")
        mus_btn.pack(side="left", padx=2)
  
        for btn in [cam_btn, mus_btn]:
            btn.bind('<Enter>', lambda e, b=btn: b.configure(style='Ctrl.Hovered.TButton'))
            btn.bind('<Leave>', lambda e, b=btn: b.configure(style='Ctrl.TButton'))
        ttk.Separator(self.control_frame, orient='vertical').pack(side='left', padx=8, fill='y')
      
        proc_frame = ttk.Frame(self.control_frame)
        proc_frame.pack(side="left", padx=(0, 10))
        ttk.Label(proc_frame, text="⚙️ Process Control:", font=("Segoe UI", 10, "bold")).pack(side="left", padx=5)
        close_cam_btn = ttk.Button(proc_frame, text="❌ Close Camera", command=lambda: self.close_process_by_name("Camera"), style="Ctrl.TButton")
        close_cam_btn.pack(side="left", padx=2)
        close_mus_btn = ttk.Button(proc_frame, text="❌ Close Music", command=lambda: self.close_process_by_name("Music"), style="Ctrl.TButton")
        close_mus_btn.pack(side="left", padx=2)
        close_all_btn = ttk.Button(proc_frame, text="🗑️ Close All", command=self.close_all_processes, style="Ctrl.TButton")
        close_all_btn.pack(side="left", padx=2)
        for btn in [close_cam_btn, close_mus_btn, close_all_btn]:
            btn.bind('<Enter>', lambda e, b=btn: b.configure(style='Ctrl.Hovered.TButton'))
            btn.bind('<Leave>', lambda e, b=btn: b.configure(style='Ctrl.TButton'))
        ttk.Separator(self.control_frame, orient='vertical').pack(side='left', padx=8, fill='y')
  
        task_frame = ttk.Frame(self.control_frame)
        task_frame.pack(side="left", padx=(0, 10))
        ttk.Label(task_frame, text="🔄 Tasks:", font=("Segoe UI", 10, "bold")).pack(side="left", padx=5)
        start_bg_btn = ttk.Button(task_frame, text="▶️ Start Background Tasks", command=self.start_background_tasks, style="Ctrl.TButton")
        start_bg_btn.pack(side="left", padx=2)
        start_photo_btn = ttk.Button(task_frame, text="📸 Start Photo Simulation", command=self.start_photo_simulation, style="Ctrl.TButton")
        start_photo_btn.pack(side="left", padx=2)
        stop_btn = ttk.Button(task_frame, text="⏹️ Stop Tasks", command=self.stop_background_tasks, style="Ctrl.TButton")
        stop_btn.pack(side="left", padx=2)
        for btn in [start_bg_btn, start_photo_btn, stop_btn]:
            btn.bind('<Enter>', lambda e, b=btn: b.configure(style='Ctrl.Hovered.TButton'))
            btn.bind('<Leave>', lambda e, b=btn: b.configure(style='Ctrl.TButton'))
        ttk.Separator(self.control_frame, orient='vertical').pack(side='left', padx=8, fill='y')
    
        exit_btn = ttk.Button(
            self.control_frame, 
            text="❌",
            command=self.quit,
            style="Exit.TButton"
        )
        
  
        style = ttk.Style()
        style.configure('Exit.TButton', 
                     font=('Segoe UI', 12, 'bold'),
                     foreground='#d32f2f',
                     padding=2,
                     width=3)
        
        style.map('Exit.TButton',
                foreground=[('active', '#ff1744'), ('!active', '#d32f2f')],
                background=[('active', '#ffebee'), ('!active', 'white')])
        

        exit_btn.place(relx=0.99, rely=0.5, anchor='e', width=30, height=30)

    def get_next_photo_number(self):
        existing_photos = []
        for fname in os.listdir("."):  
            match = re.match(r"photo(\d+)\.jpg", fname)
            if match:
                existing_photos.append(int(match.group(1)))
        if existing_photos:
            return max(existing_photos) + 1
        else:
            return 1

    def launch_camera(self):
        queues = self.scheduler.list_queues()
        for queue in queues.values():
            for pcb in queue:
                if pcb.app_name == "Camera":
                    print("Camera is already running.")
                    self.log_message("Camera is already running.")
                    return
        app = self.process_manager.create_process("Camera", priority=1)
        self.memory.allocate(app.pid, 5)
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Cannot open camera")
            self.log_message("Error: Cannot open camera")
            return
        self.photo_counter = 1
        self.camera_running = True 
        print("Camera is open. Press SPACE to take a photo.")
        self.log_message("Camera is open. Press SPACE to take a photo.")
        def update_frame():
            if not self.camera_running:
                return
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Can't receive frame. Exiting...")
                self.log_message("Error: Can't receive frame. Exiting...")
                self.cap.release()
                self.camera_label.config(image='')
                return
            frame = cv2.resize(frame, (200, 150))
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.camera_label.imgtk = imgtk  
            self.camera_label.config(image=imgtk)
            self.camera_label.after(30, update_frame) 
        update_frame()
        def on_key(event):
            if event.keysym == "space":
                ret, frame = self.cap.read()
                if ret:
                    photo_num = self.get_next_photo_number()
                    filename = f"photo{photo_num}.jpg"
                    cv2.imwrite(filename, frame)
                    print(f"Photo saved as {filename}")
                    self.log_message(f"Photo saved as {filename}")
                    self.fs.create_file(filename)
                    is_success, buffer = cv2.imencode(".jpg", frame)
                    if is_success:
                        self.fs.write_file(filename, buffer.tobytes())
                    self.memory.allocate_file(app.pid, 5)
                    self.photo_counter += 1
        self.camera_label.winfo_toplevel().bind("<Key>", on_key)
        self.refresh()

    def close_camera(self):
        self.camera_running = False
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        self.camera_label.config(image='')
        self.camera_label.winfo_toplevel().unbind("<Key>")  
        print("Camera closed.")
        self.log_message("Camera closed.")

    def launch_music(self):
        queues = self.scheduler.list_queues()
        for queue in queues.values():
            for pcb in queue:
                if pcb.app_name == "Music":
                    print("Music is already running.")
                    self.log_message("Music is already running.")
                    return
        app = self.process_manager.create_process("Music", priority=0)
        self.memory.allocate(app.pid, 3)
        with open("mp3_base64.txt", "r") as file:
            mp3_base64 = file.read()
        mp3_bytes = base64.b64decode(mp3_base64)
        self.fs.create_file("song.mp3")
        self.fs.write_file("song.mp3", mp3_bytes)
        with open("song.mp3", "wb") as f:
            f.write(mp3_bytes)
        self.memory.allocate_file(app.pid, 3)
        pygame.mixer.init()
        try:
            pygame.mixer.music.load("song.mp3")  
            pygame.mixer.music.play(-1)  
            print("Music started playing.")
            self.log_message("Music started playing.")
        except Exception as e:
            print(f"Failed to play music: {e}")
            self.log_message(f"Failed to play music: {e}")
        self.refresh()

    def close_music(self):
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
                print("Music stopped.")
                self.log_message("Music stopped.")
        except pygame.error as e:
            print(f"Pygame error on stopping music: {e}")
            self.log_message(f"Pygame error on stopping music: {e}")

    def log_message(self, message):
        """Add a message to the system log"""
        self.log_text.config(state='normal')
        timestamp = self.get_current_time()
        self.log_text.insert('end', f"[{timestamp}] {message}\n")
        self.log_text.see('end')
        self.log_text.config(state='disabled')
    
    def get_current_time(self):
        """Get current time in HH:MM:SS format"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")

    def update_status_bar(self):
        """Update all status bar information"""
        bg_running = any([t.is_alive() if hasattr(t, 'is_alive') else False 
                         for t in [self.bg_camera, self.bg_music, self.bg_scheduler]])
        bg_text = "Background Tasks: Running" if bg_running else "Background Tasks: Stopped"
        self.bg_status.config(text=bg_text, 
                            foreground="green" if bg_running else "red")
        
        used = sum(1 for p in self.memory.pages if p is not None)
        total = len(self.memory.pages)
        self.mem_status.config(text=f"Memory: {used}/{total} KB")
        
        proc_count = sum(len(q) for q in self.scheduler.list_queues().values())
        self.proc_status.config(text=f"Processes: {proc_count}")
        
        self.time_status.config(text=f"System Time: {self.get_current_time()}")
    
    def refresh(self):
        self.update_process_display()
        self.update_memory_display()
        self.update_file_display()
        self.update_status_bar()
        self.after(1000, self.refresh)

    def update_process_display(self):
        self.process_text.delete("1.0", tk.END)
        queues = self.scheduler.list_queues()
        for name, q in queues.items():
            self.process_text.insert(tk.END, f"{name.capitalize()} Queue:\n")
            for pcb in q:
                self.process_text.insert(tk.END, f"  {pcb}\n")
            self.process_text.insert(tk.END, "\n")

    def update_memory_display(self):
        self.memory_canvas.delete("all")
        width = self.memory_canvas.winfo_width()
        height = self.memory_canvas.winfo_height()
        
        cell_width = max(10, width / len(self.memory.pages))
        for i, page in enumerate(self.memory.pages):
            x1 = i * cell_width
            x2 = (i + 1) * cell_width
            
            if page is None:
                color = "#f0f0f0"  # Free memory
            else:
                import hashlib
                color = f"#{hashlib.md5(str(page).encode()).hexdigest()[:6]}"
            
            self.memory_canvas.create_rectangle(x1, 10, x2, height-30, 
                                              fill=color, outline="#ccc")
            if page is not None:
                self.memory_canvas.create_text(x1 + cell_width/2, height-15, 
                                             text=str(page), font=("Arial", 7))
        
        used = sum(1 for p in self.memory.pages if p is not None)
        total = len(self.memory.pages)
        self.mem_stats.config(
            text=f"Total: {total} KB | Used: {used} KB | Free: {total - used} KB | "
                 f"Usage: {used/total*100:.1f}%" if total > 0 else "0%")

    def update_file_display(self):
        search_term = self.fs_search_var.get().lower()

        selected = self.fs_tree.selection()
        selected_text = None
        if selected:
            selected_text = self.fs_tree.item(selected[0], "text")

        self.fs_tree.delete(*self.fs_tree.get_children())
        
        for file in self.fs.current_directory.files.values():
            if not search_term or search_term in file.name.lower():
                prefix = "🔒 " if self.fs.is_encrypted(file.name) else "📄 "
                self.fs_tree.insert('', 'end', text=prefix + file.name)
        
        for folder in self.fs.current_directory.subdirectories.values():
            if not search_term or search_term in folder.name.lower():
                self.fs_tree.insert('', 'end', text="📁 " + folder.name)

        if selected_text:
            for item in self.fs_tree.get_children():
                if self.fs_tree.item(item, "text") == selected_text:
                    self.fs_tree.selection_set(item)
                    self.fs_tree.see(item)
                    break


    def create_folder_popup(self):
        popup = tk.Toplevel(self)
        popup.title('Yeni Klasör Oluştur')
        tk.Label(popup, text='Klasör adı:').pack(padx=8, pady=4)
        entry = tk.Entry(popup)
        entry.pack(padx=8, pady=4)
        error_label = tk.Label(popup, text='', fg='red')
        error_label.pack()
        def create():
            foldername = entry.get().strip()
            if not foldername:
                error_label.config(text='Klasör adı boş olamaz!')
                return
            try:
                self.fs.mkdir(foldername)
                self.update_file_display()
                popup.destroy()
            except Exception as e:
                error_label.config(text=f'Hata: {e}')
        ttk.Button(popup, text='Oluştur', command=create).pack(pady=6)
        entry.focus()

    def _add_tooltip(self, widget, text):
        tooltip = tk.Toplevel(widget)
        tooltip.withdraw()
        tooltip.overrideredirect(True)
        label = tk.Label(tooltip, text=text, background="#ffffe0", relief="solid", borderwidth=1, font=("Segoe UI", 9))
        label.pack()
        def enter(event):
            x = widget.winfo_rootx() + 40
            y = widget.winfo_rooty() + 20
            tooltip.geometry(f'+{x}+{y}')
            tooltip.deiconify()
        def leave(event):
            tooltip.withdraw()
        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)

    def _panel_flash(self, widget):
        orig = widget.cget('background') if 'background' in widget.keys() else '#fff'
        try:
            widget.configure(background='#b3e5fc')
            widget.after(120, lambda: widget.configure(background=orig))
        except Exception:
            pass

    def on_fs_select(self, event=None):
        selected = self.fs_tree.selection()
        if not selected:
            self.fs_detail.config(state='normal')
            self.fs_detail.delete('1.0', tk.END)
            self.fs_detail.config(state='disabled')
            return

        item = selected[0]
        item_text = self.fs_tree.item(item, 'text')

        self.fs_detail.config(state='normal')
        self.fs_detail.delete('1.0', tk.END)

        if item_text.startswith('📄 '):
            filename = item_text[2:].strip()
            info = self.fs.file_info(filename)
            if isinstance(info, dict):
                self.fs_detail.insert(tk.END,
                    f"Name: {info['name']}\nSize: {info['size']} bytes\nCreated: {info['created_at']}\n\n"
                )
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    self.close_process_by_name("Camera")
                    data = self.fs.read_file(filename)
                    image = Image.open(io.BytesIO(data))
                    image = image.resize((200, 150), Image.LANCZOS)
                    imgtk = ImageTk.PhotoImage(image)
                    self.camera_label.imgtk = imgtk
                    self.camera_label.config(image=imgtk)
            else:
                content = self.fs.read_file(filename)
                if isinstance(content, bytes):
                    content = content.decode('utf-8', errors='ignore')
                self.fs_detail.insert(tk.END, content)

        elif item_text.startswith('📁 '):
            foldername = item_text[2:].strip()
            info = self.fs.dir_info(foldername)
            if isinstance(info, dict):
                self.fs_detail.insert(tk.END,
                    f"Folder: {info['name']}\nCreated: {info['created_at']}\n"
                    f"Subfolders: {info['folders']}\nFiles: {info['files']}\n"
                )
            else:
                self.fs_detail.insert(tk.END, "Folder info not found.")

        self.fs_detail.config(state='disabled')

    def on_tree_double_click(self, event=None):
        selected = self.fs_tree.selection()
        if not selected:
            return

        item = selected[0]
        item_text = self.fs_tree.item(item, 'text')

        if item_text.startswith("📁 "):
            foldername = item_text[2:].strip()
            self.fs.cd(foldername)
            self.update_file_display()
        elif item_text.startswith("📄 ") or item_text.startswith("🔒 "):
            filename = item_text[2:].strip()

            def open_viewer_with_content(content, encrypted):
                popup = tk.Toplevel(self)
                popup.title(f"{filename} - File Viewer")

                text_widget = tk.Text(popup, width=60, height=20, state="normal")
                text_widget.insert(tk.END, content)
                text_widget.config(state="disabled")
                text_widget.pack(padx=10, pady=10)

                encrypt_var = tk.BooleanVar(value=encrypted)

                def toggle_encrypt():
                    encrypt_var.set(not encrypt_var.get())
                    btn_encrypt.config(text="Encrypt" if not encrypt_var.get() else "Decrypt")

                def enable_edit_mode():
                    text_widget.config(state="normal")
                    btn_save.config(state="normal")
                    btn_encrypt.config(state="normal")

                def save():
                    new_content = text_widget.get("1.0", tk.END).rstrip()
                    if encrypt_var.get():
                        pwd_popup = tk.Toplevel(popup)
                        pwd_popup.title("Enter password to encrypt")

                        tk.Label(pwd_popup, text="Password:").pack(padx=10, pady=5)
                        pwd_entry = tk.Entry(pwd_popup, show="*")
                        pwd_entry.pack(padx=10, pady=5)
                        pwd_entry.focus()

                        def confirm_pwd():
                            pwd = pwd_entry.get()
                            if pwd:
                                self.fs.write_file(filename, new_content, password=pwd)
                                self.log_message(f"{filename} saved and encrypted successfully.")
                                pwd_popup.destroy()
                                popup.destroy()
                                self.update_file_display()
                            else:
                                messagebox.showerror("Error", "Password cannot be empty!")

                        tk.Button(pwd_popup, text="OK", command=confirm_pwd).pack(pady=5)
                    else:
                        self.fs.write_file(filename, new_content)
                        self.log_message(f"{filename} saved without encryption.")
                        popup.destroy()
                        self.update_file_display()

                button_frame = ttk.Frame(popup)
                button_frame.pack(pady=(0, 10))

                btn_edit = ttk.Button(button_frame, text="Edit", command=enable_edit_mode)
                btn_edit.pack(side="left", padx=5)

                btn_save = ttk.Button(button_frame, text="Save", command=save, state="disabled")
                btn_save.pack(side="left", padx=5)

                btn_encrypt = ttk.Checkbutton(button_frame, text="Encrypt", variable=encrypt_var)
                btn_encrypt.pack(side="left", padx=5)
                btn_encrypt.config(state="disabled")

            if self.fs.is_encrypted(filename):
                pwd_popup = tk.Toplevel(self)
                pwd_popup.title(f"Enter password for {filename}")

                tk.Label(pwd_popup, text="Password:").pack(padx=10, pady=5)
                pwd_entry = tk.Entry(pwd_popup, show="*")
                pwd_entry.pack(padx=10, pady=5)
                pwd_entry.focus()

                def check_password():
                    pwd = pwd_entry.get()
                    if self.fs.check_password(filename, pwd):
                        pwd_popup.destroy()
                        content = self.fs.read_file(filename, password=pwd)
                        if isinstance(content, bytes):
                            content = content.decode('utf-8', errors='ignore')
                        open_viewer_with_content(content, encrypted=True)
                    else:
                        messagebox.showerror("Error", "Incorrect password!")

                tk.Button(pwd_popup, text="Submit", command=check_password).pack(pady=10)
            else:
                content = self.fs.read_file(filename)
                if isinstance(content, bytes):
                    content = content.decode('utf-8', errors='ignore')
                open_viewer_with_content(content, encrypted=False)

    def create_file_popup(self):
        popup = tk.Toplevel(self)
        popup.title('Create New File')
        tk.Label(popup, text='File name:').pack(padx=8, pady=4)
        entry = tk.Entry(popup)
        entry.pack(padx=8, pady=4)

        def create():
            filename = entry.get().strip()
            if filename:
                self.fs.create_file(filename)
                self._panel_flash(self.fs_tree)
                self.update_file_display()
            popup.destroy()

        ttk.Button(popup, text='Create', command=create).pack(pady=6)
        entry.focus()

    def delete_selected_file(self):
        selected = self.fs_tree.selection()
        if not selected:
            return

        item = selected[0]
        item_text = self.fs_tree.item(item, 'text')

        try:
            if item_text.startswith('📄 '):
                filename = item_text[2:].strip()
                self.fs.delete_file(filename)
                self.log_message(f"File deleted: {filename}")
            elif item_text.startswith('📁 '):
                foldername = item_text[2:].strip()
                self.fs.delete_directory(foldername)
                self.log_message(f"Folder deleted: {foldername}")
            else:
                self.log_message("Unknown item type.")
        except Exception as e:
            self.log_message(f"Delete failed: {e}")
        finally:
            self._panel_flash(self.fs_tree)
            self.update_file_display()

    def show_block_storage(self):
        window = tk.Toplevel(self)
        window.title("Block Storage")
        window.geometry("500x400")

        text_widget = tk.Text(window, wrap="word")
        text_widget.pack(fill="both", expand=True)

        for i, (block_id, block) in enumerate(self.fs.storage.blocks.items()):
            try:
                display_block = block.decode('utf-8')
            except UnicodeDecodeError:
                display_block = str(block)
            text_widget.insert("end", f"Block {i} (ID: {block_id}):\n{display_block}\n\n")




    def close_process_by_name(self, app_name):
        if app_name == "Camera" and not getattr(self, 'camera_running', False):
            return
        queues = self.scheduler.list_queues()
        found = False
        for queue in queues.values():
            for pcb in queue:
                if pcb.app_name == app_name:
                    self.process_manager.terminate_process(pcb.pid)
                    self.memory.deallocate(pcb.pid)
                    file_id = hash(pcb.app_name)
                    self.memory.deallocate_file(file_id)
                    found = True
                    break
            if found:
                break
        if found:
            if app_name == "Camera":
                self.close_camera()
            elif app_name == "Music":
                self.close_music()
            self.refresh()
        else:
            print(f"No running process found with name '{app_name}'")
            self.log_message(f"No running process found with name '{app_name}'")

    def close_all_processes(self):
        queues = self.scheduler.list_queues()
        app_names = set()
        for queue in queues.values():
            for pcb in queue:
                app_names.add(pcb.app_name)
        if not app_names:
            print("No running processes to close.")
            self.log_message("No running processes to close.")
            return
        for app_name in app_names:
            self.close_process_by_name(app_name)
        print("All processes closed.")
        self.log_message("All processes closed.")

    def start_background_tasks(self):
        self.log_message("Starting background tasks...")
        try:
            if not hasattr(self.bg_camera, 'is_alive') or not self.bg_camera.is_alive():
                self.bg_camera = CameraTask(self.fs, log_fn=self.log_message)
                self.bg_camera.start()
                self.log_message("Camera task started")
            if not hasattr(self.bg_music, 'is_alive') or not self.bg_music.is_alive():
                self.bg_music = MusicTask(self.memory, pid=99)
                self.bg_music.start()
                self.log_message("Music task started")
            if not hasattr(self.bg_scheduler, 'is_alive') or not self.bg_scheduler.is_alive():
                self.bg_scheduler = SchedulerTask(self.scheduler)
                self.bg_scheduler.start()
                self.log_message("Scheduler task started")
            if not hasattr(self.bg_consumer, 'is_alive') or not self.bg_consumer.is_alive():
                self.bg_consumer = PhotoConsumer(log_fn=self.log_message, update_fn=self.increment_processed_count)
                self.bg_consumer.start()
                self.log_message("PhotoConsumer task started")

        except Exception as e:
            self.log_message(f"Error starting background tasks: {str(e)}")

    def start_photo_simulation(self):
        self.log_message("Starting photo simulation...")

        try:
            if not hasattr(self.bg_camera, 'is_alive') or not self.bg_camera.is_alive():
                self.bg_camera = CameraTask(self.fs, log_fn=self.log_message)
                self.bg_camera.start()
                self.log_message("Camera task started (simulation)")

            if not hasattr(self.bg_consumer, 'is_alive') or not self.bg_consumer.is_alive():
                self.bg_consumer = PhotoConsumer(log_fn=self.log_message, update_fn=self.increment_processed_count)
                self.bg_consumer.start()
                self.log_message("PhotoConsumer task started (simulation)")

        except Exception as e:
            self.log_message(f"Error in photo simulation start: {str(e)}")


    def stop_background_tasks(self):
        self.log_message("Stopping background tasks...")
        try:
            self.bg_camera.stop()
            self.bg_music.stop()
            self.bg_scheduler.stop()
            self.bg_consumer.stop()
            self.log_message("All background tasks stopped")
        except Exception as e:
            self.log_message(f"Error stopping background tasks: {str(e)}")

if __name__ == "__main__":
    app = OSVisualizer()
    app.mainloop()


