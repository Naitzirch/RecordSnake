from simplejsondb import Database
 
# Read info from json database
db_json = Database("database/db.json", default=dict())
db = db_json.data

# setting variables
users   = db["users"]

print(users.get("244496158049697792"))