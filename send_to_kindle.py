import base64
import pathlib
import mimetypes
import time
import os
import argparse
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from mailjet_rest import Client

api_key = # inserir a api key do mailjet'
api_secret = # inserir o secret do mailjet'
sender_email = #
sender_name = #

mailjet = Client(auth=(api_key, api_secret), version='v3.1')

def wait_available(file_path):
    time.sleep(1)
    count = 0
    while count <= 20:
        try:
            if os.access(file_path, os.R_OK):
                print("Arquivo ok")
                return True
        except FileNotFoundError:
            print("Arquivo indisponivel, tentando novamente...")
            count += 1
            time.sleep(1)
            continue
    return False

def send_email(to, content, file_path):
    file = pathlib.Path(file_path)

    with open(file, "rb") as attach_file:
        attachment = str(base64.b64encode(attach_file.read()))[1:]
        print(str(file))
        mimetype = mimetypes.guess_type(file)
        print(mimetype)

    data = {
        'Messages': [
            {
                "From": {
                    "Email": sender_email,
                    "Name": sender_name
                },
                "To": [
                    {
                        "Email": to
                    }
                ],
                "Subject": 'convert',
                "TextPart": content,
                "attachments": [
                    {
                        "Filename": file.name,
                        "ContentType": mimetype[0],
                        "Base64Content": attachment
                    }]
            }
        ]
    }

    result = mailjet.send.create(data=data)
    print(result.status_code)
    print(result.json())


class Handler(FileSystemEventHandler):
    last_file = ""
    def __init__(self, email):
        self.email = email

    def on_created(self, event):
        if (not wait_available(event.src_path)):
            print("Arquivo indisponivel")
            return
        if (event.src_path == Handler.last_file):
            print("Arquivo duplicado")
            return
        Handler.last_file = event.src_path
        send_email(self.email, pathlib.Path(event.src_path).name, event.src_path)


def start_observer(path, email):
    event_handler = Handler(email)

    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)

    observer.start()
    try:
        while True:
            time.sleep(1)
    finally:
        observer.join()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("kindle_email", help="The kindle device email")
    parser.add_argument("folder", help="The folder to monitor")
    args = parser.parse_args()

    start_observer(args.folder, args.kindle_email)


if __name__ == "__main__":
    main()
