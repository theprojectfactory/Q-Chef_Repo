################################################################################
# Q-Chef Server
# Authors: Q-Chef Backend Programmers
# Updated: 20200512
# Note: Database credentials certificate path will need to be updated when run locally.
################################################################################
# Imports and application creation
################################################################################
import json
import random as rand
from flask import Flask, request, jsonify, render_template

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Use the application default credentials
cred = credentials.Certificate("/home/sandy/Documents/Q-Chef/database_keys/sandy-smiles_q-chef-back-end-firebase-adminsdk-kyeic-a3564abe5f.json")
firebase_admin.initialize_app(cred, {
  'projectId': 'q-chef-back-end',
})
db = firestore.client()

# Create a web server
app = Flask(__name__)

collectionIDs = ['users',
                 'recipes',
                 'ingredients',
                 'ingredient_clusters',
                 'ingredient_subclusters',
                 'onboarding']

userStartingDoc = {
  'i_taste' : {},
  'is_taste': {},
  'ic_taste': {},
  'r_taste' : {},
  'i_familiarity' : {},
  'is_familiarity': {},
  'ic_familiarity': {},
  'r_familiarity' : {},
}

################################################################################
# Debugging
################################################################################
DEBUG = True
WARN = True
INFO = True
DATA = True
HELP = True

def debug(fString):
  if DEBUG and 'ERROR' in fString:
    print(fString)
    return

  if DEBUG and WARN and 'WARNING' in fString:
    print(fString)
    return

  if DEBUG and INFO and 'INFO' in fString:
    print(fString)
    return

  if DEBUG and DATA and 'DATA' in fString:
    print(fString)
    return

  if DEBUG and HELP and 'HELP' in fString:
    print(fString)
    return

################################################################################
# "Database"
################################################################################
# createDocument
# Create a document within a specified document collection.
# Input:
#  - (string) collectionID <- Database collection name (ID)
#  - (string) documentID <- Database document name (ID)
#  - (dict) creationData <- Dictionary containing values to set in the doc
# Output:
#  - (string) error
def createDocument(collectionID, documentID, creationData):
  debug(f'[updateDocument - INFO]: Starting updateDocument.')

  doc_ref = db.collection(collectionID).document(documentID)
  doc_ref.set(creationData)
  doc = doc_ref.get()
  if not doc.exists:
    err = f'[retrieveDocument - ERROR]: Document {documentID} does not exist in collection {collectionID}.'
    debug(err)
    return err

  return ''

# retrieveDocument
# Retrieve a document within a specified document collection.
# Input:
#  - (string) collectionID <- Database collection name (ID)
#  - (string) documentID <- Database document name (ID)
# Output:
#  - (doc_ref) document reference
#  - (doc) document itself (if it exists)
#  - (string) error
def retrieveDocument(collectionID, documentID):
  debug(f'[retrieveDocument - INFO]: Starting retrieveDocument.')

  if not (collectionID in collectionIDs):
    err = f'[retrieveDocument - ERROR]: Collection name {collectionID} is not a known collection.'
    debug(err)
    return None, None, err

  doc_ref = db.collection(collectionID).document(documentID)
  doc = doc_ref.get()
  if not doc.exists:
    err = f'[retrieveDocument - ERROR]: Document {documentID} does not exist in collection {collectionID}.'
    debug(err)
    return None, None, err

  return doc_ref, doc, ''

# deleteDocument
# Delete a document within a specified document collection.
# Input:
#  - (string) collectionID <- Database collection name (ID)
#  - (string) documentID <- Database document name (ID)
# Output:
#  - (string) error
def deleteDocument(collectionID, documentID):
  debug(f'[deleteDocument - INFO]: Starting deleteDocument.')

  doc_ref, doc, err = retrieveDocument(databaseName, dataID)
  if err:
    err = f'[deleteDocument - ERROR]: Unable to retrieve document, err: {err}'
    debug(err)
    return err

  if not doc.exists:
    return ''

  doc_ref.delete()
  return ''

# updateDocument
# Update a document within a specified document collection.
# Input:
#  - (string) collectionID <- Database collection name (ID)
#  - (string) documentID <- Database document name (ID)
#  - (dict) updateData <- Dictionary containing values to update in the doc
# Output:
#  - (string) error
def updateDocument(collectionID, documentID, updateData):
  debug(f'[updateDocument - INFO]: Starting updateDocument.')

  doc_ref, doc, err = retrieveDocument(databaseName, dataID)
  if not doc.exists:
    err = f'[updateDocument - ERROR]: Document {documentID} does not exist in collection {collectionID}.'
    debug(f'{err}')
    return err

  doc_ref.update(updateData)
  return ''

