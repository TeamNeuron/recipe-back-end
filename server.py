#!/usr/bin/python3
import json
import sqlite3
import sys
#import word2vec
from flask import Flask, request, abort, redirect, url_for, g

app = Flask(__name__)

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
    return 'Recipe backend v0.4'



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
        else
            weighted_matches[match] = 1
    # TODO: sort weighted_matches by values        
    #replace matches with weighted_matches.keys() below
    
    # we only want to return the top 20% + 10 matches
    num_matches = len(weighted_matches.keys())
    if num_matches > 15:
        num_results = ( num_matches * 0.2 ) + 10
    else:
        num_results = num_matches
    
    # Build return object
    results = []
    i = 0
    while i < num_results :
        match = weighted_matches[i]
        result = recipeData[match]
        result['id'] = match
        results.append(result)
        i++
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
    # Ensure Python 3 is being used
    if sys.version_info[0] == 3:
        buildIndex()
        app.run(debug=True, port=4242, host='0.0.0.0')
    else:
        print('Error: Must be running Python 3')
