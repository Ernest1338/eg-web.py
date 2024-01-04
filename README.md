<h1><p align=center>eg-web.py</p></h1>
<h3><p align=center>Simple Python Web Framework with Template Support Included</p></h3>
<br \><br \>

# Example
```Python
from web import App, read_file, Template


Templates = {"index": Template("index.html")}


def api_button2():
    return "<h1>Button 2 content</h1>"


App(
    {
        "/": lambda: Templates["index"].render({"body": "Content"}),
        "/api/button1": lambda: "Hi from the server!",
        "/api/button2": api_button2,
        "/index": lambda: read_file("index.html"),
    }
).run()
```

# License
### MIT