################################################################################
# Taste Helper Functions
################################################################################
# updateSingleIngredientTasteRating
# Updates the user's taste rating of the ingredient, ingredient subcluster and cluster.
# - Input:
#   - (string) user id,
#   - (string) ingredient id
#   - (float)  rating
# - Output:
#   - (string) error
def updateSingleIngredientTasteRating(user_id, ingredient_id, rating):
  debug(f'[updateSingleIngredientTasteRating - INFO]: Starting.')
  updating_data = {}

  # Retrieve the user document
  doc_ref, doc, err = retrieveDocument('users', user_id)
  if err:
    return err
  user_dict = doc.to_dict()

  # Retrieve the ingredients document
  i_dict = {}
  doc_ref, doc, err = retrieveDocument('ingredients', ingredient_id)
  if err:
    return err
  ingredients_dict = doc.to_dict()
  try:
    i_dict = ingredients_dict[ingredient_id]
  except:
    err = '[updateSingleIngredientTasteRating - ERROR]: Unable to find ingredient information.'
    debug(f'{err}')
    return err

  # Update the ingredient rating
  updating_data['i_taste'] = user_dict['i_taste']
  try:
    r = user_dict['i_taste'][ingredient_id]['rating']
    n = user_dict['i_taste'][ingredient_id]['n_ratings']
    r = (r*n+rating)/(n+1)
    n += 1
    updating_data['i_taste'][ingredient_id] =  {'rating': r, 'n_ratings': n}
  except:
    updating_data['i_taste'] = {ingredient_id: {'rating': rating, 'n_ratings': 1}}

  # Update the ingredient subcluster rating
  subcluster_id = i_dict["subcluster"]
  if subcluster_id != None:
    updating_data['is_taste'] = user_dict['is_taste']
    try:
      r = user_dict['is_taste'][subcluster_id]['rating']
      n = user_dict['is_taste'][subcluster_id]['n_ratings']
      r = (r*n+rating)/(n+1)
      n += 1
      updating_data['is_taste'] = {subcluster_id: {'rating': r, 'n_ratings': n}}
    except:
      updating_data['is_taste'] = {subcluster_id: {'rating': rating, 'n_ratings': 1}}

  # Update the ingredient cluster rating
  cluster_id = i_dict["cluster"]
  if cluster_id != None:
    updating_data['ic_taste'] = user_dict['ic_taste']
    try:
      r = user_dict['ic_taste'][cluster_id]['rating']
      n = user_dict['ic_taste'][cluster_id]['n_ratings']
      r = (r*n+rating)/(n+1)
      n += 1
      updating_data['ic_taste'] = {cluster_id: {'rating': r, 'n_ratings': n}}
    except:
      updating_data['ic_taste'] = {cluster_id: {'rating': rating, 'n_ratings': 1}}

  # Update the user's document:
  err = updateDocument('users', user_id, updating_data)
  if err:
    err = f'[updateSingleIngredientTasteRating - ERROR]: Unable to update user document with taste ratings for ingredient {ingredient_id}, err: {err}'
    debug(f'{err}')
    return err
  return''

################################################################################
# updateIngredientTasteRating
# Updates the user's taste rating of the given ingredients.
# Input:
#  - (dict) data containing user id, ingredient ids and ratings
# Output:
#  - (string) error
def updateIngredientTasteRatings(data):
  debug(f'[updateIngredientTasteRating - INFO]: Starting.')

  user_id = data['userID']
  ingredient_ids = data['taste_ratings']
  for ingredient_id in ingredient_ids.keys():
    rating = ingredient_ids[ingredient_id]
    err = updateSingleIngredientTasteRating(user_id, ingredient_id, rating)
    if err:
      err = f'[updateIngredientTasteRating - ERROR]: Unable to update taste ratings for ingredient {ingredient_id}, err: {err}'
      debug(f'{err}')
      return err
  return ''

