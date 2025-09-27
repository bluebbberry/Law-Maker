import pygame
import sys
import re
from typing import Dict, List, Tuple, Optional


# Simple Prolog engine for the reality machine
class PrologEngine:
    def __init__(self):
        self.facts = []
        self.rules = []
        self.reality_state = {
            'door_locked': True,
            'machine_active': False,
            'tentacle_visible': False,
            'ada_location': 'lab',
            'world_stability': 100
        }

    def add_fact(self, fact: str):
        """Add a fact to the knowledge base"""
        if fact not in self.facts:
            self.facts.append(fact)
            self._update_reality(fact)

    def add_rule(self, rule: str):
        """Add a rule to the knowledge base"""
        if rule not in self.rules:
            self.rules.append(rule)

    def query(self, query: str) -> bool:
        """Simple query resolution"""
        # Direct fact lookup
        if query in self.facts:
            return True

        # Simple rule resolution (basic pattern matching)
        for rule in self.rules:
            if ':-' in rule:
                head, body = rule.split(':-')
                head = head.strip()
                if head == query:
                    # Check if all conditions in body are satisfied
                    conditions = [c.strip() for c in body.split(',')]
                    if all(self.query(cond) for cond in conditions):
                        return True

        return False

    def _update_reality(self, fact: str):
        """Update the reality state based on new facts"""
        if fact == "door_unlocked":
            self.reality_state['door_locked'] = False
        elif fact == "machine_activated":
            self.reality_state['machine_active'] = True
        elif fact == "eldritch_summoned":
            self.reality_state['tentacle_visible'] = True
            self.reality_state['world_stability'] -= 30
        elif fact == "reality_stabilized":
            self.reality_state['world_stability'] = min(100, self.reality_state['world_stability'] + 50)

    def execute_prolog(self, code: str) -> Tuple[bool, str]:
        """Execute Prolog code and return success status and message"""
        try:
            lines = [line.strip() for line in code.split('\n') if line.strip()]

            for line in lines:
                if line.endswith('.'):
                    line = line[:-1]  # Remove trailing dot

                if ':-' in line:
                    self.add_rule(line)
                else:
                    self.add_fact(line)

            return True, "Reality manipulation successful."

        except Exception as e:
            self.reality_state['world_stability'] -= 10
            return False, f"Reality glitch: {str(e)}"


class GameState:
    def __init__(self):
        self.current_scene = "lab"
        self.inventory = []
        self.prolog_engine = PrologEngine()
        self.dialogue_state = 0
        self.game_complete = False
        self.prolog_terminal_open = False
        self.terminal_code = ""
        self.terminal_output = ""


class GameObject:
    def __init__(self, name: str, x: int, y: int, width: int, height: int,
                 description: str, clickable: bool = True):
        self.name = name
        self.rect = pygame.Rect(x, y, width, height)
        self.description = description
        self.clickable = clickable
        self.visible = True


class Scene:
    def __init__(self, name: str, background_color: Tuple[int, int, int],
                 description: str):
        self.name = name
        self.background_color = background_color
        self.description = description
        self.objects = []
        self.exits = {}

    def add_object(self, obj: GameObject):
        self.objects.append(obj)

    def add_exit(self, direction: str, target_scene: str, condition=None):
        self.exits[direction] = {'target': target_scene, 'condition': condition}


