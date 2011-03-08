'''
Created on Mar 8, 2011

@author: camerondawson
'''
from features.tcm_data_helper import eq_, get_user_password, record_api_for_step, \
    jstr, json_to_obj, as_arrayof, plural, json_pretty
from lettuce.terrain import world
from tcm_data_helper import ns
import base64
import copy
import mimetypes
import string
import urllib

def get_auth_header(userid = "admin@utest.com", passwd = "admin"):
    auth = 'Basic ' + string.strip(base64.encodestring(userid + ':' + passwd))

    return auth

def get_form_headers(auth_header = get_auth_header()):
    return {'Authorization': auth_header,
            'content-type': "application/x-www-form-urlencoded"}

def get_json_headers(auth_header = get_auth_header()):
    return {'Authorization': auth_header,
            'Content-Type':'application/json'}
def add_params(uri_path, params = {}):
    '''
        add the param to request JSON responses to the params object
        I'll first add on the URI prefix
        then add in the params
    '''
    newparams = copy.copy(params)
    newparams["_type"] = "json"
    #assert False, urllib.urlencode(params)
    #assert False, params

    uri = uri_path + "?" + urllib.urlencode(newparams)
    #if re.search("companies", uri_suffix):
        #assert False, uri
    return uri

def verify_status(exp_status, response, msg):
    '''
        Helper that prints out the error message if something other than what's expected
        is returned.
    '''
    data = response.read()
    eq_(response.status, exp_status, msg + ": " + str(data))
    return data

def get_auth_header_user_name(user_name):
    names = user_name.split()
    user_list = get_list_from_search("user",
                                     world.path_users,
                                     {"firstName": names[0], "lastName": names[1]})
    try:
        useremail = user_list[0][ns("email")]
        userpw = get_user_password(user_name)
    except KeyError:
        assert False, "%s\nDidn't find field in %s" % (str(KeyError), user_list)

    return get_auth_header(useremail, userpw)

def log_user_in(name):
    headers = get_json_headers(get_auth_header_user_name(name))
    # log the user in

    return do_put_for_cookie(world.path_users + "login", "", headers)

#@todo: this should do a request.  Or perhaps we should request once before.all and build this map in memory
def get_user_status_id(userStatus):
    statusMap = {"active": 1,
                 "inactive": 2,
                 "disabled": 3}
    return statusMap.get(userStatus)






def do_get(uri, params = {}, headers = get_json_headers(), exp_status = 200):

    record_api_for_step("GET", uri)

    world.conn.request("GET", add_params(uri, params), "", headers)
    response = world.conn.getresponse()
    return verify_status(exp_status, response, str(uri))

def do_put_for_cookie(uri, body, headers = get_form_headers()):
    '''
        usually we don't care about the returned headers,  but in
        the case of login, for instance, we need the cookie it returns
    '''
    method = "PUT"

    record_api_for_step(method, uri)

    world.conn.request(method, add_params(uri),
                       urllib.urlencode(body, doseq=True),
                       headers)
    response = world.conn.getresponse()

    # stolen from Carl Meyer's code
    # Work around httplib2's broken multiple-header handling
    # http://code.google.com/p/httplib2/issues/detail?id=90
    # This will break if a cookie value contains commas.
    cookies = [c.split(";")[0].strip() for c in
               response.getheader("set-cookie").split(",")]
    auth_cookie = [c for c in cookies if c.startswith("USERTOKEN=")][0]



    data = verify_status(200, response, "%s %s:\n%s" % (method, uri, body))
    return data, auth_cookie

def do_put(uri, body, headers = get_form_headers()):
    return do_request("PUT", uri, body = body, headers = headers)

def do_post(uri, body, params = {}, headers = get_form_headers()):
    return do_request("POST", uri, body = body, headers = headers)

def do_delete(uri, params, headers = get_form_headers()):
    return do_request("DELETE", uri, params = params, headers = headers)