################################################################################
# updateSingleRecipeTasteRating
# Updates the user's taste rating of the recipe and it's ingredients.
# - Input:
#   - (string) user id,
#   - (string) recipe id
#   - (float)  rating
# - Output:
#   - (string) error
def updateSingleRecipeTasteRating(user_id, recipe_id, rating):
  debug(f'[updateSingleRecipeTasteRating - INFO]: Starting.')
  updating_data = {}

  # Retrieve the user document
  doc_ref, doc, err = retrieveDocument('users', user_id)
  if err:
    return err
  user_dict = doc.to_dict()

  # Retrieve the recipe document
  r_dict = {}
  doc_ref, doc, err = retrieveDocument('recipes', recipe_id)
  if err:
    return err
  recipes_dict = doc.to_dict()
  try:
    r_dict = recipes_dict[recipe_id]
  except:
    err = '[updateSingleRecipeTasteRating - ERROR]: Unable to find recipe information.'
    debug(f'{err}')
    return err

  # Update the recipe rating
  updating_data['r_taste'] = user_dict['r_taste']
  try:
    r = user_dict['r_taste'][recipe_id]['rating']
    n = user_dict['r_taste'][recipe_id]['n_ratings']
    r = (r*n+rating)/(n+1)
    n += 1
    updating_data['r_taste'][recipe_id] =  {'rating': r, 'n_ratings': n}
  except:
    updating_data['r_taste'] = {recipe_id: {'rating': rating, 'n_ratings': 1}}

  # Update the ingredients.
  ingredient_ids = r_dict["ingredient_ids"]
  for ingredient_id in ingredient_ids:
    ingredient_id = str(ingredient_id)
    err = updateSingleIngredientTasteRating(user_id, ingredient_id, rating)
    if err:
      err = f'[updateSingleRecipeTasteRating - ERROR]: Unable to update taste ratings for recipe {recipe_id}, err: {err}'
      debug(f'{err}')
      return err

  # Update the user's document:
  err = updateDocument('users', user_id, updating_data)
  if err:
    err = f'[updateSingleRecipeTasteRating - ERROR]: Unable to update user document with taste ratings for recipe {recipe_id}, err: {err}'
    debug(f'{err}')
    return err
  return''

################################################################################
# updateRecipeTasteRating
# Updates the user's recipe rating of the given recipes.
# Input:
#  - (dict) data containing user id, ingredient ids and ratings
# Output:
#  - (string) error
def updateRecipeTasteRating(data):
  debug(f'[updateRecipeTasteRating - INFO]: Starting.')

  user_id = data['userID']
  recipe_ids = data['taste_ratings']
  for recipe_id in recipe_ids.keys():
    rating = recipe_ids[recipe_id]
    err = updateSingleRecipeasteRating(user_id, recipe_id, rating)
    if err:
      err = f'[updateRecipeTasteRating - ERROR]: Unable to update taste ratings for recipe {recipe_id}, err: {err}'
      debug(f'{err}')
      return err
  return ''

################################################################################
# API URLs
################################################################################
# API index
# Renders the template index.html
def show_form():
  data = {'pageOutput':'', 'pageError':''}
  return render_template('index.html', data=data)

def grab_form_response():
  data = {'pageOutput':'Unable to find requested page.', 'pageError':''}
  try:
    pageInput = request.form.get('pageInput', '')
    pageName = request.form.get('pageName', '').split('|')
    debug(f'[Home - DATA]: pageName: {pageName}')
    debug(f'[Home - DATA]: pageInput: {pageInput}')
    if pageName[0] == '': # Home page
      return show_form()
    if pageName[0] == 'taste_preference': # Taste Preference
      values = pageInput.split(',')
      for i, val in enumerate(values):
        values[i] = val.strip() # No additional spaces
      if len(values) != 1:
        err = 'Incorrect number of values given for '
        err += 'taste_preference(userID)'
      return taste_preference(values[0])
    if pageName[0] == 'update_preference': # Update Preference
      values = pageInput.split(',')
      for i, val in enumerate(values):
        values[i] = val.strip() # No additional spaces
      if len(values) != 3:
        err = 'Incorrect number of values given for '
        err += 'update_preference(userID, recipeID, rating)'
      return update_preference(values[0], values[1], values[2])
    if pageName[0] == 'retrieve_data': # Retrieve value from DB
      pageType = pageName[1]
      pageName = pageName[0]
      values = pageInput.split(',')
      for i, val in enumerate(values):
        values[i] = val.strip() # No additional spaces
      if len(values) != 1:
        err = 'Incorrect number of values given for '
        err += 'retrieve_data(databaseName, dataID)'
      return retrieve_data(pageType, values[0])
    if pageName[0] == 'check_data': # Retrieve value from DB
      return check_data()
    if err:
      data['pageError'] = err
    data['pageOutput'] = json.dumps(r, sort_keys=True, indent=4)
  except:
    if err:
      return f'page name: {pageName}, page input: {pageInput}, err: {err}'
      
  if not r:
    data['pageOutput'] = ''
  debug(f"[Home - DATA]: r: {r}")
  debug(f"[Home - DATA]: err: {err}")
  debug(f"[Home - DATA]: data['pageOutput']: {data['pageOutput']}")
  debug(f"[Home - DATA]: data['pageError']: {data['pageError']}")
  return render_template('index.html', data=data)

