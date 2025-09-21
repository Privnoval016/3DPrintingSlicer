import numpy as np

from GCode.GCodeOp import GCodeOp


class GCodeEvaluator:
    def __init__(self):
        self.file_name = ""
        self.operations = []
        self.expected_position = np.zeros(3)
        self.actual_position = np.zeros(3)
        self.current_feedrate = 0
        self.filament_height = 0
        self.is_absolute = True
        self.index = 0

    def reset(self):
        self.expected_position = np.zeros(3)
        self.actual_position = np.zeros(3)
        self.current_feedrate = 0
        self.filament_height = 0
        self.is_absolute = True
        self.index = 0

    def evaluate_command(self, cmd, args):
        operation = GCodeOp(cmd, args)
        self.operations.append(operation)

    def can_draw(self):
        return self.filament_height > 0

    def execute_next_command(self):
        if self.index >= len(self.operations):
            return None

        operation = self.operations[self.index]
        operation.execute(self)

        self.is_absolute = operation.next_is_absolute
        self.current_feedrate = operation.next_feedrate
        self.filament_height = operation.next_filament_height

        if operation.reset_pos is not None:
            self.expected_position = operation.reset_pos

        if operation.isMoving:
            if self.is_absolute:
                self.actual_position += operation.end_pos - self.expected_position
                self.expected_position = operation.end_pos
            else:
                self.actual_position += operation.end_pos
                self.expected_position += operation.end_pos


        self.index += 1


    def parse(self, file_name):

        self.file_name = file_name
        self.operations = []
        self.reset()

        with open(self.file_name, 'r') as file:
            lines = file.readlines()
            for line in lines:
                line = line.strip()
                if not line.startswith('G') or not line:
                    continue

                if ';' in line:
                    line = line.split(';')[0].strip()

                parts = line.split()

                cmd = parts[0]

                if len(parts) < 2:
                    continue

                args = parts[1:]

                self.evaluate_command(cmd, args)

        print(f"Parsed {len(self.operations)} G-code operations from {self.file_name}.")



