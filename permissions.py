#!/usr/bin/env python
#
# Copyright 2010 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""A Facebook application that demonstrates new data permissions."""

import facebook
import logging
import os.path
import tornado.web
import tornado.wsgi
import urllib
import wsgiref.handlers

from django.utils import simplejson as json
from google.appengine.ext import db
from google.appengine.ext.webapp import util

FACEBOOK_APP_ID = "your app ID"
FACEBOOK_APP_SECRET = "your app secret"


class User(db.Model):
    id = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    name = db.StringProperty(required=True)
    profile_url = db.StringProperty(required=True)
    access_token = db.StringProperty(required=True)


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        cookies = dict((k, c.value) for k, c in self.cookies.items())
        cookie = facebook.get_user_from_cookie(
            cookies, FACEBOOK_APP_ID, FACEBOOK_APP_SECRET)
        if cookie:
            user = User.get_by_key_name(cookie["uid"])
            if not user:
                graph = facebook.GraphAPI(cookie["access_token"])
                profile = graph.get_object("me")
                user = User(key_name=str(profile["id"]),
                            id=str(profile["id"]),
                            name=profile["name"],
                            profile_url=profile["link"],
                            access_token=cookie["access_token"])
                user.put()
            elif user.access_token != cookie["access_token"]:
                user.access_token = cookie["access_token"]
                user.put()
            return user
        return None

    @property
    def api(self):
        if self.current_user:
            return facebook.GraphAPI(self.current_user.access_token)
        else:
            return facebook.GraphAPI()

    def render_string(self, path, **args):
        args["facebook_app_id"] = FACEBOOK_APP_ID
        return tornado.web.RequestHandler.render_string(self, path, **args)


class HomeHandler(BaseHandler):
    def get(self):
        self.render("index.html")


class ContentHandler(BaseHandler):
    def post(self):
        self.write(self.ui.modules.Content())


class Content(tornado.web.UIModule):
    def render(self):
        if not self.current_user:
            return ""
        names = ["user_photos", "user_likes", "user_events", "email"]
        query = "SELECT " + ",".join(names) + " FROM permissions WHERE " + \
            "uid = " + self.current_user.id
        url = "https://api.facebook.com/method/fql.query?" + urllib.urlencode({
            "access_token": self.current_user.access_token,
            "query": query,
            "format": "json",
        })
        try:
            permissions = json.loads(urllib.urlopen(url).read())[0]
        except:
            permissions = dict((n, 0) for n in names)
        photos = self.handler.api.get_connections("me", "photos")
        likes = self.handler.api.get_connections("me", "likes")
        events = self.handler.api.get_connections("me", "events")
        email = self.handler.api.get_object("me").get("email", None)
        return self.render_string(
            "content.html", photos=photos, likes=likes, events=events,
            email=email, permissions=permissions)


settings = dict(
    template_path=os.path.join(os.path.dirname(__file__), "templates"),
    ui_modules={"Content": Content},
    debug=True,
)
application = tornado.wsgi.WSGIApplication([
    (r"/", HomeHandler),
    (r"/content", ContentHandler),
], **settings)


def main():
    util.run_wsgi_app(application)


if __name__ == "__main__":
    main()
