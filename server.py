#!/usr/bin/python3
import json
import pymysql
#import word2vec
from flask import Flask, request, abort, redirect, url_for

def connectToDatabase(config):
    with open(config) as json_file:
        data = json.load(json_file)
        return pymysql.connect(**data)
    return None

# Connect to database with configuration
conn = connectToDatabase('dbconfig.json')

app = Flask(__name__)

@app.route("/")
def version():
    return "Recipe backend v0.1"

"""
Query the database for a list of recipe IDs and names.
Input: Ingredient names in a JSON array
Output: JSON array of objects, each with a recipe ID, name, and ingredients

Example:
    /query?ingredients=['sugar', 'milk', 'eggs']
"""
@app.route("/query", methods=['GET'])
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
@app.route("/get_recipe", methods=['GET'])
def getRecipe():
    data = ''
    idval = request.args.get('id')
    if idval:
        cur = conn.cursor()
        cur.execute("SELECT name FROM test where id=%s;", (idval))
        row = cur.fetchone()
        if row:
            data = row[0]
        cur.close()
    return data

if __name__ == "__main__":
    app.run(debug=True, port=4242, host='0.0.0.0')

