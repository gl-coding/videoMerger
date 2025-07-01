"""
This example describes how to use the workflow interface to stream chat.
"""

import os, json, sys
# Our official coze sdk for Python [cozepy](https://github.com/coze-dev/coze-py)
from cozepy import COZE_CN_BASE_URL

# Get an access_token through personal access token or oauth.
coze_api_token = 'pat_6iWlxRyOqUkjrZcLGHzIiJVLPvyySxS6OtEuphbUiCJ3bQRpiy4bGboe34UDIGxc'
# The default access is api.coze.com, but if you need to access api.coze.cn,
# please use base_url to configure the api endpoint to access
coze_api_base = COZE_CN_BASE_URL

from cozepy import Coze, TokenAuth, Stream, WorkflowEvent, WorkflowEventType  # noqa

# Init the Coze client through the access_token.
coze = Coze(auth=TokenAuth(token=coze_api_token), base_url=coze_api_base)

# Create a workflow instance in Coze, copy the last number from the web link as the workflow's ID.
workflow_id = '7520641397058437163'


# The stream interface will return an iterator of WorkflowEvent. Developers should iterate
# through this iterator to obtain WorkflowEvent and handle them separately according to
# the type of WorkflowEvent.

def write_to_file(data_file, content):
    with open(data_file, 'w') as f:
        f.write(content)

def handle_workflow_iterator(stream: Stream[WorkflowEvent]):
    for event in stream:
        if event.event == WorkflowEventType.MESSAGE:
            #print("got message", event.message)
            #print("got message", event.message.content)
            message_json = event.message.content
            message_dict = json.loads(message_json)
            for k, v in message_dict.items():
                data_file = f"{data_file_prefix}_{k}.txt"
                write_to_file(data_file, v)

            #rewrite_content = message_dict['rewrite']
            #title_content = message_dict['title']
            #subtitle_content = message_dict['subtitle']
            #write_to_file(data_file, rewrite_content)
            #write_to_file(title_file, title_content)
            #write_to_file(subtitle_file, subtitle_content)
        elif event.event == WorkflowEventType.ERROR:
            print("got error", event.error)
        elif event.event == WorkflowEventType.INTERRUPT:
            handle_workflow_iterator(
                coze.workflows.runs.resume(
                    workflow_id=workflow_id,
                    event_id=event.interrupt.interrupt_data.event_id,
                    resume_data="hey",
                    interrupt_type=event.interrupt.interrupt_data.type,
                )
            )

filename = sys.argv[1]
data_file_prefix = f"{filename}"
#data_file = f"{filename}.txt"
#title_file = f"{filename}_title.txt"
#subtitle_file = f"{filename}_subtitle.txt"


handle_workflow_iterator(
    coze.workflows.runs.stream(
        workflow_id=workflow_id,
    )
)