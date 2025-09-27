#!/usr/bin/env python3
"""
Law Maker - A Prolog Programming Game

A game where players implement laws in Prolog for the fictional city-state of Solarfurt.
Players are given facts, rules, and expected query results, then must write Prolog code
to correctly implement the law.
"""

import os
import tempfile
import subprocess
import json
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class GameResult(Enum):
    SUCCESS = "success"
    SYNTAX_ERROR = "syntax_error"
    WRONG_RESULTS = "wrong_results"
    PROLOG_ERROR = "prolog_error"


@dataclass
class Query:
    """Represents a Prolog query with expected results"""
    query: str
    expected: List[str]  # Expected solutions
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


class LawMakerGame:
    """Main game class"""

    def __init__(self):
        self.prolog_runner = PrologRunner()
        self.levels = self._create_levels()
        self.current_level = 0

    def _create_levels(self) -> List[Level]:
        """Create game levels"""
        levels = []

        # Level 1: Basic eligibility
        level1 = Level(
            id="basic_eligibility",
            title="Student Meal Subsidy Law",
            description="Implement the new student meal subsidy law for Solarfurt",
            background_story="""
Welcome to Solarfurt, civil servant! The city council has just passed the Student Meal 
Subsidy Law. Your job is to implement this law in our legal database system (Prolog).

The law is simple: students who are under 25 years old and have low income are eligible 
for meal subsidies. Students get 50 credits per month, and low-income students get an 
additional 30 credits bonus.
            """,
            given_facts="""
% Citizens of Solarfurt
person(alice).
person(bob).
person(charlie).
person(diana).

% Personal information
age(alice, 22).
age(bob, 26).
age(charlie, 19).
age(diana, 23).

income(alice, low).
income(bob, medium).
income(charlie, low).
income(diana, high).

student(alice).
student(charlie).
student(diana).
            """,
            law_description="""
Student Meal Subsidy Law:
1. A person is eligible for meal subsidy if they are a student AND under 25 years old
2. Base subsidy amount is 50 credits per month for eligible students
3. Low-income eligible students receive an additional 30 credits bonus (total 80 credits)
4. You need to implement predicates: eligible(Person) and subsidy_amount(Person, Amount)
            """,
            queries=[
                Query("eligible(X)", ["alice", "charlie"], "Who is eligible for subsidies?"),
                Query("subsidy_amount(alice, Amount)", ["80"], "Alice's subsidy amount"),
                Query("subsidy_amount(charlie, Amount)", ["80"], "Charlie's subsidy amount"),
                Query("subsidy_amount(diana, Amount)", ["false"], "Diana should not get subsidy"),
            ],
            hints=[
                "Remember to check both student status AND age",
                "Use the 'income(Person, low)' fact to determine bonus eligibility",
                "If someone is not eligible, subsidy_amount should fail (return false)"
            ]
        )
        levels.append(level1)

        # Level 2: More complex rules
        level2 = Level(
            id="parking_permits",
            title="Parking Permit Regulation",
            description="Implement the new parking permit system for Solarfurt",
            background_story="""
The Solarfurt Traffic Department needs you to implement the new parking permit system.
Different types of residents get different parking privileges based on their circumstances.
            """,
            given_facts="""
% Residents
person(emma).
person(frank).
person(grace).
person(henry).

% Residential status
resident_type(emma, senior).
resident_type(frank, disabled).
resident_type(grace, regular).
resident_type(henry, student).

% Vehicle information
owns_car(emma).
owns_car(frank).
owns_car(grace).

% District information  
lives_in_district(emma, downtown).
lives_in_district(frank, suburbs).
lives_in_district(grace, downtown).
lives_in_district(henry, downtown).
            """,
            law_description="""
Parking Permit Law:
1. All car owners who are residents get a basic parking permit
2. Senior citizens get free permits (cost: 0)
3. Disabled residents get free permits (cost: 0)  
4. Students get discounted permits (cost: 25)
5. Regular residents pay full price (cost: 100)
6. Downtown residents pay an additional 20 district fee (unless free permit)

Implement: has_permit(Person) and permit_cost(Person, Cost)
            """,
            queries=[
                Query("has_permit(X)", ["emma", "frank", "grace"], "Who has parking permits?"),
                Query("permit_cost(emma, Cost)", ["20"], "Emma's permit cost (senior + downtown)"),
                Query("permit_cost(frank, Cost)", ["0"], "Frank's permit cost (disabled)"),
                Query("permit_cost(grace, Cost)", ["120"], "Grace's permit cost (regular + downtown)"),
                Query("permit_cost(henry, Cost)", ["false"], "Henry doesn't own a car"),
            ],
            hints=[
                "Only car owners can get permits",
                "Check resident_type for special pricing",
                "Downtown district fee applies to non-free permits"
            ],
            difficulty=2
        )
        levels.append(level2)

        return levels

    def display_level(self, level: Level):
        """Display level information"""
        print(f"\n{'=' * 60}")
        print(f"LEVEL {self.current_level + 1}: {level.title}")
        print(f"{'=' * 60}")
        print(f"\nBackground:")
        print(level.background_story)
        print(f"\nGiven Facts (already in the system):")
        print(level.given_facts)
        print(f"\nLaw to Implement:")
        print(level.law_description)
        print(f"\nTest Queries (your implementation should satisfy these):")
        for i, query in enumerate(level.queries, 1):
            print(f"{i}. Query: {query.query}")
            print(f"   Expected: {query.expected}")
            if query.description:
                print(f"   ({query.description})")

        if level.hints:
            print(f"\nHints:")
            for i, hint in enumerate(level.hints, 1):
                print(f"{i}. {hint}")

    def get_user_code(self) -> str:
        """Get Prolog code from user"""
        print(f"\n{'*' * 60}")
        print("Enter your Prolog implementation below.")
        print("Type 'END' on a new line when finished:")
        print("*" * 60)

        lines = []
        while True:
            try:
                line = input()
                if line.strip() == 'END':
                    break
                lines.append(line)
            except EOFError:
                break

        return '\n'.join(lines)

    def check_solution(self, level: Level, user_code: str) -> Tuple[GameResult, Dict]:
        """Check if user's solution is correct"""
        # Combine given facts with user code
        full_code = level.given_facts + '\n' + user_code

        result, details = self.prolog_runner.run_queries(full_code, level.queries)
        return result, details

    def display_results(self, result: GameResult, details: Dict):
        """Display test results"""
        print(f"\n{'=' * 60}")
        print("TEST RESULTS")
        print(f"{'=' * 60}")

        if result == GameResult.SUCCESS:
            print("🎉 CONGRATULATIONS! Your implementation is correct!")
            print("All test queries passed!")
        elif result == GameResult.PROLOG_ERROR:
            print("❌ Prolog Error:")
            print(details.get('error', 'Unknown error'))
        elif result == GameResult.WRONG_RESULTS:
            print("❌ Some queries failed:")
            for query_id, query_result in details.items():
                if query_id.startswith('query_'):
                    print(f"\nQuery: {query_result['query']}")
                    print(f"Expected: {query_result['expected']}")
                    print(f"Got: {query_result['actual']}")
                    if query_result['correct']:
                        print("✅ PASSED")
                    else:
                        print("❌ FAILED")
                        if 'error' in query_result:
                            print(f"Error: {query_result['error']}")

    def play_level(self, level_index: int) -> bool:
        """Play a specific level, return True if completed"""
        if level_index >= len(self.levels):
            print("No more levels!")
            return False

        level = self.levels[level_index]
        self.display_level(level)

        max_attempts = 3
        for attempt in range(max_attempts):
            print(f"\nAttempt {attempt + 1} of {max_attempts}")
            user_code = self.get_user_code()

            if not user_code.strip():
                print("No code entered!")
                continue

            result, details = self.check_solution(level, user_code)
            self.display_results(result, details)

            if result == GameResult.SUCCESS:
                return True
            elif attempt < max_attempts - 1:
                print(f"\nTry again! {max_attempts - attempt - 1} attempts remaining.")

                # Show hints after first failure
                if attempt == 0 and level.hints:
                    print("\nHere are some hints to help you:")
                    for i, hint in enumerate(level.hints, 1):
                        print(f"{i}. {hint}")

        print("\nOut of attempts! Moving to next level...")
        return False

    def play(self):
        """Main game loop"""
        print("""
╔═══════════════════════════════════════════════════════════════╗
║                          LAW MAKER                            ║
║                    Solarfurt Legal System                     ║
╠═══════════════════════════════════════════════════════════════╣
║  Implement laws in Prolog for the city-state of Solarfurt!   ║
║  You are a civil servant tasked with encoding new laws       ║
║  into our legal database system.                             ║
╚═══════════════════════════════════════════════════════════════╝
        """)

        if not self.prolog_runner.prolog_available:
            print("""
⚠️  WARNING: SWI-Prolog not found!

To play this game, you need SWI-Prolog installed:
- Ubuntu/Debian: sudo apt-get install swi-prolog
- MacOS: brew install swi-prolog
- Windows: Download from https://www.swi-prolog.org/

The game will still show you the challenges, but cannot test your solutions.
            """)
            input("Press Enter to continue anyway...")

        completed_levels = 0

        while self.current_level < len(self.levels):
            success = self.play_level(self.current_level)
            if success:
                completed_levels += 1
                print(f"\n🌟 Level {self.current_level + 1} completed!")

            self.current_level += 1

            if self.current_level < len(self.levels):
                input(f"\nPress Enter to continue to Level {self.current_level + 1}...")

        # Game complete
        print(f"""
╔═══════════════════════════════════════════════════════════════╗
║                       GAME COMPLETE!                         ║
╠═══════════════════════════════════════════════════════════════╣
║  You completed {completed_levels} out of {len(self.levels)} levels successfully!     ║
║                                                               ║
║  Thank you for serving the city-state of Solarfurt!         ║
║  Your Prolog skills have helped implement important laws     ║
║  that will benefit all citizens.                             ║
╚═══════════════════════════════════════════════════════════════╝
        """)


def main():
    """Main entry point"""
    game = LawMakerGame()

    try:
        game.play()
    except KeyboardInterrupt:
        print("\n\nGame interrupted. Thank you for playing Law Maker!")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please report this issue!")


if __name__ == "__main__":
    main()