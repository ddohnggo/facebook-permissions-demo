/*
 * Copyright 2010 Facebook
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

function init() {
    window.fbAsyncInit = initFacebook;
    var root = document.createElement('div');
    root.id = 'fb-root';
    document.body.appendChild(root);
    var script = document.createElement('script');
    script.type = 'text/javascript';
    script.src = document.location.protocol + '//connect.facebook.net/en_US/all.js';
    script.async = true;
    root.appendChild(script);
}

function initFacebook() {
    FB.init({appId: gFacebookAppId, status: true, cookie: true, xfbml: true});
    FB.Event.subscribe('auth.statusChange', function(response) {
	if (response.session && response.session.uid) {
	    if (response.session.uid != gUserId) {
		gUserId = response.session.uid;
		reloadContent();
	    }
	} else if (gUserId) {
	    gUserId = null;
	    reloadContent();
	}
    });
}

function reloadContent() {
    $("#content").html('<img class="loading" src="/static/loading.gif"/>');
    $.post("/content", {}, function(data) {
        $("#content").html(data);
    });
}

init();
