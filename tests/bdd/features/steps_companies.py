'''
Created on Jan 31, 2011

@author: camerondawson
'''

from lettuce import *
#from nose.tools import *
from step_helper import *


'''
######################################################################

                     COMPANY STEPS

######################################################################
'''

@step(u'company with (that name|name "(.*)") (does not exist|exists)')
def check_company_foo_existence(step, stored, name, existence):
    name = get_stored_or_store_name("company", stored, name)
    search_and_verify_existence(step, world.path_companies, 
                    {"name": name}, 
                     "company", existence)


@step(u'create a new company with name "(.*)"')
def create_a_new_company_with_name(step, company_name):
    post_payload = {"name": company_name,
                    "phone": "617-417-0593",
                    "address": "31 lakeside drive",
                    "city": "Boston",
                    "zip": "01721",
                    "url": "http//www.utest.com",
                    "countryId": 123
                    }
    headers = {'Authorization': get_auth_header()}

    world.conn.request("POST", add_params(world.path_companies, post_payload), "", headers)
    #world.conn.send(post_payload)
    response = world.conn.getresponse()
    verify_status(200, response, "create new company")


@step(u'delete the company with (that name|name "(.*)")')
def delete_company_with_name(step, stored, name):
    name = get_stored_or_store_name("company", stored, name)
    
    headers = {'Authorization': get_auth_header(),
               'content-type': "application/x-www-form-urlencoded"
               }

    resid, version = get_resource_identity("company", add_params(world.path_companies, {"name": name}))
               
    world.conn.request("DELETE", 
                       add_params(world.path_companies + resid, 
                                  {"originalVersionId": version}), "", headers)

    response = world.conn.getresponse()
    verify_status(200, response, "delete company")


@step(u'search all Companies')
def search_all_companies(step):
    assert False, 'This step must be implemented'

