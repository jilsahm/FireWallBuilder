from flask import render_template, Flask, request, abort, make_response
from modules.options import mapJsonToRule, buildFirewall, Firewall
from modules.sanitizer import isValidRule, Patterns
from modules.dbhandler import buildDatabase, Connection
import json

app = Flask(__name__)
db  = "./database/firewall.db"

class ContentLength():
    def __init__( self, maxSize ):
        self.maxSize = maxSize
        self.route = None
        
    def wrappedRoute( self, *args, **kwargs ):
        length = request.content_length
        if length is not None and length > self.maxSize:
            abort( 413 )
        return self.route( *args, **kwargs )
    
    def __call__( self, route ):
        self.route = route
        return self.wrappedRoute
    
@app.route( "/" )
def index():
    return render_template( "index.html" )

@app.route( "/compiler", methods=["POST"] )
@ContentLength( 4096 )
def compiler():
    rules = mapJsonToRule( request.get_json() )
    if isValidRule( rules ):
        outputScript = buildFirewall( rules )
    else:
        abort( 500 )
    return outputScript

@ContentLength( 4096 )
@app.route( "/save", methods=["POST"] )
def save():
    rules = mapJsonToRule( request.get_json() )    
    if isValidRule( rules ):
        if 0 >= len( rules ):
            return "There has to be at least one rule"
        firewall = Firewall( "Testtitile", "0000-00-00", rules )
        with Connection( db ) as cursor:
            firewall.insert( cursor )
    return "Firewall saved"

@ContentLength( 64 )
@app.route( "/show" )
def showSavedFirewalls():
    firewall = []
    with Connection( db ) as cursor:
        firewall = Firewall.fetchAll( cursor )
    return json.dumps( firewall )

@ContentLength( 64 )
@app.route( "/load/<fid>", methods=["GET"] )
def loadFirewall( fid ):
    if Patterns.ID.value.search( fid ) is None:
        abort( 500 )
    with Connection( db ) as cursor:
        return Firewall.fetchById( fid, cursor )
    abort( 500 )

@ContentLength( 64 )
@app.route( "/remove/<fid>", methods=["GET"] )
def removeFirewall( fid ):
    if Patterns.ID.value.search( fid ) is None:
        abort( 500 )
    # TODO
    return "TODO"

if __name__ == "__main__":
    #app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
    buildDatabase( db, "./database/dbstructure.sql" )
    app.run( host= '0.0.0.0' )
