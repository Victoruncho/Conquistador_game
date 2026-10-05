import json

from django.shortcuts import render

from .models import Category, ChoiceQuestion, NumericQuestion


def question_ui(request):
    categories = Category.objects.prefetch_related('choicequestion_set', 'numericquestion_set').all()
    questions = []

    for category in categories:
        for question in category.choicequestion_set.all():
            questions.append({
                'id': f'choice-{question.pk}',
                'type': 'choice',
                'category': category.name,
                'text': question.text,
                'options': [
                    {'id': option.pk, 'text': option.text, 'is_correct': option.is_correct}
                    for option in question.answer_options.all()
                ],
                'correct_answer': question.answer_options.filter(is_correct=True).first().text if question.answer_options.filter(is_correct=True).exists() else None,
            })

        for question in category.numericquestion_set.all():
            questions.append({
                'id': f'numeric-{question.pk}',
                'type': 'numeric',
                'category': category.name,
                'text': question.text,
                'correct_answer': question.correct_answer,
            })

    context = {
        'questions_json': json.dumps(questions, ensure_ascii=False),
    }
    return render(request, 'question_ui.html', context)
