import json
import os

class QuestionBank:
    def __init__(self, filepath="data/questions.json"):
        self.filepath = filepath
        self.questions = self._load_questions()

    def _load_questions(self):
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"[questions.py] Could not find questions file at {self.filepath}")

        with open(self.filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_all_questions(self):
        return self.questions

    def get_question_by_id(self, question_id):
        return next((q for q in self.questions if q["question_id"] == question_id), None)
