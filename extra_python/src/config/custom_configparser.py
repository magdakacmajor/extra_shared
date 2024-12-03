'''
Created on 11 Nov 2018

@author: root
'''

import configparser
import re
import json
import os


class CustomConfigParser():
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.config = configparser.ConfigParser()
        self.config.read(
            f'{os.path.abspath(os.path.dirname(__file__))}/config.txt')

    def get_server_port(self):
        return self.config.getint('SERVER', 'port')

    def get_user(self):
        return self.config['SERVER']['usr']

    def get_upload_dir(self):
        return self.config['SERVER']['upload_dir']

    def get_hyperparams(self):
        props = dict(self.config.items('HYPERPARAMS'))
        return self.parse_from_string(props)

    def get_java_classpath(self):
        return self.config['JAVA']['classpath']

    def get_java_jythonpath(self):
        return self.config['JAVA']['jython_path']

    def get_tokenization_params(self):
        props = dict(self.config.items('TOKENIZATION'))
        return self.parse_from_string(props)

    def parse_from_string(self, props):
        for key in props:
            if props[key] in ['true', 'false']:
                props[key] = props[key] == 'true'
            elif re.fullmatch(r'\d+', props[key]):
                props[key] = int(props[key])
            elif re.fullmatch(r'\d*\.\d+', props[key]):
                props[key] = float(props[key])
            elif props[key].startswith('['):
                props[key] = json.loads(props[key])
        return props
