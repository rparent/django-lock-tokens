/*global document, window, XMLHttpRequest */
var lock_tokens = {};


/* Token class */
lock_tokens.Token = function (app_label, model, object_id, token, expiration_date_str) {
  this.app_label = app_label;
  this.model = model;
  this.object_id = object_id;
  this.token_ = token;
  this.expiration_date_ = new Date(expiration_date_str);
};
lock_tokens.Token.prototype.get_token = function () {
  return this.token_;
};
lock_tokens.Token.prototype.get_expiration_date = function () {
  return this.expiration_date_;
};
lock_tokens.Token.prototype.set_expiration_date = function (expiration_date_str) {
  this.expiration_date_ = new Date(expiration_date_str);
};


/* API Client class*/
lock_tokens.APIClient = function (base_api_url, csrf_token, csrf_header_name) {
  this.base_api_url = base_api_url;
  this.csrf_token = csrf_token;
  this.csrf_header_name = csrf_header_name;
  this.async_call_ = true;
};
lock_tokens.APIClient.prototype.api_call_ = function (uri, http_method, callback) {
  var r = new XMLHttpRequest();
  r.open(http_method, this.base_api_url + uri, this.async_call_);
  r.onreadystatechange = function () {
    if (r.readyState !== 4) { return; }
    callback(r.status, r.responseText);
  };
  var is_safe = /^(GET|HEAD|OPTIONS|TRACE)$/.test(http_method);
  if (!is_safe && this.csrf_token) {
    r.setRequestHeader(this.csrf_header_name, this.csrf_token);
  }
  r.send();
};
lock_tokens.APIClient.prototype.lock_resource = function (app_label, model, object_id, callback) {
  this.api_call_([app_label, model, object_id].join('/') + '/', 'POST', function (http_status, text) {
    if (http_status === 201) {
      var api_response = JSON.parse(text);
      callback(api_response);
    } else {
      console.error('Could not lock resource. HTTP status: ' + http_status);
      callback(null);
    }
  });
};
lock_tokens.APIClient.prototype.get_existing_lock_token = function (app_label, model, object_id, token_str, callback) {
  this.api_call_([app_label, model, object_id, token_str].join('/') + '/', 'GET', function (http_status, text) {
    if (http_status === 200) {
      var api_response = JSON.parse(text);
      callback(api_response);
    } else {
      console.error('Could not get lock token. HTTP status: ' + http_status);
      callback(null);
    }
  });
};
lock_tokens.APIClient.prototype.renew_lock_token = function (app_label, model, object_id, token_str, callback) {
  this.api_call_([app_label, model, object_id, token_str].join('/') + '/', 'PATCH', function (http_status, text) {
    if (http_status === 200) {
      var api_response = JSON.parse(text);
      callback(api_response);
    } else {
      console.error('Could not renew lock. HTTP status: ' + http_status);
      callback(null);
    }
  });
};
lock_tokens.APIClient.prototype.remove_lock_token = function (app_label, model, object_id, token_str, callback) {
  this.api_call_([app_label, model, object_id, token_str].join('/') + '/', 'DELETE', function (http_status) {
    if (http_status === 204) {
      callback(true);
    } else {
      console.error('Could not delete lock. HTTP status: ' + http_status);
      callback(false);
    }
  });
};