def do_request(method, uri, params = {}, body = {}, headers = get_form_headers(), exp_status = 200):
    '''
        do the request
    '''

    record_api_for_step(method, uri)

    world.conn.request(method, add_params(uri, params),
                       urllib.urlencode(body, doseq=True),
                       headers)
    response = world.conn.getresponse()

    return verify_status(exp_status, response, "%s %s:\n%s" % (method, uri, body))

def search_and_verify_existence(uri, search_args, obj_name, existence):
    expect_to_find = (existence.strip() == "exists")
    search_and_verify(uri, search_args, obj_name, expect_to_find)

def search_and_verify(uri, search_args, obj_name, expect_to_find):
    '''
        This does a search based on the search_args passed in.  So "expect_to_find"
        is really filtered based on those parameters.

        expect_to_find: If True, then we verify based on expecting to find something.
                        If False, this will fail if we get a resultset greater than 0.
    '''

    resp_list = get_list_from_search(obj_name, uri, params = search_args)

    if not expect_to_find:
        eq_(len(resp_list), 0, "expect result size zero:\n" + jstr(resp_list))
    else:
        # we want to verify just ONE of the items returned.  Indeed, we likely
        # expect only one.  So we pick the first item returned
        item = resp_list[0]

        # Verify that the result's values match our search params
        for k, v in search_args.items():
            eq_(item.get(ns(k)), v, obj_name + " match")




'''
######################################################################

                     RESID FUNCTIONS

######################################################################
'''
def get_user_resid(name):
    '''
        name: Split into 2 parts at the space.  Only the first two parts are used.  Must have at least 2 parts.
    '''
    names = name.split()
    return get_resource_identity("user", world.path_users, {"firstName": names[0], "lastName": names[1]})

def get_role_resid(role):
    '''
        Get the resourceIdentity of a role, based on the description of the role
    '''
    return get_resource_identity("role", world.path_roles, {"name": role})

def get_product_resid(product):
    '''
        Get the resourceIdentity, based on the name
    '''
    return get_resource_identity("product", world.path_products, {"name": product})

def get_seed_product_id():
    return  get_product_resid(world.seed_product["name"])[0]

def get_company_resid(product):
    return get_resource_identity("company", world.path_companies, {"name": product})

def get_seed_company_id():
    return get_company_resid(world.seed_company["name"])[0]

def get_country_resid(country):
    return get_resource_identity("country", world.path_countries, {"name": country})

def get_environment_resid(environment):
    return get_resource_identity("environment", world.path_environments, {"name": environment})

def get_environmenttype_resid(environment):
    return get_resource_identity("environmenttype", world.path_environmenttypes, {"name": environment})

def get_environmentgroup_resid(environment):
    return get_resource_identity("environmentgroup", world.path_environmentgroups, {"name": environment})

def get_testcase_resid(name):
    return get_resource_identity("testcase", world.path_testcases, {"name" : name})

def get_testsuite_resid(name):
    return get_resource_identity("testsuite", world.path_testsuites, {"name" : name})

def get_testcycle_resid(name):
    return get_resource_identity("testcycle", world.path_testcycles, {"name": name})

def get_testrun_resid(name):
    return get_resource_identity("testrun", world.path_testruns, {"name": name})

def get_tag_resid(tag):
    return get_resource_identity("tag", world.path_tags, {"tag": tag})

def get_resource_identity(obj_name, uri, params):
    '''
        tcm_type: Something like user or role or permission.
        uri: The URI stub to make the call

        Return the id and version as strings

        @TODO: This presumes a list of objects is returned.  So it ONLY returns the resid for
        the first element of the list.  Will almost certainly need a better solution in the future.
        Like a new method "get_resource_identities" which returns a list of ids or something.
    '''

    resp_list = get_list_from_search(obj_name, uri, params = params)
    item = resp_list[0]
    try:
        resid = int(item[ns("resourceIdentity")]["@id"])
        version = item[ns("resourceIdentity")]["@version"]
        return resid, version
    except KeyError:
        assert False, "didn't find expected tcm_type:  %s -- %s or %s in:\n%s" % (ns("resourceIdentity"),
                                                                     "@id",
                                                                     "@version",
                                                                     jstr(resp_list))

