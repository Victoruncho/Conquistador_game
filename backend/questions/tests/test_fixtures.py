import json

from django.core.management import call_command
from django.test import TestCase

from questions.models import AnswerOption, Category, ChoiceQuestion, NumericQuestion


class QuestionFixtureTests(TestCase):
    fixtures = ['questions/question_bank.json']

    def test_fixture_loads_expected_counts(self):
        self.assertEqual(Category.objects.count(), 6)
        self.assertEqual(ChoiceQuestion.objects.count(), 12)
        self.assertEqual(NumericQuestion.objects.count(), 12)
        self.assertEqual(AnswerOption.objects.count(), 48)

    def test_choice_questions_have_exactly_four_answers_and_one_correct(self):
        for question in ChoiceQuestion.objects.all():
            self.assertEqual(question.answer_options.count(), 4)
            self.assertEqual(question.answer_options.filter(is_correct=True).count(), 1)

    def test_numeric_questions_have_integer_answers(self):
        for question in NumericQuestion.objects.all():
            self.assertIsInstance(question.correct_answer, int)
