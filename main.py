#!/usr/bin/env python3
"""
Law Maker - A Prolog Programming Game

A game where players implement laws in Prolog for the fictional city-state of Solarfurt.
Features a beautiful Solarpunk aesthetic - rusty-futuristic with sustainable tech vibes.
"""

import os
import json
import tempfile
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import threading
import sys

# Try to import PIL, fall back gracefully if not available
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Try to import janus_swi for better Prolog integration
try:
    import janus_swi as janus

    JANUS_AVAILABLE = True
except ImportError:
    JANUS_AVAILABLE = False
    print("Warning: janus_swi not available. Install with: pip install janus_swi")


class GameResult(Enum):
    SUCCESS = "success"
    SYNTAX_ERROR = "syntax_error"
    WRONG_RESULTS = "wrong_results"
    PROLOG_ERROR = "prolog_error"


@dataclass
class Query:
    """Represents a Prolog query with expected results"""
    query: str
    expected: List[str]
    description: str = ""


@dataclass
class Level:
    """Represents a game level with law implementation challenge"""
    id: str
    title: str
    description: str
    background_story: str
    given_facts: str
    law_description: str
    queries: List[Query]
    hints: List[str] = None
    difficulty: int = 1


# Updated GUI text elements with cleaner Star Trek + Solarpunk styling
GUI_TEXT = {
    'app_title': "LAW MAKER",
    'app_subtitle': "Integrated Legal Code Compiler",
    'mission_select': "Mission Selection",
    'legal_brief': "Legal Brief",
    'code_forge': "Code Editor",
    'test_results': "Test Results",
    'activate_mission': "Activate Mission",
    'refresh_database': "Refresh Database",
    'test_implementation': "Test Implementation",
    'clear_code': "Clear Code",
    'load_example': "Load Example",
    'clear_report': "Clear Report",
    'mission_header': "Select Your Legal Mission",
    'mission_desc': "Choose a law to implement in the integrated legal database:",
    'code_forge_header': "Prolog Code Editor",
    'compliance_report': "Legal Compliance Report",
    'analyzing': "Analyzing...",
    'prolog_online': "Janus Prolog Online",
    'prolog_offline': "Prolog Offline",
    'mission_accomplished': "MISSION ACCOMPLISHED",
    'system_error': "SYSTEM ERROR",
    'compliance_violations': "COMPLIANCE VIOLATIONS DETECTED"
}


class SolarpunkTheme:
    """Solarpunk theme colors and styles - rusty-futuristic aesthetic"""

    # Color palette inspired by Star Trek LCARS + natural elements
    COLORS = {
        'bg_primary': '#0A0E1A',  # Deep space blue-black
        'bg_secondary': '#1B2B35',  # Dark teal
        'bg_panel': '#2A4A5A',  # Medium blue-gray
        'bg_input': '#0F1419',  # Very dark blue
        'accent_primary': '#00D4AA',  # Bright teal (Star Trek-ish)
        'accent_secondary': '#66B2FF',  # Bright blue
        'accent_tertiary': '#FFB366',  # Warm orange
        'accent_success': '#00FF88',  # Bright green
        'text_primary': '#E8F4F8',  # Very light blue-white
        'text_secondary': '#B8D4E8',  # Light blue
        'text_accent': '#00D4AA',  # Matching accent
        'warning': '#FF6B35',  # Orange-red
        'success': '#00FF88',  # Bright green
        'border': '#4A6FA5',  # Medium blue
        'hover': '#3A5F85'  # Hover blue
    }

    @staticmethod
    def configure_style():
        """Configure ttk styles with Star Trek + Solarpunk fusion theme"""
        style = ttk.Style()

        # Main frame styles
        style.configure('Solarpunk.TFrame',
                        background=SolarpunkTheme.COLORS['bg_primary'],
                        relief='flat')

        style.configure('Panel.TFrame',
                        background=SolarpunkTheme.COLORS['bg_panel'],
                        relief='ridge',
                        borderwidth=1)

        # Label styles
        style.configure('Solarpunk.TLabel',
                        background=SolarpunkTheme.COLORS['bg_primary'],
                        foreground=SolarpunkTheme.COLORS['text_primary'],
                        font=('Helvetica', 10))

        style.configure('Title.TLabel',
                        background=SolarpunkTheme.COLORS['bg_primary'],
                        foreground=SolarpunkTheme.COLORS['accent_primary'],
                        font=('Helvetica', 18, 'bold'))

        style.configure('Header.TLabel',
                        background=SolarpunkTheme.COLORS['bg_primary'],
                        foreground=SolarpunkTheme.COLORS['text_accent'],
                        font=('Helvetica', 12, 'bold'))

        # Button styles - more Star Trek LCARS inspired
        style.configure('Solarpunk.TButton',
                        background=SolarpunkTheme.COLORS['accent_primary'],
                        foreground=SolarpunkTheme.COLORS['bg_primary'],
                        font=('Helvetica', 10, 'bold'),
                        borderwidth=0,
                        relief='flat',
                        padding=(12, 6))

        style.map('Solarpunk.TButton',
                  background=[('active', SolarpunkTheme.COLORS['accent_secondary']),
                              ('pressed', SolarpunkTheme.COLORS['accent_tertiary'])])

        # Notebook styles
        style.configure('Solarpunk.TNotebook',
                        background=SolarpunkTheme.COLORS['bg_primary'],
                        borderwidth=0)

        style.configure('Solarpunk.TNotebook.Tab',
                        background=SolarpunkTheme.COLORS['bg_secondary'],
                        foreground=SolarpunkTheme.COLORS['text_secondary'],
                        padding=[16, 8],
                        font=('Helvetica', 10, 'bold'),
                        borderwidth=1)

        style.map('Solarpunk.TNotebook.Tab',
                  background=[('selected', SolarpunkTheme.COLORS['accent_primary']),
                              ('active', SolarpunkTheme.COLORS['hover'])],
                  foreground=[('selected', SolarpunkTheme.COLORS['bg_primary'])])

        return style


