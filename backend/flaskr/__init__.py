import os
import re
from flask import Flask, request, abort, jsonify
from flask.globals import current_app
from flask.signals import request_finished
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_cors import CORS
import random
from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
    CORS(app)
    '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Headers',
                             'GET, POST, PATCH, DELETE, OPTIONS')
        return response
    '''
  @TODO:
  Create an endpoint to handle GET requests
  for all available categories.
  '''
    @app.route('/categories')
    def get_categories():
        categories = Category.query.all()
        formatted_categories = dict()
        for category in categories:
            formatted_categories[str(category.id)] = category.type

        if formatted_categories == []:
            abort(404)
        else:
            return jsonify({
                'success': True,
                'categories': formatted_categories,
                'total_categories': len(formatted_categories)
            })
    '''
  @TODO:
  Create an endpoint to handle GET requests for questions,
  including pagination (every 10 questions).
  This endpoint should return a list of questions,
  number of total questions, current category, categories.

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions.
  '''

    @app.route('/questions', methods=['GET'])
    def get_questions():
        page = request.args.get('page', 1, type=int)
        start = (page - 1) * 10
        end = start + 10
        questions = Question.query.all()
        categories = Category.query.all()
        categories_result = dict()
        for category in categories:
            categories_result[str(category.id)] = category.type

        formatted_categories = [catagory.format() for catagory in categories]
        formatted_questions = [question.format() for question in questions]
        current_categories = [int(question.format()['category'])
                              for question in questions]
        print('#' * 100)
        print(len(formatted_questions))
        print('#' * 100)
        if formatted_questions[start:end] == []:
            abort(404)
        else:
            return jsonify({
                'success': True,
                'questions': formatted_questions[start:end],
                'total_questions': len(formatted_questions),
                'categories': categories_result,
                'currentCategory': current_categories
            })

    '''
  @TODO:
  Create an endpoint to DELETE question using a question ID.

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page.
  '''
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):

        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()
            question.delete()
            return jsonify({"success": True})
        except:
            abort(404)
    '''
  @TODO:
  Create an endpoint to POST a new question,
  which will require the question and answer text,
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab,
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.
  '''

    def save_question(data):
        question = data['question']
        answer = data.get('answer')
        category = data.get('category')
        difficulty = data.get('difficulty')

        return Question(question=question, answer=answer, category=category, difficulty=difficulty)

    @app.route('/questions', methods=['POST'])
    def create_question():
        try:
            data = request.get_json()
            question = save_question(data)
            question.insert()

            return jsonify({"success": True})
        except:
            abort(405)

    '''
  @TODO:
  Create a POST endpoint to get questions based on a search term.
  It should return any questions for whom the search term
  is a substring of the question.

  TEST: Search by any phrase. The questions list will update to include
  only question that include that string within their question.
  Try using the word "title" to start.
  '''
    @app.route('/search', methods=['POST'])
    def search_questions():
        data = request.get_json()['searchTerm']
        questions = Question.query.filter(
            Question.question.ilike('%' + data + '%'))
        formatted_questions = [question.format() for question in questions]
        current_categories = [int(question.format()['category'])
                              for question in questions]

        if formatted_questions == []:
            abort(404)
        else:
            return jsonify({
                'success': True,
                'questions': formatted_questions,
                'totalQuestions': len(formatted_questions),
                'currentCategory': current_categories
            })
    '''
  @TODO:
  Create a GET endpoint to get questions based on category.

  TEST: In the "List" tab / main screen, clicking on one of the
  categories in the left column will cause only questions of that
  category to be shown.
  '''

    @app.route('/categories/<int:id_category>/questions')
    def get_questions_by_categories(id_category):
        page = request.args.get('page', 1, type=int)
        start = (page - 1) * 10
        end = start + 10
        categories = Category.query.all()
        questions = Question.query.filter(
            Question.category == id_category).all()
        categories_result = dict()
        for category in categories:
            categories_result[str(category.id)] = category.type

        formatted_questions = [question.format() for question in questions]
        current_categories = [int(question.format()['category'])
                              for question in questions]

        if formatted_questions[start:end] == []:
            abort(404)
        else:
            return jsonify({
                'success': True,
                'questions': formatted_questions[start:end],
                'totalQuestions': len(formatted_questions),
                'categories': categories_result,
                'currentCategory': current_categories
            })

    '''
  @TODO:
  Create a POST endpoint to get questions to play the quiz.
  This endpoint should take category and previous question parameters
  and return a random questions within the given category,
  if provided, and that is not one of the previous questions.

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not.
  '''

    @app.route('/quizzes', methods=['POST'])
    def play_quiz():

        data = request.get_json()
        requested_category = data.get('quiz_category')
        previous_questions = data.get('previous_questions')
        try:
            if requested_category['id'] == '0':
                random_question = Question.query.filter(
                    Question.id.notin_(previous_questions)).order_by(func.random()).first()
            else:
                random_question = Question.query.filter(
                    Question.category == requested_category['id'],
                    Question.id.notin_(previous_questions)
                ).order_by(func.random()).first()

            res = {
                'success': True
            }

            if random_question is not None:
                res['question'] = random_question.format()

            return res
        except:
            abort(404)

    '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'Resource Not Found'
        }), 404

    @app.errorhandler(422)
    def unprocessable_entity(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': 'Unprocessable Entity'
        }), 422

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'error': 405,
            'message': 'Method Not Allowed'
        }), 405

    return app
