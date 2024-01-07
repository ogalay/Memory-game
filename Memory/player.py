class Player:

    def __init__(self):
        self.score = 0
        self.can_play = True

    def reset_score(self):
        self.score = 0

    def increment_score(self):
        self.score += 1
