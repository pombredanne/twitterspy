from collections import deque
import random

from twisted.python import log

import protocol

MAX_RESULTS = 1000

class Moodiness(object):

    MOOD_CHOICES=[
        (0.9, ('happy', 'humbled')),
        (0.5, ('frustrated', 'annoyed', 'anxious', 'grumpy')),
        (0.1, ('annoyed', 'dismayed', 'depressed', 'worried')),
        (float('-inf'), ('angry', 'cranky', 'disappointed'))
        ]

    def __init__(self):
        self.recent_results = deque()
        self.previous_good = (0, 0)

    def current_mood(self):
        """Get the current mood (good, total, percentage)"""
        if not self.recent_results:
            log.msg("Short-circuiting tally results since there aren't any.")
            return None, None, None
        good = reduce(lambda x, y: x + 1 if y else x, self.recent_results)
        total = len(self.recent_results)
        percentage = float(good) / float(total)

        return good, total, percentage

    def __call__(self):
        # Short-circuit no results
        good, total, percentage = self.current_mood()
        if total is None:
            return
        msg = ("Processed %d out of %d recent searches (previously %d/%d)."
            % (good, total, self.previous_good[0], self.previous_good[1]))
        choices=[v for a,v in self.MOOD_CHOICES if percentage >= a][0]
        mood=random.choice(choices)

        self.previous_good = (good, total)

        log.msg(msg + " my mood is " + mood)
        conn = protocol.current_conn
        if conn:
            conn.publish_mood(mood, msg)

    def add(self, result):
        if len(self.recent_results) >= MAX_RESULTS:
            self.recent_results.popleft()
        self.recent_results.append(result)

moodiness = Moodiness()
