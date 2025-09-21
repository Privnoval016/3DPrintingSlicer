import numpy as np


class GCodeOp:
    def __init__(self, cmd, args):
        self.cmd = cmd
        self.args = args
        self.isMoving = False
        self.end_pos = np.zeros(3)
        self.next_filament_height = 0
        self.next_is_absolute = True
        self.reset_pos = None
        self.next_feedrate = 0

        self.cmds = {
            'G0': self.handle_g0,   # Rapid linear move
            'G1': self.handle_g1,   # Linear move
            'G28': self.handle_g28, # Move to home position
            'G90': self.handle_g90, # Set to absolute positioning
            'G91': self.handle_g91, # Set to relative positioning
            'G92': self.handle_g92, # Change position without moving
        }


    def execute(self, current_state):
        self.next_is_absolute = current_state.is_absolute
        self.next_feedrate = current_state.current_feedrate
        self.next_filament_height = current_state.filament_height
        self.end_pos = np.copy(current_state.actual_position)

        if self.cmd in self.cmds:
            self.cmds[self.cmd]()


    def handle_g0(self):
        self.isMoving = True

        for param in self.args:
            if param[0] == 'X':
                self.end_pos[0] = float(param[1:])
            if param[0] == 'Y':
                self.end_pos[1] = float(param[1:])
            if param[0] == 'Z':
                self.end_pos[2] = float(param[1:])

            if param[0] == 'F':
                self.next_feedrate = float(param[1:])
            if param[0] == 'E':
                self.next_filament_height = float(param[1:])


    def handle_g1(self):
        self.isMoving = True

        for param in self.args:
            if param[0] == 'X':
                self.end_pos[0] = float(param[1:])
            if param[0] == 'Y':
                self.end_pos[1] = float(param[1:])
            if param[0] == 'Z':
                self.end_pos[2] = float(param[1:])

            if param[0] == 'F':
                self.next_feedrate = float(param[1:])
            if param[0] == 'E':
                self.next_filament_height = float(param[1:])

    def handle_g28(self):
        self.isTeleport = True

        if len(self.args) == 0:
            self.end_pos = np.zeros(3)
            return

        for param in self.args:
            if param[0] == 'X':
                self.end_pos[0] = 0
            if param[0] == 'Y':
                self.end_pos[1] = 0
            if param[0] == 'Z':
                self.end_pos[2] = 0


    def handle_g90(self):
        self.next_is_absolute = True


    def handle_g91(self):
        self.next_is_absolute = False


    def handle_g92(self):

        for param in self.args:
            if param[0] == 'X':
                self.reset_pos[0] = float(param[1:])
            if param[0] == 'Y':
                self.reset_pos[1] = float(param[1:])
            if param[0] == 'Z':
                self.reset_pos[2] = float(param[1:])

            if param[0] == 'E':
                self.next_filament_height = float(param[1:])