class LevelLoader:
    """Loads level configurations from JSON files"""

    @staticmethod
    def load_levels_from_directory(directory: str) -> List[Level]:
        """Load all levels from a directory containing JSON files"""
        levels = []

        if not os.path.exists(directory):
            LevelLoader.create_sample_levels(directory)

        try:
            level_files = [f for f in os.listdir(directory) if f.endswith('.json')]
            level_files.sort()

            for filename in level_files:
                filepath = os.path.join(directory, filename)
                level = LevelLoader.load_level_from_file(filepath)
                if level:
                    levels.append(level)

        except Exception as e:
            print(f"Error loading levels: {e}")
            return LevelLoader.get_sample_levels()

        return levels if levels else LevelLoader.get_sample_levels()

    @staticmethod
    def load_level_from_file(filepath: str) -> Optional[Level]:
        """Load a single level from a JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Handle both nested and flat JSON structures
            if 'content' in data:
                data = data['content']

            queries = []
            for q_data in data.get('queries', []):
                query = Query(
                    query=q_data['query'],
                    expected=q_data['expected'],
                    description=q_data.get('description', '')
                )
                queries.append(query)

            level = Level(
                id=data['id'],
                title=data['title'],
                description=data['description'],
                background_story=data['background_story'],
                given_facts=data['given_facts'],
                law_description=data['law_description'],
                queries=queries,
                hints=data.get('hints', []),
                difficulty=data.get('difficulty', 1)
            )

            return level

        except Exception as e:
            print(f"Error loading level from {filepath}: {e}")
            return None

    @staticmethod
    def create_sample_levels(directory: str):
        """Create sample level files in the specified directory"""
        os.makedirs(directory, exist_ok=True)

        # Level 1 - Fixed version with correct expected results
        level1_data = {
            "id": "student_meal_subsidy",
            "title": "Student Meal Subsidy Law",
            "description": "Implement the new student meal subsidy law for Solarfurt",
            "background_story": "🌱 Welcome to Solarfurt, civil servant! Our eco-friendly city council has passed the Student Meal Subsidy Law. Your job is to implement this law in our legal database system.\n\n🔋 The law supports sustainable living: students under 25 are eligible for meal subsidies. Base rate is 50 credits, with a 30-credit bonus for low-income students.\n\n🏛️ This is your first assignment in our rusty-but-reliable legal tech system. Code with care - the future depends on it!",
            "given_facts": "% Citizens of Solarfurt's sustainable community\nperson(alice).\nperson(bob).\nperson(charlie).\nperson(diana).\n\n% Personal information\nage(alice, 22).\nage(bob, 26).\nage(charlie, 19).\nage(diana, 23).\n\n% Income levels\nincome(alice, low).\nincome(bob, medium).\nincome(charlie, low).\nincome(diana, high).\n\n% Student status\nstudent(alice).\nstudent(charlie).\n% Note: diana is NOT a student, bob is too old",
            "law_description": "🌿 Student Meal Subsidy Law (Solarfurt Ordinance 2024-001):\n\n1. Eligibility: Must be a student AND under 25 years old\n2. Base subsidy: 50 credits per month for eligible students\n3. Low-income bonus: Additional 30 credits (total 80)\n4. Implementation: Create eligible(Person) and subsidy_amount(Person, Amount)\n5. Non-eligible persons should make subsidy_amount fail",
            "queries": [
                {"query": "eligible(X)", "expected": ["alice", "charlie"], "description": "Find all eligible students"},
                {"query": "subsidy_amount(alice, Amount)", "expected": ["80"],
                 "description": "Alice: student + low income = 80"},
                {"query": "subsidy_amount(charlie, Amount)", "expected": ["80"],
                 "description": "Charlie: student + low income = 80"},
                {"query": "subsidy_amount(diana, Amount)", "expected": [],
                 "description": "Diana: not a student, should fail"},
                {"query": "subsidy_amount(bob, Amount)", "expected": [], "description": "Bob: too old, should fail"}
            ],
            "hints": [
                "🔍 Check BOTH student(Person) AND age < 25",
                "💰 Low-income students get 80 credits (50 + 30 bonus)",
                "⚠️  Non-eligible people should make subsidy_amount fail completely"
            ],
            "difficulty": 1
        }

        # Save level file
        with open(os.path.join(directory, '01_student_meal_subsidy.json'), 'w') as f:
            json.dump(level1_data, f, indent=2)

    @staticmethod
    def get_sample_levels() -> List[Level]:
        """Return hardcoded sample levels as fallback"""
        query1 = [
            Query("eligible(X)", ["alice", "charlie"], "Find all eligible students"),
            Query("subsidy_amount(alice, Amount)", ["80"], "Alice: student + low income = 80"),
            Query("subsidy_amount(charlie, Amount)", ["80"], "Charlie: student + low income = 80"),
            Query("subsidy_amount(diana, Amount)", [], "Diana: not a student, should fail"),
        ]

        level1 = Level(
            id="student_meal_subsidy",
            title="Student Meal Subsidy Law",
            description="Implement the new student meal subsidy law for Solarfurt",
            background_story="🌱 Welcome to Solarfurt, civil servant! Our eco-friendly city council has passed the Student Meal Subsidy Law.",
            given_facts="% Citizens of Solarfurt\nperson(alice).\nperson(bob).\nperson(charlie).\nperson(diana).\n\nage(alice, 22).\nage(bob, 26).\nage(charlie, 19).\nage(diana, 23).\n\nincome(alice, low).\nincome(bob, medium).\nincome(charlie, low).\nincome(diana, high).\n\nstudent(alice).\nstudent(charlie).",
            law_description="Student Meal Subsidy Law:\n1. Must be student AND under 25\n2. Base: 50 credits\n3. Low-income bonus: +30 credits",
            queries=query1,
            hints=["Check both conditions", "Use income facts", "Make predicate fail for non-eligible"]
        )

        return [level1]


class JanusPrologRunner:
    """Enhanced Prolog runner using janus_swi for better integration"""

    def __init__(self):
        self.janus_available = JANUS_AVAILABLE
        if self.janus_available:
            try:
                # Initialize janus_swi
                janus.query_once("writeln('Prolog available!')")
                self.prolog_available = True
            except Exception as e:
                print(f"Error initializing janus_swi: {e}")
                self.prolog_available = False
                self.janus_available = False
        else:
            self.prolog_available = False

    def run_queries(self, prolog_code: str, queries: List[Query]) -> Tuple[GameResult, Dict[str, Any]]:
        """Run Prolog queries using janus_swi"""
        if not self.prolog_available:
            return GameResult.PROLOG_ERROR, {
                "error": "Janus SWI-Prolog not available. Install with: pip install janus_swi"}

        try:
            # Load Prolog code from string using consult with data parameter
            janus.consult("temp_rules", prolog_code)

            results = {}
            all_correct = True

            for i, query in enumerate(queries):
                try:
                    # Execute query and collect all solutions
                    actual_results = []
                    found_solutions = False

                    # Use janus query functions
                    for solution in janus.query(query.query):
                        found_solutions = True
                        if solution:
                            # Extract variable bindings
                            if isinstance(solution, dict) and solution:
                                # For queries with variables, collect ONLY the variable values
                                for var, value in solution.items():
                                    # Skip boolean indicators and None values, only collect actual variable values
                                    if value not in [True, False, 'True', 'False', None, 'None'] and str(value) not in [
                                        'True', 'False', 'None']:
                                        actual_results.append(str(value))
                            elif not isinstance(solution, dict):
                                # For non-dict results, only add if it's not a boolean indicator or None
                                if (solution not in [True, False, 'True', 'False', None, 'None'] and
                                        str(solution) not in ['True', 'False', 'None']):
                                    actual_results.append(str(solution))

                    # If we found solutions but no actual_results were collected,
                    # this might be a boolean query that succeeded
                    if found_solutions and not actual_results:
                        # Check if this is a pure boolean query (no variables expected)
                        if not query.expected or (len(query.expected) == 1 and query.expected[0] in ['true', True]):
                            actual_results.append("true")

                    # If no solutions were found at all, try query_once for boolean queries
                    if not found_solutions:
                        try:
                            result = janus.query_once(query.query)
                            if result is not None:
                                if isinstance(result, dict) and result:
                                    # Extract variable values from the single result
                                    for var, value in result.items():
                                        # Skip boolean indicators
                                        if value not in [True, False, 'True', 'False', None, 'None']:
                                            actual_results.append(str(value))
                                elif result is True:
                                    # Only add "true" for pure boolean queries with no variables
                                    if not any(c.isupper() for c in query.query):  # Simple heuristic for no variables
                                        actual_results.append("true")
                        except:
                            pass  # Query failed, actual_results remains empty

                    # Handle expected results comparison
                    if not query.expected or query.expected == ['false']:  # Expected to fail
                        correct = len(actual_results) == 0
                    else:
                        # Compare with expected results
                        expected_set = set(str(e) for e in query.expected)
                        actual_set = set(str(r) for r in actual_results)
                        correct = actual_set == expected_set

                    results[f"query_{i}"] = {
                        "query": query.query,
                        "expected": query.expected,
                        "actual": actual_results,
                        "correct": correct
                    }

                    if not correct:
                        all_correct = False

                except Exception as e:
                    results[f"query_{i}"] = {
                        "query": query.query,
                        "expected": query.expected,
                        "actual": [],
                        "error": str(e),
                        "correct": False
                    }
                    all_correct = False

            if all_correct:
                return GameResult.SUCCESS, results
            else:
                return GameResult.WRONG_RESULTS, results

        except Exception as e:
            return GameResult.PROLOG_ERROR, {"error": f"Prolog error: {str(e)}"}

class LawMakerGUI:
    """Solarpunk-themed GUI for the Law Maker game"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Law Maker")
        self.root.geometry("1200x800")

        # Apply Solarpunk theme
        self.style = SolarpunkTheme.configure_style()
        self.root.configure(bg=SolarpunkTheme.COLORS['bg_primary'])

        # Game state
        self.levels_directory = "levels"
        self.levels = []
        self.current_level_index = 0
        self.current_level = None
        self.prolog_runner = JanusPrologRunner()
        self.attempts_remaining = 3

        # Load levels
        self.load_levels()

        # Setup GUI with Solarpunk styling
        self.setup_gui()

        # Load first level
        if self.levels:
            self.load_level(0)

    def load_levels(self):
        """Load levels from directory"""
        self.levels = LevelLoader.load_levels_from_directory(self.levels_directory)
        if not self.levels:
            messagebox.showerror("Error", "No levels could be loaded!")
            self.root.quit()

    def setup_gui(self):
        """Setup the Solarpunk-themed GUI components"""
        # Create header with rusty-futuristic styling
        header_frame = ttk.Frame(self.root, style='Panel.TFrame')
        header_frame.pack(fill=tk.X, padx=5, pady=5)

        title_label = ttk.Label(header_frame,
                                text="Solarfurt Department of Finance",
                                style='Title.TLabel')
        title_label.pack(pady=10)

        subtitle = ttk.Label(header_frame,
                             text="B Wing, 2030/05/12",
                             style='Header.TLabel')
        subtitle.pack(pady=(0, 10))

        # Create main notebook with custom styling
        self.notebook = ttk.Notebook(self.root, style='Solarpunk.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create frames for each tab
        self.level_frame = ttk.Frame(self.notebook, style='Solarpunk.TFrame')
        self.notebook.add(self.level_frame, text="📋 Mission Select")

        self.problem_frame = ttk.Frame(self.notebook, style='Solarpunk.TFrame')
        self.notebook.add(self.problem_frame, text="📖 Legal Brief")

        self.editor_frame = ttk.Frame(self.notebook, style='Solarpunk.TFrame')
        self.notebook.add(self.editor_frame, text="🖩 Pocket-Inferer")

        self.results_frame = ttk.Frame(self.notebook, style='Solarpunk.TFrame')
        self.notebook.add(self.results_frame, text="🔍 Test Results")

        self.setup_level_selection()
        self.setup_problem_description()
        self.setup_code_editor()
        self.setup_results_panel()

    def create_styled_text(self, parent, **kwargs):
        """Create a text widget with Solarpunk styling"""
        text_widget = scrolledtext.ScrolledText(
            parent,
            bg=SolarpunkTheme.COLORS['bg_input'],
            fg=SolarpunkTheme.COLORS['text_primary'],
            insertbackground=SolarpunkTheme.COLORS['accent_tertiary'],
            selectbackground=SolarpunkTheme.COLORS['accent_primary'],
            relief='sunken',
            borderwidth=2,
            **kwargs
        )
        return text_widget

    def setup_level_selection(self):
        """Setup Solarpunk-styled level selection panel"""
        # Header
        header = ttk.Label(self.level_frame,
                           text="🏛️ Select Your Legal Mission",
                           style='Header.TLabel')
        header.pack(pady=15)

        desc = ttk.Label(self.level_frame,
                         text="Choose a law to implement in our legal database:",
                         style='Solarpunk.TLabel')
        desc.pack(pady=5)

        # Level list with custom styling
        list_frame = ttk.Frame(self.level_frame, style='Panel.TFrame')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        self.level_listbox = tk.Listbox(
            list_frame,
            height=12,
            font=('Consolas', 11),
            bg=SolarpunkTheme.COLORS['bg_input'],
            fg=SolarpunkTheme.COLORS['text_primary'],
            selectbackground=SolarpunkTheme.COLORS['accent_tertiary'],
            selectforeground=SolarpunkTheme.COLORS['text_primary'],
            relief='sunken',
            borderwidth=2
        )
        self.level_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.level_listbox.bind('<Double-Button-1>', self.on_level_select)

        # Buttons with Solarpunk styling
        button_frame = ttk.Frame(self.level_frame, style='Solarpunk.TFrame')
        button_frame.pack(pady=15)

        ttk.Button(button_frame, text="⚡ Activate Mission",
                   command=self.on_level_select, style='Solarpunk.TButton').pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="🔄 Refresh Database",
                   command=self.refresh_levels, style='Solarpunk.TButton').pack(side=tk.LEFT, padx=10)

        # Status
        self.status_label = ttk.Label(self.level_frame, text="", style='Solarpunk.TLabel')
        self.status_label.pack(pady=10)

        self.populate_level_list()

    def setup_problem_description(self):
        """Setup Solarpunk-styled problem description panel"""
        # Title
        self.problem_title = ttk.Label(self.problem_frame, text="", style='Header.TLabel')
        self.problem_title.pack(pady=10)

        # Create sub-notebook for different sections
        problem_notebook = ttk.Notebook(self.problem_frame, style='Solarpunk.TNotebook')
        problem_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Background story tab
        story_frame = ttk.Frame(problem_notebook, style='Solarpunk.TFrame')
        problem_notebook.add(story_frame, text="🌿 Background")
        self.story_text = self.create_styled_text(story_frame, state=tk.DISABLED, height=12)
        self.story_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Given facts tab
        facts_frame = ttk.Frame(problem_notebook, style='Solarpunk.TFrame')
        problem_notebook.add(facts_frame, text="📊 Database Facts")
        self.facts_text = self.create_styled_text(facts_frame, state=tk.DISABLED, height=12, font=('Consolas', 10))
        self.facts_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Law description tab
        law_frame = ttk.Frame(problem_notebook, style='Solarpunk.TFrame')
        problem_notebook.add(law_frame, text="⚖️ Legal Requirements")
        self.law_text = self.create_styled_text(law_frame, state=tk.DISABLED, height=12)
        self.law_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Queries tab
        queries_frame = ttk.Frame(problem_notebook, style='Solarpunk.TFrame')
        problem_notebook.add(queries_frame, text="🧪 Test Specs")
        self.queries_text = self.create_styled_text(queries_frame, state=tk.DISABLED, height=12)
        self.queries_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Hints tab
        hints_frame = ttk.Frame(problem_notebook, style='Solarpunk.TFrame')
        problem_notebook.add(hints_frame, text="💡 Hints")
        self.hints_text = self.create_styled_text(hints_frame, state=tk.DISABLED, height=12)
        self.hints_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def setup_code_editor(self):
        """Setup Solarpunk-styled code editor panel"""
        # Header
        editor_header = ttk.Frame(self.editor_frame, style='Panel.TFrame')
        editor_header.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(editor_header, text="Prolog Pocket-Inferer",
                  style='Header.TLabel').pack(side=tk.LEFT)

        self.attempts_label = ttk.Label(editor_header, text="", style='Solarpunk.TLabel')
        self.attempts_label.pack(side=tk.RIGHT)

        # Code editor with enhanced styling
        self.code_text = self.create_styled_text(self.editor_frame, height=18)
        self.code_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Buttons
        button_frame = ttk.Frame(self.editor_frame, style='Solarpunk.TFrame')
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        self.test_button = ttk.Button(button_frame, text="🔬 Test Implementation",
                                      command=self.test_solution, style='Solarpunk.TButton')
        self.test_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="🗑️ Clear Code",
                   command=self.clear_code, style='Solarpunk.TButton').pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="📝 Load Example",
                   command=self.load_example, style='Solarpunk.TButton').pack(side=tk.LEFT, padx=5)

        # Prolog status
        self.prolog_status = ttk.Label(button_frame, text="", style='Solarpunk.TLabel')
        self.prolog_status.pack(side=tk.RIGHT, padx=10)

        self.update_prolog_status()

    def setup_results_panel(self):
        """Setup Solarpunk-styled results panel"""
        header = ttk.Label(self.results_frame, text="🔍 Legal Compliance Report",
                           style='Header.TLabel')
        header.pack(pady=15)

        self.results_text = self.create_styled_text(self.results_frame, height=25, state=tk.DISABLED)
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Results buttons
        results_buttons = ttk.Frame(self.results_frame, style='Solarpunk.TFrame')
        results_buttons.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(results_buttons, text="🗑️ Clear Report",
                   command=self.clear_results, style='Solarpunk.TButton').pack(side=tk.LEFT, padx=5)

    def populate_level_list(self):
        """Populate the level selection list"""
        self.level_listbox.delete(0, tk.END)
        for i, level in enumerate(self.levels):
            difficulty_icons = "⚡" * level.difficulty + "🌿" * (5 - level.difficulty)
            self.level_listbox.insert(tk.END,
                                      f"Mission {i + 1}: {level.title} {difficulty_icons}")

    def on_level_select(self, event=None):
        """Handle level selection"""
        selection = self.level_listbox.curselection()
        if selection:
            level_index = selection[0]
            self.load_level(level_index)
            self.notebook.select(self.problem_frame)

    def load_level(self, level_index: int):
        """Load a specific level"""
        if 0 <= level_index < len(self.levels):
            self.current_level_index = level_index
            self.current_level = self.levels[level_index]
            self.attempts_remaining = 3

            # Update problem description
            self.problem_title.config(text=f"Mission {level_index + 1}: {self.current_level.title}")

            # Update text areas
            self.update_text_widget(self.story_text, self.current_level.background_story)
            self.update_text_widget(self.facts_text, self.current_level.given_facts)
            self.update_text_widget(self.law_text, self.current_level.law_description)

            # Update queries display
            queries_text = "🧪 Test Specifications (your code must satisfy these):\n\n"
            for i, query in enumerate(self.current_level.queries, 1):
                queries_text += f"{i}. Query: {query.query}\n"
                queries_text += f"   Expected: {query.expected if query.expected else 'Should fail'}\n"
                if query.description:
                    queries_text += f"   📝 {query.description}\n"
                queries_text += "\n"

            self.update_text_widget(self.queries_text, queries_text)

            # Update hints
            if self.current_level.hints:
                hints_text = "💡 Hints from the local Net:\n\n"
                for i, hint in enumerate(self.current_level.hints, 1):
                    hints_text += f"{i}. {hint}\n"
            else:
                hints_text = "💫 No hints available - trust in the code, young padawan."

            self.update_text_widget(self.hints_text, hints_text)

            # Clear editor and results
            self.code_text.delete(1.0, tk.END)
            self.clear_results()

            # Update status
            self.update_attempts_display()
            self.status_label.config(text=f"🌱 Mission {level_index + 1} loaded: {self.current_level.title}")

    def update_text_widget(self, widget, text):
        """Update a text widget with new content"""
        widget.config(state=tk.NORMAL)
        widget.delete(1.0, tk.END)
        widget.insert(1.0, text)
        widget.config(state=tk.DISABLED)

    def update_attempts_display(self):
        """Update the attempts remaining display"""
        hearts = "💚" * self.attempts_remaining + "💔" * (3 - self.attempts_remaining)
        self.attempts_label.config(text=f"Attempts: {hearts}")

    def update_prolog_status(self):
        """Update the Prolog availability status"""
        if self.prolog_runner.prolog_available:
            self.prolog_status.config(text="⚡ Janus Prolog Online", foreground=SolarpunkTheme.COLORS['success'])
        else:
            self.prolog_status.config(text="⚠️ Prolog Offline", foreground=SolarpunkTheme.COLORS['warning'])

    def test_solution(self):
        """Test the user's solution with enhanced feedback"""
        if not self.current_level:
            messagebox.showwarning("Warning", "🌿 Please select a mission first!")
            return

        if self.attempts_remaining <= 0:
            messagebox.showinfo("Info", "💔 No attempts remaining for this mission!")
            return

        user_code = self.code_text.get(1.0, tk.END).strip()
        if not user_code:
            messagebox.showwarning("Warning", "⚡ Please enter some Prolog code in the forge!")
            return

        # Disable test button during testing
        self.test_button.config(state=tk.DISABLED)
        self.test_button.config(text="🔬 Analyzing...")

        # Run test in separate thread to avoid freezing GUI
        def run_test():
            try:
                # Combine given facts with user code
                full_code = self.current_level.given_facts + '\n' + user_code
                result, details = self.prolog_runner.run_queries(full_code, self.current_level.queries)

                # Update GUI in main thread
                self.root.after(0, lambda: self.display_test_results(result, details))
            except Exception as e:
                self.root.after(0, lambda: self.display_error(str(e)))

        threading.Thread(target=run_test, daemon=True).start()

    def display_test_results(self, result: GameResult, details: Dict):
        """Display test results with Solarpunk styling"""
        self.test_button.config(state=tk.NORMAL, text="🔬 Test Implementation")

        results_text = f"🔍 LEGAL COMPLIANCE REPORT 🔍\n"
        results_text += f"{'=' * 50}\n"
        results_text += f"Mission: {self.current_level.title}\n"
        results_text += f"Attempt: {4 - self.attempts_remaining}/3\n"
        results_text += f"{'=' * 50}\n\n"

        if result == GameResult.SUCCESS:
            results_text += "🎉 MISSION ACCOMPLISHED! 🎉\n"
            results_text += "Your legal implementation passes all compliance tests!\n"
            results_text += "🌱 The citizens of Solarfurt thank you for your service! 🌱\n\n"

            # Show detailed results
            for query_id, query_result in details.items():
                if query_id.startswith('query_'):
                    results_text += f"✅ Query: {query_result['query']}\n"
                    results_text += f"   Expected: {query_result['expected'] if query_result['expected'] else 'Should fail'}\n"
                    results_text += f"   Got: {query_result['actual']}\n\n"

            # Level completed
            messagebox.showinfo("🎉 Success!",
                                f"Mission {self.current_level_index + 1} completed!\n\n🌿 Your Prolog implementation correctly satisfies all legal requirements.\n\nGood job!")

        elif result == GameResult.PROLOG_ERROR:
            results_text += "⚠️ SYSTEM ERROR ⚠️\n"
            results_text += f"The rusty-futuristic compiler encountered an issue:\n"
            results_text += f"{details.get('error', 'Unknown error')}\n\n"
            results_text += "🔧 Check your syntax and try again, legal engineer!\n"

        elif result == GameResult.WRONG_RESULTS:
            results_text += "❌ COMPLIANCE VIOLATIONS DETECTED ❌\n\n"

            for query_id, query_result in details.items():
                if query_id.startswith('query_'):
                    if query_result['correct']:
                        results_text += f"✅ Query: {query_result['query']}\n"
                    else:
                        results_text += f"❌ Query: {query_result['query']}\n"

                    results_text += f"   Expected: {query_result['expected'] if query_result['expected'] else 'Should fail'}\n"
                    results_text += f"   Got: {query_result['actual']}\n"

                    if 'error' in query_result and query_result['error']:
                        results_text += f"   Error: {query_result['error']}\n"

                    results_text += "\n"

        # Update attempts
        self.attempts_remaining -= 1
        self.update_attempts_display()

        if result != GameResult.SUCCESS and self.attempts_remaining == 0:
            results_text += f"\n💔 OUT OF ATTEMPTS! 💔\n"
            results_text += "Mission failed, but you can try other missions or reload this one.\n"
            results_text += "🌿 Learn from this experience, young legal engineer! 🌿\n"
        elif result != GameResult.SUCCESS and self.attempts_remaining > 0:
            hearts = "💚" * self.attempts_remaining
            results_text += f"\n⚡ Try again! {hearts} attempts remaining.\n"

            # Show hints after first failure
            if self.attempts_remaining == 2 and self.current_level.hints:
                results_text += "\n💡 You can browse the local net for hints:\n"
                for i, hint in enumerate(self.current_level.hints, 1):
                    results_text += f"{i}. {hint}\n"

        # Display results with enhanced styling
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(1.0, results_text)

        # Add some color coding
        self.results_text.tag_configure("success", foreground=SolarpunkTheme.COLORS['success'])
        self.results_text.tag_configure("error", foreground=SolarpunkTheme.COLORS['warning'])
        self.results_text.tag_configure("header", foreground=SolarpunkTheme.COLORS['accent_secondary'])

        # Apply tags
        content = self.results_text.get(1.0, tk.END)
        lines = content.split('\n')
        for i, line in enumerate(lines):
            line_start = f"{i + 1}.0"
            line_end = f"{i + 1}.end"

            if "✅" in line or "ACCOMPLISHED" in line or "SUCCESS" in line:
                self.results_text.tag_add("success", line_start, line_end)
            elif "❌" in line or "ERROR" in line or "VIOLATIONS" in line:
                self.results_text.tag_add("error", line_start, line_end)
            elif "REPORT" in line or "Mission:" in line:
                self.results_text.tag_add("header", line_start, line_end)

        self.results_text.config(state=tk.DISABLED)

        # Switch to results tab
        self.notebook.select(self.results_frame)

    def display_error(self, error_msg: str):
        """Display an error message with Solarpunk styling"""
        self.test_button.config(state=tk.NORMAL, text="🔬 Test Implementation")
        messagebox.showerror("⚠️ System Error", f"🔧 The compiler encountered an issue:\n\n{error_msg}")

    def clear_code(self):
        """Clear the code editor"""
        self.code_text.delete(1.0, tk.END)

    def clear_results(self):
        """Clear the results panel"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        self.results_text.config(state=tk.DISABLED)

    def load_example(self):
        """Load an example solution (for testing purposes)"""
        if not self.current_level:
            messagebox.showwarning("Warning", "🌿 Please select a mission first!")
            return

        # Example solution for the student subsidy level
        example_code = "% 🌱 Your Prolog code goes here\n% Implement the required predicates for sustainable law!\n\n"

        if self.current_level.id == "student_meal_subsidy":
            example_code = """% 🌱 Student meal subsidy implementation for Solarfurt
