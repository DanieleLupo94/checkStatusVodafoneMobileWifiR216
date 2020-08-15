import requests

SKILL_ID = 'amzn1.ask.skill.1bef177d-03ee-468a-9580-a17c3775b96a'  # iftt notification
# SKILL_ID = 'amzn1.ask.skill.1e17ba0c-cf21-437b-b4e1-ebdb59a7841e'  # ExampleMessageSkill
# dal pannello skill
SKILL_CLIENT_ID = 'amzn1.application-oa2-client.d764c3df43fd4e02bcd87607cd133660'
# dal pannello skill
SKILL_CLIENT_SECRET = '4a17b61f5ff025f3cf44a58d35245d4ddefba1ed413f7a660587298c561dd65a'
# SKILL_CLIENT_ID = 'amzn1.application-oa2-client.b76e197d734b45cc9a57e14bb8f487da'
# SKILL_CLIENT_SECRET = '7a95c4cec4f03fb49bb1ba335f14b62c6d2d0ff45c68374ac80f7fc33045a14c'
API_TOKEN_URL = 'https://api.amazon.com/auth/O2/token'


def richiediToken():
    scope = "alexa:skill_messaging"
    # scope = "messaging:push"
    payload = "grant_type=client_credentials&scope=" + scope + "&client_id=" + \
        SKILL_CLIENT_ID + "&client_secret=" + SKILL_CLIENT_SECRET
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    print("Header: ", headers)
    print("Body: ", payload)
    richiestaToken = requests.post(
        API_TOKEN_URL, data=payload, headers=headers)
    print("Risposta:")
    print(richiestaToken.json())


richiediToken()
