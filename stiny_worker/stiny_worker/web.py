from bottle import route, request, run

def run_webserver(worker, host, port):
    # Set up the bottle endpoint

    @route('/do/<command>', method='POST')
    def do_command(command):
        kwargs = dict(request.json)
        worker.do(command, **kwargs)
        return {}

    run(host=host, port=port)
