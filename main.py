#!/usr/bin/env python3
"""
Law Maker - A Prolog Programming Game

A game where players implement laws in Prolog for the fictional city-state of Solarfurt.
Players are given facts, rules, and expected query results, then must write Prolog code
to correctly implement the law.
"""

import os
import json
import tempfile
import subprocess
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import threading


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


class LevelLoader:
    """Loads level configurations from JSON files"""

    @staticmethod
    def load_levels_from_directory(directory: str) -> List[Level]:
        """Load all levels from a directory containing JSON files"""
        levels = []

        if not os.path.exists(directory):
            # Create sample levels if directory doesn't exist
            LevelLoader.create_sample_levels(directory)

        try:
            level_files = [f for f in os.listdir(directory) if f.endswith('.json')]
            level_files.sort()  # Ensure consistent ordering

            for filename in level_files:
                filepath = os.path.join(directory, filename)
                level = LevelLoader.load_level_from_file(filepath)
                if level:
                    levels.append(level)

        except Exception as e:
            print(f"Error loading levels: {e}")
            # Return sample levels as fallback
            return LevelLoader.get_sample_levels()

        return levels if levels else LevelLoader.get_sample_levels()

    @staticmethod
    def load_level_from_file(filepath: str) -> Optional[Level]:
        """Load a single level from a JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

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

        # Level 1
        level1_data = {
            "id": "basic_eligibility",
            "title": "Student Meal Subsidy Law",
            "description": "Implement the new student meal subsidy law for Solarfurt",
            "background_story": "Welcome to Solarfurt, civil servant! The city council has just passed the Student Meal Subsidy Law. Your job is to implement this law in our legal database system (Prolog).\n\nThe law is simple: students who are under 25 years old and have low income are eligible for meal subsidies. Students get 50 credits per month, and low-income students get an additional 30 credits bonus.",
            "given_facts": "% Citizens of Solarfurt\nperson(alice).\nperson(bob).\nperson(charlie).\nperson(diana).\n\n% Personal information\nage(alice, 22).\nage(bob, 26).\nage(charlie, 19).\nage(diana, 23).\n\nincome(alice, low).\nincome(bob, medium).\nincome(charlie, low).\nincome(diana, high).\n\nstudent(alice).\nstudent(charlie).\nstudent(diana).",
            "law_description": "Student Meal Subsidy Law:\n1. A person is eligible for meal subsidy if they are a student AND under 25 years old\n2. Base subsidy amount is 50 credits per month for eligible students\n3. Low-income eligible students receive an additional 30 credits bonus (total 80 credits)\n4. You need to implement predicates: eligible(Person) and subsidy_amount(Person, Amount)",
            "queries": [
                {"query": "eligible(X)", "expected": ["alice", "charlie"],
                 "description": "Who is eligible for subsidies?"},
                {"query": "subsidy_amount(alice, Amount)", "expected": ["80"], "description": "Alice's subsidy amount"},
                {"query": "subsidy_amount(charlie, Amount)", "expected": ["80"],
                 "description": "Charlie's subsidy amount"},
                {"query": "subsidy_amount(diana, Amount)", "expected": ["false"],
                 "description": "Diana should not get subsidy"}
            ],
            "hints": [
                "Remember to check both student status AND age",
                "Use the 'income(Person, low)' fact to determine bonus eligibility",
                "If someone is not eligible, subsidy_amount should fail (return false)"
            ],
            "difficulty": 1
        }

        # Level 2
        level2_data = {
            "id": "parking_permits",
            "title": "Parking Permit Regulation",
            "description": "Implement the new parking permit system for Solarfurt",
            "background_story": "The Solarfurt Traffic Department needs you to implement the new parking permit system. Different types of residents get different parking privileges based on their circumstances.",
            "given_facts": "% Residents\nperson(emma).\nperson(frank).\nperson(grace).\nperson(henry).\n\n% Residential status\nresident_type(emma, senior).\nresident_type(frank, disabled).\nresident_type(grace, regular).\nresident_type(henry, student).\n\n% Vehicle information\nowns_car(emma).\nowns_car(frank).\nowns_car(grace).\n\n% District information\nlives_in_district(emma, downtown).\nlives_in_district(frank, suburbs).\nlives_in_district(grace, downtown).\nlives_in_district(henry, downtown).",
            "law_description": "Parking Permit Law:\n1. All car owners who are residents get a basic parking permit\n2. Senior citizens get free permits (cost: 0)\n3. Disabled residents get free permits (cost: 0)\n4. Students get discounted permits (cost: 25)\n5. Regular residents pay full price (cost: 100)\n6. Downtown residents pay an additional 20 district fee (unless free permit)\n\nImplement: has_permit(Person) and permit_cost(Person, Cost)",
            "queries": [
                {"query": "has_permit(X)", "expected": ["emma", "frank", "grace"],
                 "description": "Who has parking permits?"},
                {"query": "permit_cost(emma, Cost)", "expected": ["20"],
                 "description": "Emma's permit cost (senior + downtown)"},
                {"query": "permit_cost(frank, Cost)", "expected": ["0"],
                 "description": "Frank's permit cost (disabled)"},
                {"query": "permit_cost(grace, Cost)", "expected": ["120"],
                 "description": "Grace's permit cost (regular + downtown)"},
                {"query": "permit_cost(henry, Cost)", "expected": ["false"], "description": "Henry doesn't own a car"}
            ],
            "hints": [
                "Only car owners can get permits",
                "Check resident_type for special pricing",
                "Downtown district fee applies to non-free permits"
            ],
            "difficulty": 2
        }

        # Save level files
        with open(os.path.join(directory, '01_student_meal_subsidy.json'), 'w') as f:
            json.dump(level1_data, f, indent=2)

        with open(os.path.join(directory, '02_parking_permits.json'), 'w') as f:
            json.dump(level2_data, f, indent=2)

    @staticmethod
    def get_sample_levels() -> List[Level]:
        """Return hardcoded sample levels as fallback"""
        query1 = [
            Query("eligible(X)", ["alice", "charlie"], "Who is eligible for subsidies?"),
            Query("subsidy_amount(alice, Amount)", ["80"], "Alice's subsidy amount"),
            Query("subsidy_amount(charlie, Amount)", ["80"], "Charlie's subsidy amount"),
            Query("subsidy_amount(diana, Amount)", ["false"], "Diana should not get subsidy"),
        ]

        level1 = Level(
            id="basic_eligibility",
            title="Student Meal Subsidy Law",
            description="Implement the new student meal subsidy law for Solarfurt",
            background_story="Welcome to Solarfurt, civil servant! The city council has just passed the Student Meal Subsidy Law. Your job is to implement this law in our legal database system (Prolog).\n\nThe law is simple: students who are under 25 years old and have low income are eligible for meal subsidies. Students get 50 credits per month, and low-income students get an additional 30 credits bonus.",
            given_facts="% Citizens of Solarfurt\nperson(alice).\nperson(bob).\nperson(charlie).\nperson(diana).\n\n% Personal information\nage(alice, 22).\nage(bob, 26).\nage(charlie, 19).\nage(diana, 23).\n\nincome(alice, low).\nincome(bob, medium).\nincome(charlie, low).\nincome(diana, high).\n\nstudent(alice).\nstudent(charlie).\nstudent(diana).",
            law_description="Student Meal Subsidy Law:\n1. A person is eligible for meal subsidy if they are a student AND under 25 years old\n2. Base subsidy amount is 50 credits per month for eligible students\n3. Low-income eligible students receive an additional 30 credits bonus (total 80 credits)\n4. You need to implement predicates: eligible(Person) and subsidy_amount(Person, Amount)",
            queries=query1,
            hints=[
                "Remember to check both student status AND age",
                "Use the 'income(Person, low)' fact to determine bonus eligibility",
                "If someone is not eligible, subsidy_amount should fail (return false)"
            ]
        )

        return [level1]


class PrologRunner:
    """Handles running Prolog queries using SWI-Prolog"""

    def __init__(self):
        self.prolog_available = self._check_prolog_availability()

    def _check_prolog_availability(self) -> bool:
        """Check if SWI-Prolog is available"""
        try:
            result = subprocess.run(['swipl', '--version'],
                                    capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def run_queries(self, prolog_code: str, queries: List[Query]) -> Tuple[GameResult, Dict[str, Any]]:
        """Run Prolog queries and return results"""
        if not self.prolog_available:
            return GameResult.PROLOG_ERROR, {"error": "SWI-Prolog not found. Please install SWI-Prolog."}

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.pl', delete=False) as f:
                f.write(prolog_code)
                temp_file = f.name

            results = {}
            all_correct = True

            for i, query in enumerate(queries):
                try:
                    # Create a query file that loads the program and runs the query
                    query_code = f"""