@app.route('/', methods=['GET', 'POST'])
def home():
  debug('[Home - INFO]: Requesting the home page.')
  if request.method == 'POST':
    debug('[Home - INFO]: POST request')
    debug(f'[Home - DATA]: request.form: {request.form}')
    return grab_form_response()

  debug('[Home - INFO]: GET request')
  debug(f'[Home - DATA]: request: {request}')
  return show_form()

################################################################################
# Taste Preference URLs
################################################################################
# onboarding_ingredient_rating [GET|POST]
# 1st end point used.
# GET: End point is for obtaining the ingredients for the user to rate
# during on-boarding.
# - Input:
#   - n/a
# - Output:
#   - (json)
# POST: End point is for saving the user's ratings of ingredients
# during on-boarding.
# - Input:
#   - (json)
# - Output:
#   - (string) error
@app.route('/onboarding_ingredient_rating', methods=['GET', 'POST'])
def onboarding_ingredient_rating():
  debug(f'[onboarding_ingredient_rating - INFO]: Starting.')
  if request.method == 'POST':
    debug('[onboarding_ingredient_rating - INFO]: POST request')
    request_data = json.loads(request.data)
    debug(f'[Home - DATA]: request_data: {request_data}')
    user_id =  request_data['userID']
    # Attempt to grab user's document (as this is the first endpoint)
    err = createDocument('users', user_id, userStartingDoc)
    if err:
      return err
    # Update user's document with ingredient ratings
    err = updateIngredientTasteRatings(request_data)
    if err:
      return err
    return ''

  debug('[onboarding_ingredient_rating - INFO]: GET request')
  # Attempt to grab onboarding ingredients list.
  doc_ref, doc, err = retrieveDocument('onboarding', 'ingredients')
  if err:
    return err
  return jsonify(doc.to_dict())

