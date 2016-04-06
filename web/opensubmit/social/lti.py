'''
	LTI authentication, based on the passthrough backend.
'''

from passthrough import PassThroughAuth

class LtiAuth(PassThroughAuth):
    name='lti'