% Sustainable legal code for eco-friendly governance

% A person is eligible if they are a student AND under 25
eligible(Person) :-
    student(Person),
    age(Person, Age),
    Age < 25.

% Low-income eligible students get 80 credits (50 + 30 bonus)
subsidy_amount(Person, Amount) :-
    eligible(Person),
    income(Person, low),
    Amount = 80.

% Other eligible students get 50 credits (base amount)
subsidy_amount(Person, Amount) :-
    eligible(Person),
    \\+ income(Person, low),
    Amount = 50.

% 🔋 Note: Non-eligible persons will make subsidy_amount fail
%    which is exactly what the law requires!"""

        self.code_text.delete(1.0, tk.END)
        self.code_text.insert(1.0, example_code)

    def refresh_levels(self):
        """Refresh levels from current directory"""
        try:
            self.levels = LevelLoader.load_levels_from_directory(self.levels_directory)
            self.populate_level_list()
            self.status_label.config(text=f"🔄 Refreshed {len(self.levels)} missions from database")

            # Reload current level if it still exists
            if (self.current_level and
                    self.current_level_index < len(self.levels) and
                    self.levels[self.current_level_index].id == self.current_level.id):
                self.load_level(self.current_level_index)
            elif self.levels:
                self.load_level(0)

        except Exception as e:
            messagebox.showerror("Error", f"🔧 Failed to refresh legal database:\n{e}")

    def run(self):
        """Start the Solarpunk GUI application"""

        def show_welcome_dialog():
            """Create a custom welcome dialog with image"""
            # Create the dialog window
            dialog = tk.Toplevel(self.root)
            dialog.title("Law Maker")
            dialog.geometry("900x900")  # Made taller to accommodate both images
            dialog.resizable(False, False)
            dialog.grab_set()  # Make it modal

            # Center the dialog
            dialog.transient(self.root)
            dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))

            # Main frame with scrollbar capability
            main_frame = tk.Frame(dialog, bg='#2d5016', padx=20, pady=20)
            main_frame.pack(fill=tk.BOTH, expand=True)

            # Try to load and display the cityscape image
            try:
                if os.path.exists("sprites/cityscape-background-illustration.jpg"):
                    # Load and resize the image
                    image = Image.open("sprites/cityscape-background-illustration.jpg")
                    # Resize to fit nicely in the dialog
                    image = image.resize((800, 300), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image)

                    # Image label
                    img_label = tk.Label(main_frame, image=photo, bg='#2d5016')
                    img_label.image = photo  # Keep a reference
                    img_label.pack(pady=(0, 15))
                else:
                    # Fallback if image not found
                    tk.Label(main_frame, text="[City Image Not Found]",
                             font=('Arial', 12), bg='#2d5016', fg='#90EE90').pack(pady=(0, 15))
            except Exception as e:
                # Fallback if PIL not available or other error
                tk.Label(main_frame, text="[Solarpunk City]",
                         font=('Arial', 12), bg='#2d5016', fg='#90EE90').pack(pady=(0, 15))

            # Create a horizontal frame for text and device image side by side
            content_frame = tk.Frame(main_frame, bg='#2d5016')
            content_frame.pack(pady=(0, 15), fill=tk.BOTH, expand=True)

            # Left side - Welcome text
            text_frame = tk.Frame(content_frame, bg='#2d5016')
            text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

            welcome_msg = """Welcome to Solarfurt!

    It's the year 2028. Society is aging and more and more civil servants are starting to retire.

    To tackle the problem, the citizens of Solarfurt decided to transform all laws into a machine-processable format.

    For this, a new device was developed: the "Pocket-Inferer", a logical calculator with which public servants could turn laws, data and queries into understandable code.

    As a civil servant, your task will be to learn how to use the Pocket-Inferer and turn law into code.

    Are you up for the challenge?"""

            # Text widget for the message
            text_widget = tk.Text(text_frame, height=12, width=45, wrap=tk.WORD,
                                  font=('Arial', 10), bg='#3d6026', fg='#90EE90',
                                  relief=tk.FLAT, bd=0, padx=10, pady=10)
            text_widget.insert(tk.END, welcome_msg)
            text_widget.config(state=tk.DISABLED)  # Make it read-only
            text_widget.pack(fill=tk.BOTH, expand=True)

            # Right side - Pocket-Inferer device
            device_frame = tk.Frame(content_frame, bg='#2d5016')
            device_frame.pack(side=tk.RIGHT, padx=(10, 0))

            # Try to load and display the Pocket-Inferer image
            try:
                if os.path.exists("sprites/pocket-inferer.jpg"):
                    # Load and resize the Pocket-Inferer image
                    pocket_image = Image.open("sprites/pocket-inferer.jpg")
                    # Resize to fit nicely on the right side
                    pocket_image = pocket_image.resize((300, 350), Image.Resampling.LANCZOS)
                    pocket_photo = ImageTk.PhotoImage(pocket_image)

                    # Label for the device
                    tk.Label(device_frame, text="The Pocket-Inferer",
                             font=('Arial', 12, 'bold'), bg='#2d5016', fg='#90EE90').pack(pady=(0, 10))

                    # Device image
                    pocket_img_label = tk.Label(device_frame, image=pocket_photo, bg='#2d5016')
                    pocket_img_label.image = pocket_photo  # Keep a reference
                    pocket_img_label.pack()

                elif os.path.exists("sprites/pocket-inferer.png"):
                    # Try PNG format as fallback
                    pocket_image = Image.open("sprites/pocket-inferer.png")
                    pocket_image = pocket_image.resize((300, 350), Image.Resampling.LANCZOS)
                    pocket_photo = ImageTk.PhotoImage(pocket_image)

                    tk.Label(device_frame, text="The Pocket-Inferer",
                             font=('Arial', 12, 'bold'), bg='#2d5016', fg='#90EE90').pack(pady=(0, 10))

                    pocket_img_label = tk.Label(device_frame, image=pocket_photo, bg='#2d5016')
                    pocket_img_label.image = pocket_photo
                    pocket_img_label.pack()

                else:
                    # Fallback if Pocket-Inferer image not found
                    tk.Label(device_frame, text="The Pocket-Inferer",
                             font=('Arial', 12, 'bold'), bg='#2d5016', fg='#90EE90').pack(pady=(0, 10))

                    # Create a placeholder box
                    placeholder_frame = tk.Frame(device_frame, bg='#4d7036', width=300, height=350, relief=tk.RAISED,
                                                 bd=2)
                    placeholder_frame.pack_propagate(False)  # Maintain size
                    placeholder_frame.pack()

                    tk.Label(placeholder_frame, text="📱\n[Device Image\nNot Found]\n🔧",
                             font=('Arial', 12), bg='#4d7036', fg='#90EE90', justify=tk.CENTER).place(relx=0.5,
                                                                                                      rely=0.5,
                                                                                                      anchor=tk.CENTER)

            except Exception as e:
                # Fallback if image loading fails
                tk.Label(device_frame, text="The Pocket-Inferer",
                         font=('Arial', 12, 'bold'), bg='#2d5016', fg='#90EE90').pack(pady=(0, 10))

                # Create a placeholder box
                placeholder_frame = tk.Frame(device_frame, bg='#4d7036', width=300, height=350, relief=tk.RAISED, bd=2)
                placeholder_frame.pack_propagate(False)  # Maintain size
                placeholder_frame.pack()

                tk.Label(placeholder_frame, text="📱\n[Logical\nCalculator]\n🔧",
                         font=('Arial', 12), bg='#4d7036', fg='#90EE90', justify=tk.CENTER).place(relx=0.5, rely=0.5,
                                                                                                  anchor=tk.CENTER)

            # OK button
            ok_button = tk.Button(main_frame, text="Yeah! Let's start Coding!",
                                  command=dialog.destroy,
                                  font=('Arial', 12, 'bold'),
                                  bg='#4d7036', fg='#90EE90',
                                  relief=tk.RAISED, bd=2,
                                  padx=20, pady=10)
            ok_button.pack(pady=(15, 0))

            # Wait for the dialog to be closed
            dialog.wait_window()

        # Show the welcome dialog
        show_welcome_dialog()

        # Start the main loop
        self.root.mainloop()

def create_sample_levels():
    """Create sample level files in the levels directory"""
    levels_dir = "levels"
    LevelLoader.create_sample_levels(levels_dir)
    print(f"🌱 Sample legal missions created in '{levels_dir}' directory")

    # Create a Solarpunk-themed README
    readme_content = """# 🌱 Solarfurt Legal System - Mission Database 🔋

