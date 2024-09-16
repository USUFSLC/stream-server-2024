from flask import Blueprint, abort, request, make_response, redirect
import requests

blueprint = Blueprint("rtmp_callbacks", __name__)

# these routes should only be available if you're talking directly to the server
# that should mean that only other programs running on the same network as this docker container can access it
# if you're not, i don't want you to even know they exist
# this function returns the default 404 message for everything here, even if the route isn't declared
@blueprint.before_app_request
def no_proxies():
    if "X-Forwarded-For" in request.headers:
        return abort(404)

@blueprint.route("/start", methods=["POST"])
def rtmp_start():
    key = request.form.get("name")
    if key is None:
        return make_response("You shouldn't be making requests here as a user.", 400)

    info = stream_keys.get(key)
    if info is None:
        return make_response("No such key.", 400)

    return make_response("Go ahead!")