/* Main class */
lock_tokens.LockTokens = function (options) {
  options = options || {};
  var base_api_url = options.base_api_url || '/lock_tokens/';
  var csrf_token = options.csrf_token || null;
  var csrf_header_name = options.csrf_header_name || 'X-CSRFToken';
  this.api_client_ = new lock_tokens.APIClient(base_api_url, csrf_token, csrf_header_name);
  this.registry_ = {};
  this.with_alerts_ = options.with_alerts || false;
};
lock_tokens.LockTokens.prototype.get_registry_key_ = function (app_label, model, object_id) {
  return [app_label, model, object_id].join('_');
};
lock_tokens.LockTokens.prototype.add_token_to_registry_ = function (token, app_label, model, object_id) {
  this.registry_[this.get_registry_key_(app_label, model, object_id)] = token;
};
lock_tokens.LockTokens.prototype.get_token_from_registry_ = function (app_label, model, object_id) {
  return this.registry_[this.get_registry_key_(app_label, model, object_id)] || null;
};
lock_tokens.LockTokens.prototype.remove_token_from_registry_ = function (app_label, model, object_id) {
  delete this.registry_[this.get_registry_key_(app_label, model, object_id)];
};
lock_tokens.LockTokens.prototype.lock = function(app_label, model, object_id, callback) {
  var LT = this;
  LT.api_client_.lock_resource(app_label, model, object_id, function (token_dict) {
    if (token_dict) {
      var token = new lock_tokens.Token(app_label, model, object_id, token_dict.token, token_dict.expires);
      LT.add_token_to_registry_(token, app_label, model, object_id);
      if (callback) { callback(token); }
      return;
    }
    var error = 'Could not lock object!';
    console.error(error);
    if (LT.with_alerts_) {
      window.alert(error);
    }
    if (callback) { callback(null); }
  });
};
lock_tokens.LockTokens.prototype.register_existing_lock_token = function(app_label, model, object_id, token_string, callback) {
  var LT = this;
  LT.api_client_.get_existing_lock_token(app_label, model, object_id, token_string, function (token_dict) {
    var token;
    if (token_dict) {
      token = new lock_tokens.Token(app_label, model, object_id, token_dict.token, token_dict.expires);
      LT.add_token_to_registry_(token, app_label, model, object_id);
    } else {
      var error = 'Could not register existing token';
      console.error(error);
      if (LT.with_alerts_) {
        window.alert(error);
      }
    }
    if (callback) {callback(token); }
  });
};
lock_tokens.LockTokens.prototype.unlock = function(app_label, model, object_id, callback) {
  var LT = this;
  var token = LT.get_token_from_registry_(app_label, model, object_id);
  if (!token) {
    if (LT.with_alerts_) {
      window.alert('No lock token registered for this object!');
    }
    if (callback) { callback(false); }
    return;
  }
  if (token.timeout) { clearTimeout(token.timeout); }
  LT.api_client_.remove_lock_token(app_label, model, object_id, token.get_token(), function (success) {
    if (success) {
      LT.remove_token_from_registry_(app_label, model, object_id);
      if (callback) { callback(true); }
      return;
    }
    if (LT.with_alerts_) {
      window.alert('Could not unlock object!');
    }
    if (callback) { callback(false); }
  });
};
lock_tokens.LockTokens.prototype.renew_lock = function (app_label, model, object_id, callback) {
  var LT = this;
  var token = LT.get_token_from_registry_(app_label, model, object_id);
  if (!token) {
    if (LT.with_alerts_) {
      window.alert('No lock token registered for this object!');
    }
    if (callback) { callback(null); }
    return;
  }
  LT.api_client_.renew_lock_token(app_label, model, object_id, token.get_token(), function (token_dict) {
    if (token_dict) {
      token.set_expiration_date(token_dict.expires);
      if (callback) { callback(token); }
      return;
    }
    if (LT.with_alerts_) {
      window.alert('Could not renew lock on object!');
    }
    if (callback) { callback(false); }
  });
};
lock_tokens.LockTokens.prototype.hold_lock = function (app_label, model, object_id) {
  var LT = this;
  var token = LT.get_token_from_registry_(app_label, model, object_id);
  var set_renew_lock_timeout = function () {
    var delay = token.get_expiration_date().getTime() - new Date().getTime();
    if (delay < 0) {
      console.error('The token seems to have expired already. If you just set it, check your time settings (timezone, expiration timeout, etc.)');
      return null;
    }
    return setTimeout(function () {
      LT.renew_lock(app_label, model, object_id, function (t) {
        if (t) {
          token.timeout = set_renew_lock_timeout();
        }
      });
    }, Math.max(delay - 2000, 10));
  };
  if (token) {
    token.timeout = set_renew_lock_timeout();
  } else {
    LT.lock(app_label, model, object_id, function (t) {
      if (t) { LT.hold_lock(app_label, model, object_id); }
    });
  }
};
lock_tokens.LockTokens.prototype.clear_all_locks = function (callback) {
  var LT = this;
  var key, token;
  var registry = LT.registry_;
  var size = Object.keys(registry).length, treated = 0;
  var cb = function () {
    treated++;
    if (treated === size) {
      callback();
    }
  };
  if (size === 0) { callback(); }
  for (key in registry) {
    if (registry.hasOwnProperty(key)) {
      token = registry[key];
      LT.unlock(token.app_label, token.model, token.object_id, cb);
    }
  }
};

lock_tokens.emit_event = function (event_name) {
  var e;
  var full_event_name = "lock_tokens." + event_name;
  if (document.createEvent) {
    e = document.createEvent("HTMLEvents");
    e.initEvent(full_event_name, true, true);
  } else {
    e = document.createEventObject();
    e.eventType = full_event_name;
  }
  e.eventName = full_event_name;
  if (document.createEvent) {
    document.dispatchEvent(e);
  } else {
    document.fireEvent("on" + e.eventType, e);
  }
};

