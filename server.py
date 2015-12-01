#!/usr/bin/python2.7
import json
import sqlite3
import sys
#import word2vec
from flask import Flask, request, abort, redirect, url_for, g, send_file
from collections import OrderedDict
from collections import defaultdict

# to install metamind api
# run the command: pip install MetaMindApi --upgrade
from metamind.api import ClassificationData, ClassificationModel, set_api_key

app = Flask(__name__, static_url_path='')

#set info for metamind
set_api_key('asAj55GwZA6r4nO9ijVGWxhbHWHuGVFcUkfxo8b8Tq6aLHqOCH')
classifier = ClassificationModel(id='40466')

ingredientsToRecipes = {}
recipeData = {}

# Executes a SQL query and returns a list of dictionaries (of each result row)
# Source: http://kevcoxe.github.io/Simple-Flask-App/
def queryDb(conn, query, args=(), one=False):
    cur = conn.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv


def getRecipes(userIngredients):
    # {recipeId: weight}
    matches = defaultdict(int)

    # Find all matches
    for ingredient in userIngredients:
        # Find all recipe IDs with each ingredient
        # WARNING: Prone to SQL injections, should definitely fix this
        results = queryDb(g.db, "select id from recipes where ingredients like '%%%s%%'" % ingredient)

        # Keep track of ingredient occurances by weight
        for row in results:
            recipeId = int(row['id'])
            matches[recipeId] += 1

    # Sort matches by weight (largest weight first)
    sortedMatches = OrderedDict(sorted(matches.items(), key=lambda x: x[1], reverse=True))

    # Build return object
    results = []
    i = 0
    for key, value in sortedMatches.items():
        i += 1
        result = recipeData[key]
        result['id'] = key
        result['weight'] = value
        results.append(result)
        if i >= 15:
            break

    return json.dumps(results)


def imagesToText(imageUrls):
    # Call metamind API to return image classifications from URLs
    metamindResults = classifier.predict(imageUrls, input_type='urls')

    ingredients = []
    for result in metamindResults:
        ingredients.append(result['label'])

    return ingredients


@app.route('/')
def index():
    return send_file('index.html')

@app.route('/version')
def version():
    return 'Recipe backend v0.7'

"""
Our magic API call.
Input: Image URLs of ingredients
Output: Recipes that require those ingredients, sorted by relevance

Example:
    /predict?ingredients=['http://pngimg.com/upload/egg_PNG25.png','https://upload.wikimedia.org/wikipedia/commons/7/78/Salt_shaker_on_white_background.jpg']
"""
@app.route('/predict', methods=['POST', 'GET'])
def predict():
    # Gets image URLs from user request
    imageUrls = []
    if request.method == 'POST':
        for key, value in request.form.items():
            if key.startswith('ingredient') and value:
                imageUrls.append(value)
    else:
        imageUrls = json.loads(request.args['ingredients'])

    # Convert image URLs to ingredient names
    ingredients = imagesToText(imageUrls)

    # Search for recipes with the ingredient names
    return getRecipes(ingredients)

"""
Route to handle converting images of ingredients to ingredient names.
"""
@app.route('/images_to_text', methods=['POST', 'GET'])
def imagesToTextHandler():
    # Gets image URLs from user request
    imageUrls = []
    if request.method == 'POST':
        for key, value in request.form.items():
            if key.startswith('ingredient') and value:
                imageUrls.append(value)
    else:
        imageUrls = json.loads(request.args['ingredients'])

    # Magic happens
    ingredients = imagesToText(imageUrls)

    return json.dumps(ingredients)

"""
Query the database for a list of recipe IDs and names.
Input: Ingredient names in a JSON array
Output: JSON array of objects, each with a recipe ID, name, and ingredients

Example:
    /query?ingredients=['sugar', 'milk', 'eggs']
"""

@app.route('/query', methods=['GET'])
def query():
    userIngredients = json.loads(request.args['ingredients'])
    return getRecipes(userIngredients)



"""
Query the database for a recipe's memo data, which contains the steps to make the recipe.
Input: ID of recipe
Output: JSON object of recipe, which includes name, ingredients, and memo data

Example:
    /get_recipe?id=42
"""
@app.route('/get_recipe', methods=['GET'])
def getRecipe():
    data = ''
    try:
        idval = int(request.args.get('id'))
        results = queryDb(g.db, 'SELECT memo FROM recipes WHERE id=?', (idval,))
        if len(results) >= 1:
            obj = recipeData[idval]
            obj['memo'] = results[0]['memo']
            obj['id'] = idval
            data = json.dumps(obj)
    except ValueError:
        pass
    return data



"""
Ask the server for all ingredients found in the database.
Output: JSON array of ingredients

Example:
    /get_ingredients
"""
@app.route('/get_ingredients', methods=['GET'])
def getIngredients():
    ingredientList = sorted(list(ingredientsToRecipes.keys()))
    return json.dumps(ingredientList)



@app.before_request
def before_request():
    g.db = sqlite3.connect('recipes.db')

@app.after_request
def after_request(response):
    g.db.close()
    return response

def buildIndex():
    conn = sqlite3.connect('recipes.db')
    results = queryDb(conn, 'SELECT id, name, ingredients FROM recipes')

    for row in results:
        recipeId = int(row['id'])

        # Update ingredients to recipes dictionary
        ingredientList = sorted(list(set(row['ingredients'].split('|'))))
        for ingredient in ingredientList:
            if ingredient not in ingredientsToRecipes:
                ingredientsToRecipes[ingredient] = []
            ingredientsToRecipes[ingredient].append(recipeId)

        # Update recipe metadata dictionary
        recipeData[recipeId] = {'name': row['name'], 'ingredients': ingredientList}

    conn.close()

if __name__ == '__main__':
    buildIndex()
    app.run(debug=True, port=80, host='0.0.0.0')
