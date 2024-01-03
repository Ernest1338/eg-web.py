#!/bin/python

from web import App, read_file


def api_button2():
    return "<h1>Button 2 content</h1>"


App(
    {
        "/": lambda: read_file("index.html"),
        "/api/button1": lambda: "Hi from the server!",
        "/api/button2": api_button2,
    }
).run()
