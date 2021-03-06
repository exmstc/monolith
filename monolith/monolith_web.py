import argparse

from flask import Flask, render_template, abort, request
from flask_bootstrap import Bootstrap

from util.dbHelper import Helper

app = Flask(__name__, template_folder='templates')
bootstrap = Bootstrap(app)

@app.route('/')
def hello():
    modulename = dbControler.getModuleName()
    channels = dbControler.getSlackChannels()
    return render_template('hello.html', modules=modulename, channels=channels)

@app.route('/config/<module>', methods=["GET", "POST"])
def config(module=None):
    modulename = dbControler.getModuleName()
    if request.method == "GET":
        default = dbControler.getDefaultConfig(name=module)
        if default == None or not module in modulename:
            return abort(404)
        queries = dbControler.getQueries(name=module)
        del default['_id']
        for q in queries:
            del q['_id'], q['exclude_list']
        channels = dbControler.getSlackChannels()
        return render_template('config.html', modules=modulename, mod_name=module, queries=queries, default=default, channels=channels)
    elif request.method == "POST":
        data = request.json
        if data == None:
            return abort(400)
        else:
            default = dbControler.getDefaultConfig(name=module)
            if default == None or not module in modulename:
                return abort(404)
            if data['action'] == 'add':
                if 'multi' in data.keys() and data['multi'] == 'true':
                    if 'queries' in data.keys() and len(data['queries']) > 0:
                        result = []
                        for query in data['queries']:
                            query_name = query['query']
                            if 'name' in query.keys() and query['name'] != '':
                                query_name = query['name']
                            try:
                                index = dbControler.addNewQuery(name=module, query=query['query'], query_name=query_name)
                                data['index'] = index
                                dbControler.updateConfig(name=module, config=query)
                            except:
                                result.append('NG')
                            result.append('OK')
                        return ','.join(result)
                    else:
                        return abort(400)
                else:
                    if 'query' in data.keys() and data['query'] != '':
                        query_name = data['query']
                        if 'name' in data.keys() and data['name'] != '':
                            query_name = data['name']
                        index = dbControler.addNewQuery(name=module, query=data['query'], query_name=query_name)
                        data['index'] = index
                        dbControler.updateConfig(name=module, config=data)
                    else:
                        return abort(400)
            elif data['action'] == 'update':
                dbControler.updateConfig(name=module, config=data)
            elif data['action'] == 'delete':
                query_id = int(data['index'])
                dbControler.removeQuery(name=module, index=query_id)
            elif data['action'] == 'enable':
                dbControler.enable(name=module)
            elif data['action'] == 'disable':
                dbControler.disable(name=module)
            elif data['action'] == 'run_job_now':
                dbControler.runNow(name=module)
        return 'OK'

@app.route('/result/<module>')
def result(module=None):
    modulename = dbControler.getModuleName()
    if request.method == "GET":
        channels = dbControler.getSlackChannels()
        page = request.args.get('pages', default='0')
        if page.isdigit():
            page = int(page)
        else:
            page = 0
        limit = request.args.get('limit', default='10')
        if limit.isdigit():
            limit = int(limit)
        else:
            limit = 10
        empty = request.args.get('empty', default='false')
        status = request.args.get('status', default='all')
        query = request.args.get('query', default='all')
        default = dbControler.getDefaultConfig(name=module)
        if default == None or not module in modulename:
            return abort(404)
        queries = [x['name'] for x in dbControler.getQueries(module) if 'name' in x.keys()]
        if not query:
            query = queries[0]
        (results, count) = dbControler.getResult(name=module, query=query, limit=limit, page=page, empty=empty, status=status)
        return render_template('result.html', modules=modulename, mod_name=module, queries=queries, results=results, total_count=count, channels=channels)

@app.route('/global_config', methods=["POST"])
def global_config(module=None):
    if request.method == "POST":
        data = request.json
        if data['action'] == 'update':
            if 'channels' in data.keys():
                channels = data['channels']
                dbControler.setSlackChannels(channels=channels)
            else:
                return abort(400)
        return 'OK'

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--db-host', type=str, default='localhost', help='DATABASE HOST NAME')
    parser.add_argument('--db-port', type=int, default=27017, help='DATABASE PORT')
    parser.add_argument('--db-name', type=str, default='monolith-database', help='DATABASE NAME')
    args = parser.parse_args()
    global dbControler
    dbControler = Helper(args.db_host, args.db_port, args.db_name)
    app.run(debug=True, host='0.0.0.0')