class WittgensteinGame:
    def __init__(self):
        pygame.init()
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Wittgenstein")

        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        self.large_font = pygame.font.Font(None, 32)

        self.game_state = GameState()
        self.scenes = {}
        self.current_text = ""
        self.text_timer = 0

        self._setup_scenes()
        self._setup_initial_prolog_facts()

        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GREEN = (0, 255, 0)
        self.RED = (255, 0, 0)
        self.GRAY = (128, 128, 128)
        self.DARK_GREEN = (0, 100, 0)
        self.PURPLE = (128, 0, 128)

    def _setup_initial_prolog_facts(self):
        """Setup initial Prolog facts about the world"""
        engine = self.game_state.prolog_engine
        engine.add_fact("ada_engineer")
        engine.add_fact("machine_exists")
        engine.add_fact("world_in_danger")
        engine.add_rule("door_unlocked :- machine_activated, ada_engineer")
        engine.add_rule("world_saved :- reality_stabilized, eldritch_banished")

    def _setup_scenes(self):
        # Laboratory scene
        lab = Scene("lab", (20, 20, 40),
                    "A cramped laboratory filled with incomprehensible machinery. The air hums with potential.")

        # Reality Machine
        machine = GameObject("machine", 300, 200, 200, 150,
                             "The Reality Machine - a writhing mass of cables and screens that hurt to look at directly.")
        lab.add_object(machine)

        # Terminal
        terminal = GameObject("terminal", 100, 300, 150, 100,
                              "A terminal connected to the Reality Machine. Prolog code flows across its screen.")
        lab.add_object(terminal)

        # Door
        door = GameObject("door", 50, 100, 60, 120,
                          "A heavy door leading to the outside world. Currently locked.")
        lab.add_object(door)

        # Notes
        notes = GameObject("notes", 500, 400, 100, 50,
                           "Research notes scattered on the desk. They speak of 'linguistic reality manipulation'.")
        lab.add_object(notes)

        self.scenes["lab"] = lab

        # Outside scene (unlocked later)
        outside = Scene("outside", (40, 20, 60),
                        "The world outside writhes with impossible geometry. Reality is breaking down.")

        # Eldritch tentacle (appears when summoned)
        tentacle = GameObject("tentacle", 200, 100, 400, 300,
                              "A massive tentacle tears through reality itself. It pulses with malevolent intelligence.")
        tentacle.visible = False
        outside.add_object(tentacle)

        # Portal
        portal = GameObject("portal", 600, 200, 100, 150,
                            "A shimmering portal to somewhere else. Or somewhen else.")
        outside.add_object(portal)

        self.scenes["outside"] = outside

    def handle_click(self, pos: Tuple[int, int]):
        """Handle mouse clicks on game objects"""
        current_scene = self.scenes[self.game_state.current_scene]

        for obj in current_scene.objects:
            if obj.clickable and obj.visible and obj.rect.collidepoint(pos):
                self._handle_object_interaction(obj)
                return

    def _handle_object_interaction(self, obj: GameObject):
        """Handle interaction with clicked objects"""
        if obj.name == "terminal":
            self.game_state.prolog_terminal_open = True
            self.current_text = "Reality Machine Terminal Online. Enter Prolog code to manipulate reality..."

        elif obj.name == "machine":
            if self.game_state.prolog_engine.reality_state['machine_active']:
                self.current_text = "The machine hums with eldritch energy. Reality bends around it."
            else:
                self.current_text = "The machine is dormant. Perhaps the terminal can activate it..."

        elif obj.name == "door":
            if self.game_state.prolog_engine.reality_state['door_locked']:
                self.current_text = "The door is locked. Ada thinks: 'Typical. Even doors conspire against me.'"
            else:
                self.game_state.current_scene = "outside"
                self.current_text = "Ada steps outside into a world gone mad..."

        elif obj.name == "notes":
            self.current_text = "The notes describe Prolog predicates for reality manipulation:\n" + \
                                "machine_activated - Powers the reality engine\n" + \
                                "eldritch_summoned - Calls forth cosmic horrors\n" + \
                                "reality_stabilized - Attempts to fix everything"

        elif obj.name == "tentacle":
            self.current_text = "Ada stares at the tentacle with characteristic apathy. 'Great. Tentacles. This Tuesday just keeps getting better.'"

        elif obj.name == "portal":
            if self.game_state.prolog_engine.query("world_saved"):
                self.current_text = "Ada steps through the portal. Reality stabilizes. The world is saved, probably."
                self.game_state.game_complete = True
            else:
                self.current_text = "The portal rejects Ada. The world must be stabilized first."

        self.text_timer = pygame.time.get_ticks()

    def handle_prolog_input(self, code: str):
        """Handle Prolog code input from the terminal"""
        success, message = self.game_state.prolog_engine.execute_prolog(code)

        self.game_state.terminal_output = f"> {code}\n{message}"

        # Update object visibility based on reality state
        self._update_scene_visibility()

        if not success:
            self.current_text = f"Ada winces as reality glitches. '{message}'"
        else:
            self.current_text = f"Ada nods. '{message}'"

        self.text_timer = pygame.time.get_ticks()

    def _update_scene_visibility(self):
        """Update object visibility based on current reality state"""
        reality = self.game_state.prolog_engine.reality_state

        # Update tentacle visibility in outside scene
        if "outside" in self.scenes:
            for obj in self.scenes["outside"].objects:
                if obj.name == "tentacle":
                    obj.visible = reality['tentacle_visible']

    def draw_prolog_terminal(self):
        """Draw the Prolog terminal interface"""
        if not self.game_state.prolog_terminal_open:
            return

        # Terminal background
        terminal_rect = pygame.Rect(50, 100, 700, 400)
        pygame.draw.rect(self.screen, self.BLACK, terminal_rect)
        pygame.draw.rect(self.screen, self.GREEN, terminal_rect, 2)

        # Title
        title = self.large_font.render("REALITY MANIPULATION TERMINAL", True, self.GREEN)
        self.screen.blit(title, (60, 110))

        # Reality state
        reality = self.game_state.prolog_engine.reality_state
        state_y = 150
        for key, value in reality.items():
            state_text = f"{key}: {value}"
            color = self.GREEN if isinstance(value, bool) and value else self.WHITE
            text = self.small_font.render(state_text, True, color)
            self.screen.blit(text, (60, state_y))
            state_y += 20

        # Output
        if self.game_state.terminal_output:
            output_lines = self.game_state.terminal_output.split('\n')
            output_y = 300
            for line in output_lines[-5:]:  # Show last 5 lines
                text = self.small_font.render(line, True, self.WHITE)
                self.screen.blit(text, (60, output_y))
                output_y += 20

        # Input prompt
        prompt = f"?- {self.game_state.terminal_code}_"
        prompt_text = self.font.render(prompt, True, self.GREEN)
        self.screen.blit(prompt_text, (60, 450))

        # Instructions
        instructions = "ESC: Close terminal | ENTER: Execute | Try: machine_activated. or eldritch_summoned."
        inst_text = self.small_font.render(instructions, True, self.GRAY)
        self.screen.blit(inst_text, (60, 480))

    def draw_scene(self):
        """Draw the current scene"""
        current_scene = self.scenes[self.game_state.current_scene]
        self.screen.fill(current_scene.background_color)

        # Draw objects
        for obj in current_scene.objects:
            if obj.visible:
                color = self.WHITE if obj.clickable else self.GRAY
                pygame.draw.rect(self.screen, color, obj.rect, 2)

                # Object label
                label = self.small_font.render(obj.name, True, color)
                self.screen.blit(label, (obj.rect.x, obj.rect.y - 20))

        # Scene description
        desc_text = self.font.render(current_scene.description, True, self.WHITE)
        self.screen.blit(desc_text, (10, 10))

    def draw_ui(self):
        """Draw the game UI"""
        # Current text display
        if self.current_text and pygame.time.get_ticks() - self.text_timer < 5000:
            text_lines = self.current_text.split('\n')
            text_y = self.screen_height - 120

            # Background for text
            text_bg = pygame.Rect(10, text_y - 10, self.screen_width - 20, 100)
            pygame.draw.rect(self.screen, (0, 0, 0, 128), text_bg)
            pygame.draw.rect(self.screen, self.WHITE, text_bg, 1)

            for line in text_lines:
                text_surface = self.font.render(line, True, self.WHITE)
                self.screen.blit(text_surface, (20, text_y))
                text_y += 25

        # World stability indicator
        stability = self.game_state.prolog_engine.reality_state['world_stability']
        stability_color = self.GREEN if stability > 70 else self.RED if stability < 30 else (255, 255, 0)
        stability_text = f"Reality Stability: {stability}%"
        stability_surface = self.font.render(stability_text, True, stability_color)
        self.screen.blit(stability_surface, (self.screen_width - 200, 10))

        # Instructions
        if not self.game_state.prolog_terminal_open:
            inst_text = "Click objects to interact. Use the terminal to program reality."
            inst_surface = self.small_font.render(inst_text, True, self.GRAY)
            self.screen.blit(inst_surface, (10, self.screen_height - 30))

    def handle_terminal_input(self, event):
        """Handle keyboard input for the Prolog terminal"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game_state.prolog_terminal_open = False
                self.game_state.terminal_code = ""
            elif event.key == pygame.K_RETURN:
                if self.game_state.terminal_code.strip():
                    self.handle_prolog_input(self.game_state.terminal_code)
                    self.game_state.terminal_code = ""
            elif event.key == pygame.K_BACKSPACE:
                self.game_state.terminal_code = self.game_state.terminal_code[:-1]
            else:
                if len(self.game_state.terminal_code) < 100:  # Limit input length
                    self.game_state.terminal_code += event.unicode

    def run(self):
        """Main game loop"""
        running = True

        # Opening message
        self.current_text = "Ada Wittgenstein stares at the Reality Machine. 'Another Tuesday, another existential crisis.'"
        self.text_timer = pygame.time.get_ticks()

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if not self.game_state.prolog_terminal_open:
                        self.handle_click(event.pos)

                elif self.game_state.prolog_terminal_open:
                    self.handle_terminal_input(event)

            # Check win condition
            if self.game_state.game_complete:
                self.current_text = "Ada saved the world with characteristic indifference. 'Well, that happened.'"

            # Draw everything
            self.draw_scene()
            self.draw_ui()
            self.draw_prolog_terminal()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = WittgensteinGame()
    game.run()
