"""
🎯 Modern Text Editor - Object-Oriented Version
📝 A feature-rich text editor with voice recognition, text-to-speech,
   and intelligent text direction detection
"""

import os
import re
import time
from threading import Thread
from datetime import datetime
from tkinter import filedialog, messagebox, colorchooser, Menu

import customtkinter as ctk
import docx
import pygame
import speech_recognition as sr
from gtts import gTTS
from PIL import Image


class VoiceManager:
    """🎤 Handles all voice-related functionality"""
    
    def __init__(self):
        self.is_recording = False
        self.is_reading = False
        self.audio_file = "speech.mp3"
        pygame.mixer.init()
    
    def toggle_recording(self, callback):
        """Toggle voice recording state"""
        if not self.is_recording:
            self.is_recording = True
            Thread(target=self._continuous_listen, args=(callback,), daemon=True).start()
            return "⏹️ Recording...", True
        else:
            self.is_recording = False
            return "🎤 Recorder", False
    
    def _continuous_listen(self, callback):
        """Background thread for continuous voice recognition"""
        recognizer = sr.Recognizer()
        while self.is_recording:
            try:
                with sr.Microphone() as mic:
                    recognizer.adjust_for_ambient_noise(mic, duration=0.3)
                    audio = recognizer.listen(mic, phrase_time_limit=5, timeout=3)
                    speech = recognizer.recognize_google(audio)
                    
                    if speech:
                        callback(speech + " ")
            except:
                continue
    
    def toggle_reading(self, content, update_button_callback):
        """Toggle text-to-speech reading"""
        if self.is_reading:
            self._stop_reading()
            update_button_callback("🔊 Read", False)
            return "🔊 Read", False
        
        if not content:
            messagebox.showinfo("Info", "No text to read")
            update_button_callback("🔊 Read", False)
            return "🔊 Read", False
        
        self.is_reading = True
        update_button_callback("⏸️ Stop", True)
        Thread(target=self._read_text, args=(content, update_button_callback), daemon=True).start()
        return "⏸️ Stop", True
    
    def _read_text(self, content, update_button_callback):
        """Background thread for text-to-speech"""
        try:
            # Generate audio
            tts = gTTS(text=content[:10000], lang='en', slow=False)
            tts.save(self.audio_file)
            
            # Play audio
            pygame.mixer.music.load(self.audio_file)
            pygame.mixer.music.play()
            
            # Monitor playback
            while pygame.mixer.music.get_busy() and self.is_reading:
                time.sleep(0.1)
            
            # Cleanup
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            
            # Delete audio file
            if os.path.exists(self.audio_file):
                try:
                    os.remove(self.audio_file)
                except:
                    pass
            
            self.is_reading = False
            update_button_callback("🔊 Read", False)
            
        except Exception as e:
            print(f"TTS Error: {e}")
            self.is_reading = False
            update_button_callback("🔊 Read", False)
    
    def _stop_reading(self):
        """Stop current reading"""
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        self.is_reading = False