################################################################################
# onboarding_recipe_rating [GET|POST]
# 2nd end point used.
# GET: End point is for obtaining the ingredients for the user to rate
# during on-boarding.
# - Input:
#   - n/a
# - Output:
#   - (json)
# POST: End point is for saving the user's ratings of ingredients
# during on-boarding.
# - Input:
#   - (json)
# - Output:
#   - (string) error
@app.route('/onboarding_recipe_rating', methods=['GET', 'POST'])
def onboarding_recipe_rating():
  debug(f'[onboarding_recipe_rating - INFO]: Starting.')
  if request.method == 'POST':
    debug('[onboarding_recipe_rating - INFO]: POST request')
    request_data = json.loads(request.data)
    debug(f'[Home - DATA]: request_data: {request_data}')
    user_id =  request_data['userID']
    # Attempt to grab user's document (as this is the first endpoint)
    err = createDocument('users', user_id, userStartingDoc)
    if err:
      return err
    # Update user's document with ingredient ratings
    err = updateRecipeTasteRatings(request_data)
    if err:
      return err
    # Return json of test recipes that a user should liked
    # TODO(kbona@): Fix up the proper json return.
    return jsonify("""
{"60372": {
  "cookTime": 30,
  "ingredient_phrases": [
    "450g/1lb boneless chicken breasts, skinned, cut into 2.5cm/1in cubes",
    "2 tsp light soy sauce",
    "1 tsp Shaoxing rice wine (or dry sherry)",
    "1 tsp cornflour",
    "1 tbsp groundnut (peanut) oil",
    "1 tsp salt",
    "freshly ground white pepper",
    "2 tbsp finely chopped orange zest",
    "1 tbsp finely chopped lemon zest",
    "2 tsp sesame oil",
    "3 tbsp finely chopped fresh coriander",
    "enough long-grain rice to fill a measuring jug to 400ml/14fl oz level",
    "1 tbsp groundnut or peanut oil",
    "3 garlic cloves, finely sliced",
    "2 tsp salt",
    "750g/1.5lb Chinese greens, such as choi sum or bok choi"
  ],
  "prepTime": 30,
  "servings": "Serves 4",
  "steps": [
    "Combine the cubed chicken with the soy sauce, rice wine (or dry sherry) and cornflour in a small bowl. Put the mixture in the fridge for about 15 minutes.",
    "For the rice, put the rice into a heavy pan with 600ml/21 fl oz water. The general rule of thumb is that the water should come up above the level of the rice by about 2.5cm/1in, or the top part of the thumb!",
    "Bring the water to the boil and cook until most of the surface liquid has evaporated - this should take about 15 minutes. The surface of the rice should have small indentations like a pitted crater.",
    "At this point, cover the pan with a very tight-fitting lid, turn the heat as low as possible and let the rice cook undisturbed for 15 minutes.  There is no need to 'fluff' the rice, let it rest for five minutes before serving it.",
    "To finish the chicken, heat a wok until it is very hot and then add the oil. When the oil is very hot and slightly smoking, add the chicken to the wok, together with the salt, pepper and orange and lemon zest.",
    "Stir-fry the mixture for four minutes, or until the chicken is cooked.  Stir in the sesame oil and give the mixture two turns and cook for another three minutes. Finally add the coriander and continue to stir-fry for another minute. Turn onto a platter and serve at once.",
    "For the greens, heat a wok or large frying-pan over high heat until it is hot. Add the oil, and, when it is very hot and slightly smoking, add the garlic and salt. Stir-fry the mixture for 15 seconds. Quickly add the Chinese greens.  Stir-fry for 3-4 minutes, or until the greens have wilted, but are still slightly crisp.",
    "Serve the chicken with the Chinese greens and rice."
  ],
  "title": "Quick orange and lemon chicken"},
"27455": {
  "cookTime": 120,
  "ingredient_phrases": [
    "4 tbsp vegetable oil",
    "500g/1lb 2oz good-quality beef steak, finely diced",
    "500g/1lb 2oz good-quality beef mince",
    "1 white onion, peeled, finely chopped",
    "1 red onion, peeled, finely chopped",
    "2 sticks celery, trimmed, chopped",
    "1 dried chipotle chilli",
    "1 tbsp dried chilli flakes",
    ".5 tbsp chilli powder",
    "2 tsp dried oregano",
    "3 tbsp light brown sugar",
    "2 x 400g/14oz cans chopped tomatoes",
    "500ml/17fl oz beef stock",
    "1 x 400g/14oz can kidney beans, drained and rinsed",
    "1 x 400g/14oz can black-eyed beans, drained and rinsed",
    "sea salt flakes and freshly ground black pepper",
    "75g/3oz plain chocolate, minimum 70% cocoa solids, roughly chopped",
    "bunch fresh coriander",
    "steamed rice",
    "8 tbsp soured cream",
    "4 spring onions, trimmed, finely sliced"
  ],
  "prepTime": 30,
  "servings": "Serves 6-8",
  "steps": [
    "Heat two tablespoons of the oil over a medium to high heat in a large, heavy-based pan with a tight fitting lid.",
    "Fry the diced beef steak in batches until browned all over, setting each batch aside on a plate using a slotted spoon.",
    "Add another tablespoon of oil to the pan and add the beef mince, frying until browned all over. Remove the mince from the pan using a slotted spoon and set aside with the beef steak.",
    "Add the remaining tablespoon of oil to the pan and fry the white onion, red onion and celery for 3-4 minutes, or until the onions have softened but not browned.",
    "Stir in the chipotle chilli, chilli flakes, chilli powder and oregano until well combined. Cook for a further two minutes.",
    "Return the diced and minced beef to the pan, then stir in the sugar, chopped tomatoes, beef stock, kidney beans and black-eyed peas. Bring the mixture to the boil, then reduce the heat until the mixture is simmering. Cover and continue to simmer over a low heat for 2-3 hours. (Alternatively, preheat the oven to 140C/280F/Gas 1 to cook in an ovenproof dish for the same amount of time.)",
    "Just before serving, season the chilli with crushed sea salt flakes and freshly ground pepper. Stir in the chocolate until melted, then stir in the chopped coriander.",
    "Serve the chilli with a bowl of steamed rice and top each serving with a dollop of soured cream. Garnish with the sliced spring onions."
  ],
  "title": "Beef chilli with bitter chocolate"}}
""")

  debug('[onboarding_recipe_rating - INFO]: GET request')
  # Attempt to grab onboarding ingredients list.
  doc_ref, doc, err = retrieveDocument('onboarding', 'recipes')
  if err:
    return err
  return jsonify(doc.to_dict())

################################################################################
# Testing URLs
################################################################################
# retrieve_data [GET|POST]
# GET|POST: End point is for retrieving documents from the database.
# - Input:
#   - (string) databaseName (Firebase collection ID)
#   - (string) dataID (Firebase document ID)
# - Output:
#   - (string) error
@app.route('/retrieve/<databaseName>/<dataID>', methods=['GET', 'POST'])
def retrieve_data(databaseName, dataID):
  debug(f'[retrieve_data - INFO]: Starting retrieve_data.')
  doc_ref, doc, err = retrieveDocument(databaseName, dataID)
  if err:
    return err

  return jsonify(doc.to_dict())

################################################################################
# Server Activation
################################################################################
# Start the web server!
if __name__ == "__main__":
  app.run(debug=True)