Welcome to the legal code repository for the sustainable city-state of Solarfurt!

## 🏛️ Mission Structure

Each legal mission is stored as a JSON file with eco-friendly metadata:

```json
{
  "id": "unique_mission_identifier",
  "title": "Mission Title",
  "description": "Brief eco-description",
  "background_story": "🌿 Sustainable story context",
  "given_facts": "% Prolog facts from the database",
  "law_description": "⚖️ Legal requirements for implementation",
  "queries": [
    {
      "query": "prolog_query(X)",
      "expected": ["expected", "results"],
      "description": "🧪 Test specification"
    }
  ],
  "hints": ["💡 Hints from the local net"],
  "difficulty": 1
}
```

## 🔧 Adding New Missions

1. Create a new JSON file in this directory
2. Follow the naming convention: `XX_mission_name.json`
3. Use sustainable coding practices
4. Test thoroughly in the compiler
5. Refresh the legal database in the app

## ⚡ Mission Design Philosophy

- 🌿 Start simple, grow organically
- 🔋 Provide engaging sustainable contexts  
- 🧪 Include comprehensive test coverage
- 💡 Add helpful guidance for learning
- ⚖️ Ensure legal logic is sound and fair

*Powered by renewable Prolog energy since 2024* 🌱
"""

    with open(os.path.join(levels_dir, "README.md"), 'w') as f:
        f.write(readme_content)


def main():
    """Main entry point for the Solarpunk Legal System"""
    print("🌱 Initializing Solarfurt Legal System...")

    # Create sample levels if they don't exist
    if not os.path.exists("levels") or not os.listdir("levels"):
        print("🔧 Setting up legal database...")
        create_sample_levels()

    # Check for janus_swi
    if not JANUS_AVAILABLE:
        print("⚠️  Warning: janus_swi not available!")
        print("🔧 For optimal performance, install with: pip install janus_swi")
        print("⚡ The system will still work, but with limited Prolog integration.")

    # Start the Solarpunk GUI
    try:
        print("🌿 Launching rusty-futuristic interface...")
        app = LawMakerGUI()
        app.run()
    except KeyboardInterrupt:
        print("\n🌱 Legal system shutdown initiated. Thank you for serving Solarfurt!")
    except Exception as e:
        print(f"🔧 System error in the compiler: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()