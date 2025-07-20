Gradesta file browser
-------------------------

This is an example gradesta graph provider which communicates via websockets.

In a gradesta graph each vertex can have up to 4 edges, each one corresponding to the directions up, down, left and right.

A each vertex in a gradesta graph has up to 4 slots:

- audio
- image
- text
- file

The protocol is two way. The graph browser can send a command like:

```
{"get": "<cell-id>"}
```

Or

```
{"update": {
    "cell-id": "<cell-id>",
    "audio": "base64",   //optional, nill to unset
    "image": "base64",   //optional, nill to unset
    "text": "string",    //optional, nill to unset
    "file": "base64",    //optional, nill to unset
    "left": "<cell-id>", //optional, nill to unset
    "right": "<cell-id>",//optional, nill to unset
    "up": "<cell-id>",   //optional, nill to unset
    "down": "<cell-id>"  //optional, nill to unset
}}
```

The graph provider will respond with only one type of response:

```
{
    "cell-id": "<cell-id>",
    "audio": "base64",   //optional
    "image": "base64",   //optional
    "text": "string",    //optional
    "file": "base64",    //optional
    "left": "<cell-id>", //optional
    "right": "<cell-id>",//optional
    "up": "<cell-id>",   //optional
    "down": "<cell-id>", //optional
    "skeleton": bool,    //sets if the cell is real (false), or a skeleton (true)
    "iframe": "<uri>",   //URI to open in iframe view
    "writeable": ["audio", "image", "text", "file", "left", "right", "up", "down"]
    //list of writable (to the client) fields
}
```
