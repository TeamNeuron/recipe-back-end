#!/usr/bin/python3
import json
import sqlite3
import sys
#import word2vec
from flask import Flask, request, abort, redirect, url_for, g

app = Flask(__name__)

# Executes a SQL query and returns a list of dictionaries (of each result row)
# Source: http://kevcoxe.github.io/Simple-Flask-App/
def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv



@app.route('/')
def version():
    return 'Recipe backend v0.2'



"""
Query the database for a list of recipe IDs and names.
Input: Ingredient names in a JSON array
Output: JSON array of objects, each with a recipe ID, name, and ingredients

Example:
    /query?ingredients=['sugar', 'milk', 'eggs']
"""
@app.route('/query', methods=['GET'])
def query():
    s = ''
    for key, value in request.args.items():
        s += '{} => {}<br>'.format(key, value)
    return s



"""
Query the database for a recipe's memo data, which contains the steps to make the recipe.
Input: ID of recipe
Output: Recipe memo field

Example:
    /get_recipe?id=42
"""
@app.route('/get_recipe', methods=['GET'])
def getRecipe():
    data = ''
    idval = request.args.get('id')
    if idval:
        results = query_db('SELECT * FROM recipes WHERE id=?', (idval,))
        if len(results) >= 1:
            results[0]['ingredients'] = results[0]['ingredients'].split('|')
        data = json.dumps(results)
    return data



@app.before_request
def before_request():
    g.db = sqlite3.connect('recipes.db')

@app.after_request
def after_request(response):
    g.db.close()
    return response

if __name__ == '__main__':
    # Ensure Python 3 is being used
    if sys.version_info[0] == 3:
        app.run(debug=True, port=4242, host='0.0.0.0')
    else:
        print('Error: Must be running Python 3')
