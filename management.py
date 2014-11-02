try:
    import usjon as json
except ImportError:
    import json

filename = "management.json"
data = json.load(open(filename))

def dnd_users():
    return data['dnd_users']

def add_user_to_dnd(username):
    data['dnd_users'].append(username)
    json.dump(data, open('management.json', 'wb'))
    return dnd_users()

