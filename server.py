#!/usr/bin/python3
import json
import sqlite3
import sys
#import word2vec
from flask import Flask, request, abort, redirect, url_for, g
from collections import OrderedDict

# to install metamind api
# run the command: pip install MetaMindApi --upgrade
from metamind.api import ClassificationData, ClassificationModel, set_api_key

app = Flask(__name__)

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


@app.route('/')
def version():
    return 'Recipe backend v0.6'

@app.route('/predict', methods=['POST'])
def predict():
    # Gets image URLs from user request
    imageUrls = []
    for key, value in request.form.items():
        if key.startswith('ingredient') and value:
            imageUrls.append(value)

    print 'imageUrls: {}'.format(imageUrls)

    # TODO: change request.args function
    # imageUrls = json.loads(request.args['urls'])
    list_results = classifier.predict(imageUrls, input_type='urls')

    print 'list_results: {}'.format(list_results)

    ingredients = []
    for result in list_results:
        ingredients.append(result['label'])

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
    # Find all matches
    matches = []
    userIngredients = json.loads(request.args['ingredients'])
    for ingredient in userIngredients:
        if ingredient in ingredientsToRecipes:
            matches += ingredientsToRecipes[ingredient]

    #add matches to dict. key is id, value is # times matched
    weighted_matches = {}
    for match in matches:
        if match in weighted_matches:
            weighted_matches[match] += 1
        else:
            weighted_matches[match] = 1

    #sort weighted_matches by values high to low
    sorted_matches = OrderedDict(sorted(weighted_matches.items(), key=lambda x: x[1], reverse=True))

    # Build return object
    results = []
    i = 0
    for key, value in sorted_matches.items():
        i += 1
        match = key
        result = recipeData[match]
        result['id'] = match
        results.append(result)
        if i >= 15:
            break

    return json.dumps(results)



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
    app.run(debug=True, port=4242, host='0.0.0.0')