:- consult('{temp_file}').
:- findall(X, ({query.query}), Solutions),
   forall(member(Sol, Solutions), (write(Sol), write('.'), nl)),
   halt.
"""

                    with tempfile.NamedTemporaryFile(mode='w', suffix='.pl', delete=False) as qf:
                        qf.write(query_code)
                        query_file = qf.name

                    # Run the query
                    result = subprocess.run(
                        ['swipl', '-q', '-t', 'halt', '-s', query_file],
                        capture_output=True, text=True, timeout=10
                    )

                    if result.returncode != 0:
                        results[f"query_{i}"] = {
                            "query": query.query,
                            "expected": query.expected,
                            "actual": [],
                            "error": result.stderr,
                            "correct": False
                        }
                        all_correct = False
                    else:
                        # Parse results
                        actual_results = []
                        if result.stdout.strip():
                            lines = result.stdout.strip().split('\n')
                            for line in lines:
                                if line.strip() and line.strip() != 'true.' and line.strip() != 'false.':
                                    actual_results.append(line.strip().rstrip('.'))

                        # Compare with expected results
                        correct = set(actual_results) == set(query.expected)
                        results[f"query_{i}"] = {
                            "query": query.query,
                            "expected": query.expected,
                            "actual": actual_results,
                            "correct": correct
                        }

                        if not correct:
                            all_correct = False

                    # Clean up query file
                    os.unlink(query_file)

                except subprocess.TimeoutExpired:
                    results[f"query_{i}"] = {
                        "query": query.query,
                        "expected": query.expected,
                        "actual": [],
                        "error": "Query timed out",
                        "correct": False
                    }
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

            # Clean up main file
            os.unlink(temp_file)

            if all_correct:
                return GameResult.SUCCESS, results
            else:
                return GameResult.WRONG_RESULTS, results

        except Exception as e:
            return GameResult.PROLOG_ERROR, {"error": str(e)}


class LawMakerGUI:
    """GUI for the Law Maker game"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Lawmaker")
        self.root.geometry("1000x700")

        # Game state
        self.levels_directory = "levels"
        self.levels = []
        self.current_level_index = 0
        self.current_level = None
        self.prolog_runner = PrologRunner()
        self.attempts_remaining = 3

        # Load levels
        self.load_levels()

        # Setup GUI
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
        """Setup the GUI components"""
        # Create main menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Levels Directory", command=self.load_levels_directory)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Level selection frame
        self.level_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.level_frame, text="Level Selection")

        # Problem description frame
        self.problem_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.problem_frame, text="Problem Description")

        # Code editor frame
        self.editor_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.editor_frame, text="Code Editor")

        # Results frame
        self.results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.results_frame, text="Test Results")

        self.setup_level_selection()
        self.setup_problem_description()
        self.setup_code_editor()
        self.setup_results_panel()

    def setup_level_selection(self):
        """Setup level selection panel"""
        ttk.Label(self.level_frame, text="Law Maker - Solarfurt Legal System",
                  font=('Arial', 16, 'bold')).pack(pady=10)

        ttk.Label(self.level_frame,
                  text="Select a level to implement laws in Prolog for the city-state of Solarfurt:",
                  font=('Arial', 10)).pack(pady=5)

        # Level list
        self.level_listbox = tk.Listbox(self.level_frame, height=15, font=('Arial', 10))
        self.level_listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        self.level_listbox.bind('<Double-Button-1>', self.on_level_select)

        # Buttons
        button_frame = ttk.Frame(self.level_frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Select Level",
                   command=self.on_level_select).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Refresh Levels",
                   command=self.refresh_levels).pack(side=tk.LEFT, padx=5)

        # Status
        self.status_label = ttk.Label(self.level_frame, text="")
        self.status_label.pack(pady=5)

        self.populate_level_list()

    def setup_problem_description(self):
        """Setup problem description panel"""
        # Title
        self.problem_title = ttk.Label(self.problem_frame, text="",
                                       font=('Arial', 14, 'bold'))
        self.problem_title.pack(pady=5)

        # Create scrollable text areas
        notebook_problem = ttk.Notebook(self.problem_frame)
        notebook_problem.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Background story tab
        story_frame = ttk.Frame(notebook_problem)
        notebook_problem.add(story_frame, text="Background Story")
        self.story_text = scrolledtext.ScrolledText(story_frame, wrap=tk.WORD,
                                                    state=tk.DISABLED, height=8)
        self.story_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Given facts tab
        facts_frame = ttk.Frame(notebook_problem)
        notebook_problem.add(facts_frame, text="Given Facts")
        self.facts_text = scrolledtext.ScrolledText(facts_frame, wrap=tk.WORD,
                                                    state=tk.DISABLED, height=8,
                                                    font=('Courier', 10))
        self.facts_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Law description tab
        law_frame = ttk.Frame(notebook_problem)
        notebook_problem.add(law_frame, text="Law Description")
        self.law_text = scrolledtext.ScrolledText(law_frame, wrap=tk.WORD,
                                                  state=tk.DISABLED, height=8)
        self.law_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Queries tab
        queries_frame = ttk.Frame(notebook_problem)
        notebook_problem.add(queries_frame, text="Test Queries")
        self.queries_text = scrolledtext.ScrolledText(queries_frame, wrap=tk.WORD,
                                                      state=tk.DISABLED, height=8)
        self.queries_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Hints tab
        hints_frame = ttk.Frame(notebook_problem)
        notebook_problem.add(hints_frame, text="Hints")
        self.hints_text = scrolledtext.ScrolledText(hints_frame, wrap=tk.WORD,
                                                    state=tk.DISABLED, height=8)
        self.hints_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def setup_code_editor(self):
        """Setup code editor panel"""
        # Title and status
        editor_header = ttk.Frame(self.editor_frame)
        editor_header.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(editor_header, text="Prolog Code Editor",
                  font=('Arial', 12, 'bold')).pack(side=tk.LEFT)

        self.attempts_label = ttk.Label(editor_header, text="")
        self.attempts_label.pack(side=tk.RIGHT)

        # Code editor
        self.code_text = scrolledtext.ScrolledText(self.editor_frame, wrap=tk.WORD,
                                                   height=20, font=('Courier', 11))
        self.code_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        # Buttons
        button_frame = ttk.Frame(self.editor_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        self.test_button = ttk.Button(button_frame, text="Test Solution",
                                      command=self.test_solution)
        self.test_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Clear Code",
                   command=self.clear_code).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Load Example",
                   command=self.load_example).pack(side=tk.LEFT, padx=5)

        # Prolog status
        self.prolog_status = ttk.Label(button_frame, text="")
        self.prolog_status.pack(side=tk.RIGHT, padx=5)

        self.update_prolog_status()

    def setup_results_panel(self):
        """Setup results panel"""
        ttk.Label(self.results_frame, text="Test Results",
                  font=('Arial', 12, 'bold')).pack(pady=5)

        self.results_text = scrolledtext.ScrolledText(self.results_frame, wrap=tk.WORD,
                                                      height=25, font=('Courier', 10))
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Results buttons
        results_buttons = ttk.Frame(self.results_frame)
        results_buttons.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(results_buttons, text="Clear Results",
                   command=self.clear_results).pack(side=tk.LEFT, padx=5)

    def populate_level_list(self):
        """Populate the level selection list"""
        self.level_listbox.delete(0, tk.END)
        for i, level in enumerate(self.levels):
            difficulty_stars = "★" * level.difficulty
            self.level_listbox.insert(tk.END,
                                      f"Level {i + 1}: {level.title} {difficulty_stars}")

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
            self.problem_title.config(text=f"Level {level_index + 1}: {self.current_level.title}")

            # Update text areas
            self.update_text_widget(self.story_text, self.current_level.background_story)
            self.update_text_widget(self.facts_text, self.current_level.given_facts)
            self.update_text_widget(self.law_text, self.current_level.law_description)

            # Update queries display
            queries_text = "Test Queries (your implementation should satisfy these):\n\n"
            for i, query in enumerate(self.current_level.queries, 1):
                queries_text += f"{i}. Query: {query.query}\n"
                queries_text += f"   Expected: {query.expected}\n"
                if query.description:
                    queries_text += f"   ({query.description})\n"
                queries_text += "\n"

            self.update_text_widget(self.queries_text, queries_text)

            # Update hints
            if self.current_level.hints:
                hints_text = "Hints to help you:\n\n"
                for i, hint in enumerate(self.current_level.hints, 1):
                    hints_text += f"{i}. {hint}\n"
            else:
                hints_text = "No hints available for this level."

            self.update_text_widget(self.hints_text, hints_text)

            # Clear editor and results
            self.code_text.delete(1.0, tk.END)
            self.clear_results()

            # Update status
            self.update_attempts_display()
            self.status_label.config(text=f"Level {level_index + 1} loaded: {self.current_level.title}")

    def update_text_widget(self, widget, text):
        """Update a text widget with new content"""
        widget.config(state=tk.NORMAL)
        widget.delete(1.0, tk.END)
        widget.insert(1.0, text)
        widget.config(state=tk.DISABLED)

    def update_attempts_display(self):
        """Update the attempts remaining display"""
        self.attempts_label.config(text=f"Attempts remaining: {self.attempts_remaining}")

    def update_prolog_status(self):
        """Update the Prolog availability status"""
        if self.prolog_runner.prolog_available:
            self.prolog_status.config(text="✓ SWI-Prolog available", foreground="green")
        else:
            self.prolog_status.config(text="✗ SWI-Prolog not found", foreground="red")

    def test_solution(self):
        """Test the user's solution"""
        if not self.current_level:
            messagebox.showwarning("Warning", "Please select a level first!")
            return

        if self.attempts_remaining <= 0:
            messagebox.showinfo("Info", "No attempts remaining for this level!")
            return

        user_code = self.code_text.get(1.0, tk.END).strip()
        if not user_code:
            messagebox.showwarning("Warning", "Please enter some Prolog code!")
            return

        # Disable test button during testing
        self.test_button.config(state=tk.DISABLED)
        self.test_button.config(text="Testing...")

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
        """Display test results"""
        self.test_button.config(state=tk.NORMAL, text="Test Solution")

        results_text = f"=== TEST RESULTS ===\n"
        results_text += f"Level: {self.current_level.title}\n"
        results_text += f"Attempt: {4 - self.attempts_remaining}\n\n"

        if result == GameResult.SUCCESS:
            results_text += "🎉 CONGRATULATIONS! Your implementation is correct!\n"
            results_text += "All test queries passed!\n\n"

            # Show detailed results
            for query_id, query_result in details.items():
                if query_id.startswith('query_'):
                    results_text += f"✅ Query: {query_result['query']}\n"
                    results_text += f"   Expected: {query_result['expected']}\n"
                    results_text += f"   Got: {query_result['actual']}\n\n"

            # Level completed
            messagebox.showinfo("Success!",
                                f"Level {self.current_level_index + 1} completed!\n\nYour Prolog implementation correctly satisfies all test queries.")

        elif result == GameResult.PROLOG_ERROR:
            results_text += "❌ Prolog Error:\n"
            results_text += f"{details.get('error', 'Unknown error')}\n\n"

        elif result == GameResult.WRONG_RESULTS:
            results_text += "❌ Some queries failed:\n\n"

            for query_id, query_result in details.items():
                if query_id.startswith('query_'):
                    if query_result['correct']:
                        results_text += f"✅ Query: {query_result['query']}\n"
                    else:
                        results_text += f"❌ Query: {query_result['query']}\n"

                    results_text += f"   Expected: {query_result['expected']}\n"
                    results_text += f"   Got: {query_result['actual']}\n"

                    if 'error' in query_result and query_result['error']:
                        results_text += f"   Error: {query_result['error']}\n"

                    results_text += "\n"

        # Update attempts
        self.attempts_remaining -= 1
        self.update_attempts_display()

        if result != GameResult.SUCCESS and self.attempts_remaining == 0:
            results_text += f"\n❌ Out of attempts for this level!\n"
            results_text += "You can still try other levels or reload this one.\n"
        elif result != GameResult.SUCCESS and self.attempts_remaining > 0:
            results_text += f"\nTry again! {self.attempts_remaining} attempts remaining.\n"

            # Show hints after first failure
            if self.attempts_remaining == 2 and self.current_level.hints:
                results_text += "\nHints to help you:\n"
                for i, hint in enumerate(self.current_level.hints, 1):
                    results_text += f"{i}. {hint}\n"

        # Display results
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(1.0, results_text)
        self.results_text.config(state=tk.DISABLED)

        # Switch to results tab
        self.notebook.select(self.results_frame)

    def display_error(self, error_msg: str):
        """Display an error message"""
        self.test_button.config(state=tk.NORMAL, text="Test Solution")
        messagebox.showerror("Error", f"An error occurred while testing:\n{error_msg}")

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
            messagebox.showwarning("Warning", "Please select a level first!")
            return

        # This is just a placeholder - in a real implementation,
        # you might have example solutions stored
        example_code = "% Your Prolog code goes here\n% Implement the required predicates\n\n"

        if self.current_level.id == "basic_eligibility":
            example_code = """% Student meal subsidy implementation
eligible(Person) :-
    student(Person),
    age(Person, Age),
    Age < 25.

subsidy_amount(Person, Amount) :-
    eligible(Person),
    income(Person, low),
    Amount = 80.

subsidy_amount(Person, Amount) :-
    eligible(Person),
    \\+ income(Person, low),
    Amount = 50."""

        self.code_text.delete(1.0, tk.END)
        self.code_text.insert(1.0, example_code)

    def load_levels_directory(self):
        """Load levels from a different directory"""
        directory = filedialog.askdirectory(title="Select Levels Directory")
        if directory:
            self.levels_directory = directory
            try:
                self.levels = LevelLoader.load_levels_from_directory(directory)
                self.populate_level_list()
                self.status_label.config(text=f"Loaded {len(self.levels)} levels from {directory}")

                # Load first level if available
                if self.levels:
                    self.load_level(0)

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load levels from {directory}:\n{e}")

    def refresh_levels(self):
        """Refresh levels from current directory"""
        try:
            self.levels = LevelLoader.load_levels_from_directory(self.levels_directory)
            self.populate_level_list()
            self.status_label.config(text=f"Refreshed {len(self.levels)} levels")

            # Reload current level if it still exists
            if (self.current_level and
                    self.current_level_index < len(self.levels) and
                    self.levels[self.current_level_index].id == self.current_level.id):
                self.load_level(self.current_level_index)
            elif self.levels:
                self.load_level(0)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh levels:\n{e}")

    def show_about(self):
        """Show about dialog"""
        about_text = """Law Maker - Solarfurt Legal System

A Prolog programming game where you implement laws 
for the fictional city-state of Solarfurt.

Features:
• Multiple levels with increasing difficulty
• File-based level configuration
• Interactive GUI with tabbed interface
• Real-time Prolog testing using SWI-Prolog
• Hints and detailed feedback

Requirements:
• Python 3.6+
• SWI-Prolog (for testing solutions)
• tkinter (usually included with Python)

Created for educational purposes to teach 
Prolog programming and logical reasoning.
"""
        messagebox.showinfo("About Law Maker", about_text)

    def run(self):
        """Start the GUI application"""
        self.root.mainloop()


