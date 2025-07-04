"""
This example describes how to use the workflow interface to chat.
"""

import os, json, requests, sys
# Our official coze sdk for Python [cozepy](https://github.com/coze-dev/coze-py)
from cozepy import COZE_CN_BASE_URL

# Get an access_token through personal access token or oauth.
coze_api_token = 'pat_6iWlxRyOqUkjrZcLGHzIiJVLPvyySxS6OtEuphbUiCJ3bQRpiy4bGboe34UDIGxc'
# The default access is api.coze.com, but if you need to access api.coze.cn,
# please use base_url to configure the api endpoint to access
coze_api_base = COZE_CN_BASE_URL

from cozepy import Coze, TokenAuth, Message, ChatStatus, MessageContentType  # noqa

# Init the Coze client through the access_token.
coze = Coze(auth=TokenAuth(token=coze_api_token), base_url=coze_api_base)

# Create a workflow instance in Coze, copy the last number from the web link as the workflow's ID.
workflow_id = '7523488680905768994'

data_dir = sys.argv[1]
title = sys.argv[2]

parameters = {
    "input": title,
}

# Call the coze.workflows.runs.create method to create a workflow run. The create method
# is a non-streaming chat and will return a WorkflowRunResult class.
workflow = coze.workflows.runs.create(
    workflow_id=workflow_id,
    parameters=parameters
)

#print("workflow.data", workflow.data.get("input"))

data = json.loads(workflow.data)
urls = data.get("input")
i = 0
for url in urls.split("|"):
    print(url)
    response = requests.get(url)
    filename = f"{data_dir}/pic_cover_{i}.jpg"
    with open(filename, "wb") as f:
        print(filename)
        f.write(response.content)
        i += 1