class SearchManager:
    """🔍 Handles search and replace functionality"""
    
    def __init__(self):
        self.search_term = ""
        self.search_positions = []
        self.current_search_index = -1
    
    def find_all(self, text_widget, search_term):
        """Find all occurrences of search term"""
        self.search_term = search_term
        self.search_positions = []
        
        if not search_term:
            return []
        
        # Clear previous highlights
        text_widget.tag_remove("highlight", "1.0", "end")
        
        # Find all occurrences
        content = text_widget.get("1.0", "end")
        for match in re.finditer(re.escape(search_term), content, re.IGNORECASE):
            start_pos = f"1.0+{match.start()}c"
            end_pos = f"1.0+{match.end()}c"
            self.search_positions.append((start_pos, end_pos))
            
            # Highlight occurrence
            text_widget.tag_add("highlight", start_pos, end_pos)
        
        text_widget.tag_config("highlight", background="yellow", foreground="black")
        return self.search_positions
    
    def find_next(self, text_widget):
        """Find and highlight next occurrence"""
        if not self.search_positions:
            return None
        
        if self.current_search_index >= len(self.search_positions):
            self.current_search_index = 0
        
        start_pos, end_pos = self.search_positions[self.current_search_index]
        
        # Scroll to and select text
        text_widget.tag_remove("sel", "1.0", "end")
        text_widget.tag_add("sel", start_pos, end_pos)
        text_widget.see(start_pos)
        
        # Highlight current match
        text_widget.tag_remove("current", "1.0", "end")
        text_widget.tag_add("current", start_pos, end_pos)
        text_widget.tag_config("current", background="orange", foreground="black")
        
        self.current_search_index = (self.current_search_index + 1) % len(self.search_positions)
        return start_pos, end_pos
    
    def find_previous(self, text_widget):
        """Find and highlight previous occurrence"""
        if not self.search_positions:
            return None
        
        self.current_search_index = (self.current_search_index - 2) % len(self.search_positions)
        return self.find_next(text_widget)


class FileManager:
    """📁 Handles file operations"""
    
    @staticmethod
    def save(content):
        """Save content to file"""
        file = filedialog.asksaveasfile(
            filetypes=[("Text files", "*.txt"), ("HTML files", "*.html"),
                       ("Word files", "*.docx"), ("All files", "*.*")]
        )
        if file:
            file.write(content)
            file.close()
            return True
        return False
    
    @staticmethod
    def open_file():
        """Open file and return content"""
        filepath = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("HTML files", "*.html"),
                       ("Word files", "*.docx")]
        )
        if not filepath:
            return None
        
        try:
            if filepath.endswith(".docx"):
                doc = docx.Document(filepath)
                return "\n".join(para.text for para in doc.paragraphs)
            else:
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open file: {e}")
            return None


class ThemeManager:
    """🎨 Handles theme and appearance"""
    
    def __init__(self):
        self.current_mode = "dark"
        ctk.set_appearance_mode(self.current_mode)
        ctk.set_default_color_theme("blue")
    
    def toggle(self):
        """Toggle between dark and light mode"""
        self.current_mode = "light" if self.current_mode == "dark" else "dark"
        ctk.set_appearance_mode(self.current_mode)
        return "☀️ Light" if self.current_mode == "dark" else "🌙 Dark"
    
    def change_background(self, text_widget, color):
        """Change text widget background color"""
        if color:
            text_widget.configure(fg_color=color)
            
            # Calculate brightness for text color
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            
            text_widget.configure(text_color="white" if brightness < 128 else "black")


class TextDirectionManager:
    """↔️ Handles text direction detection"""
    
    @staticmethod
    def check_line_direction(text_widget, event=None):
        """Check and apply direction for current line"""
        current_line = text_widget.index("insert").split('.')[0]
        start = f"{current_line}.0"
        end = f"{current_line}.end"
        current_text = text_widget.get(start, end)
        
        is_arabic = any("\u0600" <= char <= "\u06ff" for char in current_text)
        
        if is_arabic:
            text_widget.tag_add("rtl", start, end)
            text_widget.tag_remove("ltr", start, end)
        else:
            text_widget.tag_add("ltr", start, end)
            text_widget.tag_remove("rtl", start, end)
    
    @staticmethod
    def apply_direction_to_all(text_widget):
        """Apply direction to entire document"""
        content = text_widget.get("1.0", "end").split("\n")
        for i, line in enumerate(content):
            is_arabic = any("\u0600" <= char <= "\u06ff" for char in line)
            start, end = f"{i+1}.0", f"{i+1}.end"
            
            if is_arabic:
                text_widget.tag_add("rtl", start, end)
                text_widget.tag_remove("ltr", start, end)
            else:
                text_widget.tag_add("ltr", start, end)
                text_widget.tag_remove("rtl", start, end)