def create_sample_levels():
    """Create sample level files in the levels directory"""
    levels_dir = "levels"
    LevelLoader.create_sample_levels(levels_dir)
    print(f"Sample levels created in '{levels_dir}' directory")

    # Also create a README file
    readme_content = """# Law Maker Levels

This directory contains level configuration files for the Law Maker game.

## File Format

Each level is stored as a JSON file with the following structure:

```json
{
  "id": "unique_level_identifier",
  "title": "Level Title",
  "description": "Brief description",
  "background_story": "Story context for the level",
  "given_facts": "Prolog facts that are already provided",
  "law_description": "Description of the law to implement",
  "queries": [
    {
      "query": "prolog_query(X)",
      "expected": ["expected", "results"],
      "description": "Optional description of what this query tests"
    }
  ],
  "hints": [
    "Optional hint 1",
    "Optional hint 2"
  ],
  "difficulty": 1
}
```

## Adding New Levels

1. Create a new JSON file in this directory
2. Follow the naming convention: `XX_level_name.json` (where XX is a number)
3. Use the structure shown above
4. Restart the game or use "Refresh Levels" to load your new level

## Tips for Level Design

- Start with simple concepts and gradually increase complexity
- Provide clear, engaging background stories
- Include comprehensive test queries that cover edge cases
- Add helpful hints for when users get stuck
- Test your levels thoroughly before sharing
"""

    with open(os.path.join(levels_dir, "README.md"), 'w') as f:
        f.write(readme_content)


def main():
    """Main entry point"""
    # Create sample levels if they don't exist
    if not os.path.exists("levels") or not os.listdir("levels"):
        print("Creating sample levels...")
        create_sample_levels()

    # Start the GUI
    try:
        app = LawMakerGUI()
        app.run()
    except KeyboardInterrupt:
        print("\nGame interrupted. Thank you for playing Law Maker!")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()