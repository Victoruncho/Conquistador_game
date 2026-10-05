from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from questions.models import AnswerOption, Category, ChoiceQuestion, NumericQuestion


class CategoryModelTests(TestCase):
    def test_category_name_is_unique(self):
        Category.objects.create(name='History')

        with self.assertRaises(IntegrityError):
            Category.objects.create(name='History')


class ChoiceQuestionModelTests(TestCase):
    def test_choice_question_requires_exactly_four_options(self):
        category = Category.objects.create(name='Geography')
        question = ChoiceQuestion.objects.create(category=category, text='Capital of France?')

        for index in range(3):
            AnswerOption.objects.create(question=question, text=f'Option {index + 1}', is_correct=index == 0)

        with self.assertRaises(ValidationError):
            question.clean()

    def test_choice_question_requires_exactly_one_correct_answer(self):
        category = Category.objects.create(name='Geography')
        question = ChoiceQuestion.objects.create(category=category, text='Capital of France?')

        for index in range(4):
            AnswerOption.objects.create(question=question, text=f'Option {index + 1}', is_correct=True)

        with self.assertRaises(ValidationError):
            question.clean()


class NumericQuestionModelTests(TestCase):
    def test_numeric_question_requires_correct_answer(self):
        category = Category.objects.create(name='Math')
        question = NumericQuestion(category=category, text='What is 2 + 2?', correct_answer=4)

        self.assertEqual(question.correct_answer, 4)


class AnswerOptionModelTests(TestCase):
    def test_answer_option_links_to_choice_question(self):
        category = Category.objects.create(name='Science')
        question = ChoiceQuestion.objects.create(category=category, text='Largest planet?')
        option = AnswerOption.objects.create(question=question, text='Jupiter', is_correct=True)

        self.assertEqual(option.question, question)
        self.assertTrue(option.is_correct)