class ModernTextEditor(ctk.CTk):
    """📝 Main Text Editor Application"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize managers
        self.voice_manager = VoiceManager()
        self.search_manager = SearchManager()
        self.file_manager = FileManager()
        self.theme_manager = ThemeManager()
        self.text_direction_manager = TextDirectionManager()
        
        # UI state
        self.font_size = ctk.StringVar(value="24")
        self.global_content = ""
        self.default_button_color = ("#3a7ebf", "#1f538d")  # Default light/dark blue colors
        
        # Setup window
        self._setup_window()
        self._create_widgets()
        self._setup_menus()
        self._setup_keyboard_shortcuts()
    
    def _setup_window(self):
        """Configure main window"""
        self.title("✨ Modern Text Editor - OOP Edition")
        self.geometry("1200x800")
    
    def _create_widgets(self):
        """Create all UI widgets"""
        # Toolbar
        self._create_toolbar()
        
        # Text area
        self._create_text_area()
        
        # Status bar
        self._create_status_bar()
    
    def _create_toolbar(self):
        """Create toolbar with buttons"""
        self.toolbar = ctk.CTkFrame(self, height=60)
        self.toolbar.pack(fill="x", padx=10, pady=(10, 5))
        
        # Theme button
        self.theme_button = ctk.CTkButton(
            self.toolbar, text="☀️ Light", width=100,
            command=self._toggle_theme
        )
        self.theme_button.pack(side="left", padx=5)
        
        # Color button
        self.color_button = ctk.CTkButton(
            self.toolbar, text="🎨 Color", width=50,
            command=self._change_background
        )
        self.color_button.pack(side="left", padx=5)
        
        # Search button
        self.search_button = ctk.CTkButton(
            self.toolbar, text="🔍 Search", width=120,
            command=self._open_search_dialog
        )
        self.search_button.pack(side="left", padx=5)
        
        # Spacer
        ctk.CTkLabel(self.toolbar, text="").pack(side="left", expand=True)
        
        # Voice buttons
        self.record_button = ctk.CTkButton(
            self.toolbar, text="🎤 Recorder", width=120,
            command=self._toggle_recording
        )
        self.record_button.pack(side="right", padx=5)
        
        self.read_button = ctk.CTkButton(
            self.toolbar, text="🔊 Read", width=120,
            command=self._toggle_reading
        )
        self.read_button.pack(side="right", padx=5)
    
    def _create_text_area(self):
        """Create main text editing area"""
        text_frame = ctk.CTkFrame(self)
        text_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.text = ctk.CTkTextbox(
            text_frame, wrap="word", 
            font=("Courier", int(self.font_size.get()), "bold")
        )
        self.text.pack(fill="both", expand=True)
        
        # Configure text tags
        self.text.tag_config("rtl", justify="right")
        self.text.tag_config("ltr", justify="left")
        self.text.configure(undo=True, maxundo=100)
        
        # Bind events
        self.text.bind("<KeyRelease>", self._on_text_change)
    
    def _create_status_bar(self):
        """Create status bar at bottom"""
        self.status_bar = ctk.CTkFrame(self, height=30)
        self.status_bar.pack(fill="x", padx=10, pady=(0, 10))
        
        # Font size
        ctk.CTkLabel(self.status_bar, text="Font Size:").pack(side="left", padx=(10, 5))
        ctk.CTkLabel(self.status_bar, textvariable=self.font_size, width=40).pack(side="left", padx=5)
        
        # Cursor position
        self.position_label = ctk.CTkLabel(self.status_bar, text="Ln 1, Col 1")
        self.position_label.pack(side="right", padx=10)
        
        # Bind position update
        self.text.bind("<KeyRelease>", self._update_cursor_position)
        self.text.bind("<ButtonRelease>", self._update_cursor_position)
    
    def _setup_menus(self):
        """Setup application menus"""
        menubar = Menu(self)
        self.configure(menu=menubar)
        
        # File menu
        self._create_file_menu(menubar)
        
        # Edit menu
        self._create_edit_menu(menubar)
        
        # View menu
        self._create_view_menu(menubar)
    
    def _create_file_menu(self, menubar):
        """Create File menu"""
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="📁 File", menu=file_menu)
        
        file_commands = [
            ("📄 New", self._new_file, "Ctrl+N"),
            ("📂 Open", self._open_file, "Ctrl+O"),
            ("💾 Save", self._save_file, "Ctrl+S"),
            ("💾 Save As", self._save_as_file, "Ctrl+Shift+S"),
            None,  # Separator
            ("🚪 Exit", self.destroy, "Alt+F4")
        ]
        
        for cmd in file_commands:
            if cmd is None:
                file_menu.add_separator()
            else:
                label, func, accel = cmd
                file_menu.add_command(label=label, command=func, accelerator=accel)
    
    def _create_edit_menu(self, menubar):
        """Create Edit menu"""
        edit_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="✏️ Edit", menu=edit_menu)
        
        edit_commands = [
            ("↩️ Undo", self._undo, "Ctrl+Z"),
            ("↪️ Redo", self._redo, "Ctrl+Y"),
            None,
            ("✂️ Cut", self._cut, "Ctrl+X"),
            ("📋 Copy", self._copy, "Ctrl+C"),
            ("📝 Paste", self._paste, "Ctrl+V"),
            ("🗑️ Delete", self._delete, "Del"),
            None,
            ("🔍 Find", self._open_search_dialog, "Ctrl+F"),
            ("⏭️ Find Next", self._find_next, "F3"),
            ("⏮️ Find Previous", self._find_previous, "Shift+F3"),
            ("🔄 Replace", self._replace, "Ctrl+H"),
            ("📍 Go To", self._go_to_line, "Ctrl+G"),
            None,
            ("📑 Select All", self._select_all, "Ctrl+A"),
            ("🕐 Time/Date", self._insert_time_date, "F5")
        ]
        
        for cmd in edit_commands:
            if cmd is None:
                edit_menu.add_separator()
            else:
                label, func, accel = cmd
                edit_menu.add_command(label=label, command=func, accelerator=accel)
    
    def _create_view_menu(self, menubar):
        """Create View menu"""
        view_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="👁️ View", menu=view_menu)
        
        view_commands = [
            ("🔍 Zoom In", self._zoom_in, "Ctrl++"),
            ("🔍 Zoom Out", self._zoom_out, "Ctrl+-"),
            ("🔁 Reset Zoom", self._reset_zoom),
            None,
            ("📊 Status Bar", lambda: None),
            ("📝 Word Wrap", lambda: None)
        ]
        
        for cmd in view_commands:
            if cmd is None:
                view_menu.add_separator()
            else:
                label, func, accel = cmd if len(cmd) == 3 else (cmd[0], cmd[1], "")
                view_menu.add_command(label=label, command=func, accelerator=accel)
    
    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts"""
        shortcuts = {
            "<Control-n>": self._new_file,
            "<Control-o>": self._open_file,
            "<Control-s>": self._save_file,
            "<Control-Shift-S>": self._save_as_file,
            "<Control-z>": self._undo,
            "<Control-y>": self._redo,
            "<Control-f>": self._open_search_dialog,
            "<F3>": self._find_next,
            "<Shift-F3>": self._find_previous,
            "<Control-x>": self._cut,
            "<Control-c>": self._copy,
            "<Control-v>": self._paste,
            "<Control-a>": self._select_all,
            "<Control-plus>": self._zoom_in,
            "<Control-minus>": self._zoom_out,
            "<F5>": self._insert_time_date
        }
        
        for shortcut, command in shortcuts.items():
            self.bind(shortcut, lambda e, cmd=command: cmd())
    
    # ========== EVENT HANDLERS ==========
    
    def _on_text_change(self, event=None):
        """Handle text changes"""
        self.text_direction_manager.check_line_direction(self.text, event)
        self._update_cursor_position()
    
    def _update_cursor_position(self, event=None):
        """Update cursor position in status bar"""
        try:
            cursor_pos = self.text.index("insert")
            line, col = cursor_pos.split('.')
            self.position_label.configure(text=f"Ln {line}, Col {int(col)+1}")
        except:
            pass
    
    def _toggle_theme(self):
        """Toggle between dark and light theme"""
        new_text = self.theme_manager.toggle()
        self.theme_button.configure(text=new_text)
    
    def _change_background(self):
        """Change background color"""
        chosen_color = colorchooser.askcolor()[1]
        if chosen_color:
            self.theme_manager.change_background(self.text, chosen_color)
    
    def _toggle_recording(self):
        """Toggle voice recording"""
        new_text, is_recording = self.voice_manager.toggle_recording(self._insert_text)
        
        self.record_button.configure(
            text=new_text,
            fg_color="red" if is_recording else self.default_button_color
        )
    
    def _insert_text(self, text):
        """Insert text from voice recognition"""
        self.text.insert("end", text)
        self.text_direction_manager.apply_direction_to_all(self.text)
    
    def _toggle_reading(self):
        """Toggle text-to-speech reading"""
        content = self.text.get("1.0", "end").strip()
        new_text, is_reading = self.voice_manager.toggle_reading(
            content, self._update_read_button
        )
        
        self.read_button.configure(
            text=new_text,
            fg_color="red" if is_reading else self.default_button_color
        )
    
    def _update_read_button(self, text, is_reading):
        """Update read button state"""
        self.read_button.configure(
            text=text,
            fg_color="red" if is_reading else self.default_button_color
        )
    
    # ========== FILE OPERATIONS ==========
    
    def _new_file(self):
        """Create new file"""
        if self.text.get("1.0", "end-1c").strip():
            answer = messagebox.askyesnocancel("New File", "Save current file?")
            if answer is True:
                self._save_file()
            elif answer is None:
                return
        
        self.text.delete("1.0", "end")
        self.text_direction_manager.apply_direction_to_all(self.text)
    
    def _open_file(self):
        """Open file"""
        content = self.file_manager.open_file()
        if content:
            self.text.delete("1.0", "end")
            self.text.insert("1.0", content)
            self.global_content = content
            self.text_direction_manager.apply_direction_to_all(self.text)
    
    def _save_file(self):
        """Save current file"""
        content = self.text.get("1.0", "end")
        self.file_manager.save(content)
    
    def _save_as_file(self):
        """Save file with new name"""
        self._save_file()
    
    # ========== EDIT OPERATIONS ==========
    
    def _undo(self):
        """Undo last action"""
        try:
            self.text.edit_undo()
        except:
            pass
    
    def _redo(self):
        """Redo last action"""
        try:
            self.text.edit_redo()
        except:
            pass
    
    def _cut(self):
        """Cut selected text"""
        try:
            self.text.clipboard_clear()
            self.text.clipboard_append(self.text.selection_get())
            self.text.delete("sel.first", "sel.last")
        except:
            pass
    
    def _copy(self):
        """Copy selected text"""
        try:
            self.text.clipboard_clear()
            self.text.clipboard_append(self.text.selection_get())
        except:
            pass
    
    def _paste(self):
        """Paste from clipboard"""
        try:
            self.text.insert("insert", self.text.clipboard_get())
        except:
            pass
    
    def _delete(self):
        """Delete selected text"""
        self.text.delete("1.0", "end")
    
    def _select_all(self):
        """Select all text"""
        self.text.tag_add("sel", "1.0", "end")
    
    # ========== SEARCH OPERATIONS ==========
    
    def _open_search_dialog(self):
        """Open search dialog"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("🔍 Search")
        dialog.geometry("400x150")
        dialog.transient(self)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Find:").pack(pady=5)
        
        search_entry = ctk.CTkEntry(dialog, width=300)
        search_entry.pack(pady=5)
        search_entry.focus()
        
        def perform_search():
            search_term = search_entry.get()
            if search_term:
                positions = self.search_manager.find_all(self.text, search_term)
                if positions:
                    self.search_manager.find_next(self.text)
                    dialog.destroy()
                else:
                    messagebox.showinfo("Search", "Text not found")
        
        def close_search():
            self.text.tag_remove("highlight", "1.0", "end")
            dialog.destroy()
        
        btn_frame = ctk.CTkFrame(dialog)
        btn_frame.pack(pady=10)
        
        ctk.CTkButton(btn_frame, text="Find", command=perform_search).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Cancel", command=close_search).pack(side="left", padx=5)
        
        dialog.bind("<Return>", lambda e: perform_search())
        dialog.bind("<Escape>", lambda e: close_search())
    
    def _find_next(self):
        """Find next occurrence"""
        position = self.search_manager.find_next(self.text)
        if not position and not self.search_manager.search_positions:
            messagebox.showinfo("Search", "No search term entered")
    
    def _find_previous(self):
        """Find previous occurrence"""
        position = self.search_manager.find_previous(self.text)
        if not position and not self.search_manager.search_positions:
            messagebox.showinfo("Search", "No search term entered")
    
    def _replace(self):
        """Open replace dialog"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("🔄 Replace")
        dialog.geometry("400x200")
        
        ctk.CTkLabel(dialog, text="Find:").pack(pady=5)
        find_entry = ctk.CTkEntry(dialog, width=300)
        find_entry.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="Replace with:").pack(pady=5)
        replace_entry = ctk.CTkEntry(dialog, width=300)
        replace_entry.pack(pady=5)
        
        def perform_replace():
            find_text = find_entry.get()
            replace_text = replace_entry.get()
            
            if not find_text:
                return
            
            content = self.text.get("1.0", "end")
            new_content = content.replace(find_text, replace_text)
            
            self.text.delete("1.0", "end")
            self.text.insert("1.0", new_content)
            dialog.destroy()
        
        ctk.CTkButton(dialog, text="Replace All", command=perform_replace).pack(pady=10)
    
    def _go_to_line(self):
        """Go to specific line number"""
        line = ctk.CTkInputDialog(text="Enter line number:", title="📍 Go To Line").get_input()
        if line and line.isdigit():
            self.text.see(f"{line}.0")
    
    def _insert_time_date(self):
        """Insert current time and date"""
        now = datetime.now()
        self.text.insert("insert", now.strftime("%Y-%m-%d %H:%M:%S"))
    
    # ========== VIEW OPERATIONS ==========
    
    def _zoom_in(self):
        """Increase font size"""
        current_size = int(self.font_size.get())
        if current_size < 72:
            self.font_size.set(str(current_size + 2))
            self.text.configure(font=("Courier", current_size + 2, "bold"))
    
    def _zoom_out(self):
        """Decrease font size"""
        current_size = int(self.font_size.get())
        if current_size > 8:
            self.font_size.set(str(current_size - 2))
            self.text.configure(font=("Courier", current_size - 2, "bold"))
    
    def _reset_zoom(self):
        """Reset to default font size"""
        self.font_size.set("24")
        self.text.configure(font=("Courier", 24, "bold"))
    
    def run(self):
        """Start the application"""
        self.mainloop()


def main():
    """Application entry point"""
    # Ensure required packages are installed
    try:
        from PIL import Image
    except ImportError:
        print("Installing required packages...")
        import subprocess
        subprocess.run(["pip", "install", "Pillow"], capture_output=True)
    
    # Create and run the application
    app = ModernTextEditor()
    app.run()


if __name__ == "__main__":
    main()