def get_testcase_latestversion_id(testcase_id):
    # now get the latest version for that testcase id

    latestversion_uri = world.path_testcases + str(testcase_id) + "/latestversion/"

    response_txt = do_get(latestversion_uri)
    respJson = json_to_obj(response_txt)

    tcm_type = ns("testcaseversion")
    assert respJson.__contains__(tcm_type), "didn't find expected tcm_type: %s in:\n%s" % (tcm_type, jstr(respJson))
    tcv = respJson[tcm_type][0]

    field = ns("resourceIdentity")
    assert tcv.__contains__(field), "didn't find expected tcm_type: %s in:\n%s" % (field, jstr(tcv))
    resid = tcv[field]

    assert resid.__contains__("@id"), "didn't find expected tcm_type: %s in:\n%s" % ("@id", jstr(resid))
    return resid["@id"]







'''
######################################################################

                     LIST FUNCTIONS

######################################################################
'''


def get_list_from_search(tcm_type, uri, params = {}, headers = get_json_headers()):
    '''
        This will always return an array.  May have many, one or no items in it
        it goes into the "searchResult" tcm_type of response
    '''
    response_txt = do_get(uri, params, headers)

    sr_field = ns("searchResult")
    tcm_type = ns(tcm_type)
    pl_type = plural(tcm_type)

    try:
        sr = json_to_obj(response_txt)[sr_field][0]
        if (sr[ns("totalResults")] > 0):
            items = sr[pl_type][tcm_type]
            if (not isinstance(items, list)):
                items = [items]
        else:
            items = []

        return items
    except (KeyError, TypeError) as err:
        assert False, \
            "%s\nDidn't find [%s][0][%s][%s] in\n%s" % \
            (str(err),
             sr_field,
             pl_type,
             ns(tcm_type),
             json_pretty(response_txt))


#def get_list_of_type(tcm_type, response_txt):
#    respJson = json_to_obj(response_txt)
#
#    try:
#        array_of_type = respJson[ns(as_arrayof(tcm_type))][0]
#        if (len(array_of_type) > 1):
#            item = array_of_type[ns(tcm_type)]
#        else:
#            return []
#    except KeyError:
#        assert False, "didn't find expected tcm_type:  %s -- %s in:\n%s" % (ns(as_arrayof(tcm_type)),
#                                                                     ns(tcm_type),
#                                                                     jstr(respJson))

    # If there is only one, this may not come back as a list.  But I don't want to handle
    # that case everywhere, so we guarantee this is a list
#
#    if isinstance(item, list):
#        return item
#    else:
#        return [item]

def get_list_from_endpoint(tcm_type, uri, headers = get_json_headers()):
    '''
        This hits an endpoint.  It goes into the ArrayOfXXX tcm_type of response
    '''
    response_txt = do_get(uri, headers = headers)

    try:
        array_of_type = json_to_obj(response_txt)[ns(as_arrayof(tcm_type))][0]
        if (len(array_of_type) > 1):
            items = array_of_type[ns(tcm_type)]
            if (not isinstance(items, list)):
                items = [items]
        else:
            items = []

        return items
    except (KeyError, TypeError) as err:
        assert False, \
            "%s\nDidn't find [%s][0][%s] in\n%s" % \
            (str(err),
             ns(as_arrayof(tcm_type)),
             ns(tcm_type),
             json_pretty(response_txt))

def get_single_item_from_endpoint(tcm_type, uri, headers = get_json_headers()):
    '''
        This hits an endpoint.  It goes into the ArrayOfXXX tcm_type of response
    '''

    response_txt = do_get(uri, headers = headers)

    try:
        return json_to_obj(response_txt)[ns(tcm_type)][0]
    except KeyError:
        assert False, "%s\nDidn't find %s in %s" % (str(KeyError), ns(tcm_type),response_txt)










'''
    UPLOAD FILES
'''
def encode_multipart_formdata(fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """
    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\r\n'
    L = []
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    for (key, filename, value) in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % get_content_type(filename))
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'



