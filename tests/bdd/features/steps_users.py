'''
Created on Jan 28, 2011

@author: camerondawson
'''
from lettuce import *
#from nose.tools import *
from step_helper import *

'''
######################################################################

                     USER HELPER FUNCTIONS

######################################################################
'''

def create_user_from_obj(user_obj):
    '''
        Create a user based on an already formed user object
    '''
    do_post(world.path_users,
            user_obj)
    
def create_user_from_name(name):
    '''
        Create a user based on just the user name and seed data
    '''
    names = name.split()
    fname = names[0]
    lname = names[1]
    user_obj = {
                "firstName":fname,
                "lastName":lname,
                "email":fname+lname + "@mozilla.com",
                "screenName":fname+lname,
                "password":get_user_password(name),
                "companyId":get_seed_company_id(),
    } 
    create_user_from_obj(user_obj)

'''
######################################################################

                     USER STEPS

######################################################################
'''
    

@step(u'create a new user with (that name|name "(.*)")')
def create_user_with_name_foo(step, stored, name):
    name = get_stored_or_store_name("user", stored, name)
    create_user_from_name(name)
    
@step(u'logged in as user "(.*)"')
def logged_in_as_user_foo(step, name):
    names = name.split()
    world.user_name = name
    
    name_headers = { 'firstName':names[0], 'lastName': names[1] }

    world.conn.request("GET", add_params(world.path_users + "current"), None, name_headers)
    response = world.conn.getresponse()
    data = verify_status(200, response, "Fetched a user")
    
    thisUser = get_single_item(data, ns("user"))

    eq_(thisUser.get(ns("firstName")), names[0], "First Name field didn't match")
    eq_(thisUser.get(ns("lastName")), names[1], "Last Name field didn't match")

@step(u'user with (that name|name "(.*)") (exists|does not exist)')
def check_user_foo_existence(step, stored, name, existence):
    names = get_stored_or_store_name("user", stored, name).split()
    search_and_verify_existence(step, world.path_users, 
                    {"firstName": names[0], "lastName": names[1]}, 
                    "user", existence)

@step(u'user with (that name|name "(.*)") is (active|inactive|disabled)')
def check_user_foo_activated(step, stored, name, userStatus):
    names = get_stored_or_store_name("user", stored, name).split()
    statusId = get_user_status_id(userStatus) 
        
    # we DO expect to find this user, but we're just checking if they're activated or 
    # deactivated
    search_and_verify(step, world.path_users, 
                    {"firstName": names[0], "lastName": names[1], "userStatusId": statusId}, 
                    "user", True)
    
@step(u'(activate|deactivate) the user with (that name|name "(.*)")')
def activate_user_with_name_foo(step, status_action, stored, name):
    '''
        Users are not deleted, they're just registered or unregistered.
    '''
    name = get_stored_or_store_name("user", stored, name)
    
    resid, version = get_user_resid(name)
    headers = {'Authorization': get_auth_header()}

    url = add_params(world.path_users_activation % (resid, status_action), {"originalVersionId": version})
    world.conn.request("PUT", url, "", headers)

    response = world.conn.getresponse()
    verify_status(200, response, "%s new user" % (status_action))


@step(u'user "(.*)" has these roles:')
def foo_has_these_roles(step, name):
    user_id = get_user_resid(name)[0]

    world.conn.request("GET", add_params(world.path_users + user_id + "/roles"))
    response = world.conn.getresponse()
    eq_(response.status, 200, "Fetched a user")

    # walk through all roles for this user to see if it has the requested one
    respJson = get_resp_list(response, "role")

    # now walk through the expected roles and check the response
    # to see that it is represented
    roles = step.hashes
    for exp_role in roles:
        found = False
        for act_role in respJson:
            exp = exp_role.get(ns("description"))
            act = act_role.get(ns("description"))
            if (exp == act):
                found = True
        eq_(found, True, "expected role of: " + exp)

@step(u'user "(.*)" has these assignments:')
def foo_has_these_assignments(step, name):
    user_id = get_user_resid(name)[0]
    world.conn.request("GET", add_params(world.path_users + user_id + "/assignments"))
    response = world.conn.getresponse()
    eq_(response.status, 200, "Fetched a user")

    # walk through all roles for this user to see if it has the requested one
    respJson = get_resp_list(response, "testcase")

    # now walk through the expected roles and check the response
    # to see that it is represented
    exp_list = step.hashes
    for exp_item in exp_list:
        found = False
        for act_item in respJson:
            exp = exp_item.get(ns("name"))
            act = act_item.get(ns("name"))
            if (exp == act):
                found = True
        eq_(found, True, "expected assignment of: " + str(exp) +
                      "\nin response:\n" + jstr(respJson))

