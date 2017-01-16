#!flask/bin/python
from flask import Flask, jsonify, render_template, make_response, request, abort, url_for
import redis
import ldclient
import time
import logging
import sys

root = logging.getLogger()
root.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

r = redis.StrictRedis(host='localhost', port=6379, db=0)
ldclient.set_sdk_key('SDK_KEY_HERE')

app = Flask(__name__)

# resource stored in memory
flavors = [
    {
        'id': 1,
        'name': u'Chocolate',
        'stock': 150
    },
    {
        'id': 2,
        'name': u'Banana',
        'stock': 400
    },
    {
        'id': 3,
        'name': u'Chocolate Chip',
        'stock': 250
    }
]

# get rate limit (x per minute) from feature flag and enforce it
# returns a dict containing rate limit values for response and a flag if the limit has been exceeded
def limit_requests(method):
    ip = request.remote_addr
    limit = ldclient.get().variation('api-rate-limiter', {'key': method, 'ip': ip}, False)
    t = int(time.time())
    key = ip+method+str(t/60)
    current = r.get(key)
    if current == None:
        current = 0
    header_values = {'429': False, 'limit': limit, 'remaining': limit-int(current)-1, 'reset': 60-t%60}
    #rate limit exceeded?
    if int(current) >= limit:
        header_values['429'] = True
    else:
        p = r.pipeline()
        p.incr(key,1)
        p.expire(key,60)
        p.execute()
    return header_values

# check feature flag for write permission
def has_write_permission():
    ip = request.remote_addr
    return ldclient.get().variation('api-write-permission', {'key': ip, 'ip': ip}, False)

# make our responses readable by humans
def convert_id_to_uri(flavor):
    new_flavor = {}
    for field in flavor:
        if field == 'id':
            new_flavor['uri'] = url_for('get_flavor', name = flavor['name'], _external = True)
        else:
            new_flavor[field] = flavor[field]
    return new_flavor

# create a response with configured mimetype and headers
def create_response(dat, header_values):
    resp = make_response(dat)
    resp.mimetype = 'application/json'
    resp.headers['X-Rate-Limit-Limit'] = header_values.get('limit')
    resp.headers['X-Rate-Limit-Remaining'] = header_values.get('remaining')
    resp.headers['X-Rate-Limit-Reset'] = header_values.get('reset')
    return resp

# Get all flavors
# Usage: $ curl -v host/api/v1/flavors
@app.route('/api/v1/flavors', methods=['GET'])
def get_flavors():
    header_values = limit_requests('GET')
    if header_values.get('429'):
        return render_template('429.html', \
        limit=header_values.get('limit'),\
        interval='minute',\
        reset=header_values.get('reset'))
    if len(flavors) == 0:
        abort(404)
    dat = jsonify({'flavors': map(convert_id_to_uri, flavors)})
    return create_response(dat, header_values)

# Get a flavor
# Usage: $ curl -v host/api/v1/flavors/FLAVOR_NAME
@app.route('/api/v1/flavors/<string:name>', methods=['GET'])
def get_flavor(name):
    header_values = limit_requests('GET')
    if header_values.get('429'):
        return render_template('429.html', \
        limit=header_values.get('limit'),\
        interval='minute',\
        reset=header_values.get('reset'))
    flavor = [flavor for flavor in flavors if name.lower() == flavor['name'].lower()]
    if len(flavor) == 0:
        abort(404)
    dat = jsonify({'flavor': convert_id_to_uri(flavor[0])})
    return create_response(dat, header_values)

# Create a flavor
# Usage: $ curl -v -H "Content-Type: application/json" -X POST -d '{"name":FLAVOR_NAME, "stock":FLAVOR_AMOUNT}' host/api/v1/flavors
@app.route('/api/v1/flavors', methods=['POST'])
def create_flavor():
    header_values = limit_requests('POST')
    if header_values.get('429'):
        return render_template('429.html', \
        limit=header_values.get('limit'),\
        interval='minute',\
        reset=header_values.get('reset'))
    if not has_write_permission():
        abort(403)
    if len(filter(lambda flavor: flavor['name'] == request.json['name'], flavors)) > 0:
        abort(409)
    try:
        flavor = {
            'id': flavors[-1]['id'] + 1,
            'name': request.json['name'],
            'stock': request.json['stock']
        }
    except:
        abort(400)
    flavors.append(flavor)
    dat = jsonify({'flavor': convert_id_to_uri(flavor)})
    return create_response(dat, header_values)

# Modify a flavor
# Usage: $ curl -v -H "Content-Type: application/json" -X PUT -d '{"name":NEW_FLAVOR_NAME, "stock":NEW_FLAVOR_AMOUNT}' host/api/v1/flavors/FLAVOR_NAME
@app.route('/api/v1/flavors/<string:name>', methods=['PUT'])
def update_flavor(name):
    header_values = limit_requests('PUT')
    if header_values.get('429'):
        return render_template('429.html', \
        limit=header_values.get('limit'),\
        interval='minute',\
        reset=header_values.get('reset'))
    if not has_write_permission():
        abort(403)
    flavor = filter(lambda flavor: flavor['name'].lower() == name.lower(), flavors)
    if len(flavor) == 0:
        abort(404)
    if not request.json:
        abort(400)
    if 'name' in request.json and type(request.json['name']) != unicode:
        abort(400)
    if 'stock' in request.json and type(request.json['stock']) is not int:
        abort(400)
    flavor[0]['name'] = request.json.get('name', flavor[0]['name'])
    flavor[0]['stock'] = request.json.get('stock', flavor[0]['stock'])
    dat = jsonify({'flavor': convert_id_to_uri(flavor[0])})
    return create_response(dat, header_values)

# Delete a flavor
# Usage: $ curl -v -X DELETE host/api/v1/flavors/FLAVOR_NAME
@app.route('/api/v1/flavors/<string:name>', methods=['DELETE'])
def delete_flavor(name):
    header_values = limit_requests('DELETE')
    if header_values.get('429'):
        return render_template('429.html', \
        limit=header_values.get('limit'),\
        interval='minute',\
        reset=header_values.get('reset'))
    if not has_write_permission():
        abort(403)
    flavor = filter(lambda flavor: flavor['name'].lower() == name.lower(), flavors)
    if len(flavor) == 0:
        abort(404)
    flavors.remove(flavor[0])
    dat = jsonify({'deleted': True})
    return create_response(dat, header_values)
