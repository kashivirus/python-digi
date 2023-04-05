"""Generates refresh token for AdWords using the Installed Application flow."""


import sys

from oauth2client import client

from django.conf import settings

# Your OAuth 2.0 Client ID and Secret. If you do not have an ID and Secret yet,
# please go to https://console.developers.google.com and create a set.
CLIENT_ID = "988169984630-315oq2dvf0k51pug1nso1bjv6jujrca3.apps.googleusercontent.com"
CLIENT_SECRET = "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"

# The AdWords API OAuth 2.0 scope.
SCOPE = u'https://www.googleapis.com/auth/adwords'


def main():
  """Retrieve and display the access and refresh token."""
  flow = client.OAuth2WebServerFlow(
      client_id=CLIENT_ID,
      client_secret=CLIENT_SECRET,
      scope=[SCOPE],
      user_agent='Ads Python Client Library',
      redirect_uri='urn:ietf:wg:oauth:2.0:oob')

  authorize_url = flow.step1_get_authorize_url()

  print('Log into the Google Account you use to access your AdWords account'
        'and go to the following URL: \n{}\n'.format(authorize_url))
  print('After approving the token enter the verification code (if specified).')
  code = input('Code: ').strip()

  try:
    credential = flow.step2_exchange(code)
  except client.FlowExchangeError as e:
    print('Authentication has failed: {}'.format(e))
    sys.exit(1)
  else:
    print('OAuth 2.0 authorization successful!\n\n'
          'Your access token is:\n {}\n\nYour refresh token is:\n {}'.format(
          credential.access_token, credential.refresh_token))


if __name__ == '__main__':
  main()