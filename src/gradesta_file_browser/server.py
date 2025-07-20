import os
import mimetypes
import base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import Optional

app = FastAPI()

# Utility functions for file type detection and encoding
def get_file_type(path):
    mime, _ = mimetypes.guess_type(path)
    if mime is None:
        return 'file'
    if mime.startswith('text'):
        return 'text'
    if mime.startswith('image'):
        return 'image'
    if mime.startswith('audio'):
        return 'audio'
    return 'file'

def encode_file(path, mode='rb'):
    with open(path, mode) as f:
        data = f.read()
        if 'b' in mode:
            return base64.b64encode(data).decode('utf-8')
        return data

def get_cell(path: str) -> dict:
    """
    Return a cell dict for the given path, following the Gradesta protocol.
    """
    cell = {
        'cell-id': path,
        'skeleton': False,
        'writeable': ['audio', 'image', 'text', 'file', 'left', 'right', 'up', 'down']
    }
    if os.path.isdir(path):
        # Directory: vertical doubly-linked list of entries
        try:
            entries = sorted(os.listdir(path))
        except PermissionError:
            entries = []
            cell['text'] = f"[Permission denied] {os.path.basename(path) or path}"
        cells = [os.path.join(path, e) for e in entries]
        # Add .. cell at the top unless root
        parent = os.path.dirname(path.rstrip('/')) or '/'
        if path != '/':
            cells = ['..'] + cells
        # Build up/down links
        idx = None
        if path != '/':
            idx = 1  # .. is at 0
        else:
            idx = 0
        for i, cell_path in enumerate(cells):
            if cell_path == '..':
                continue
            if i > 0:
                cell['up'] = cells[i-1]
            if i < len(cells)-1:
                cell['down'] = cells[i+1]
        if 'text' not in cell:
            cell['text'] = os.path.basename(path) or '/'
        if path != '/':
            cell['left'] = parent
    else:
        # File: link left to parent, set appropriate slot
        parent = os.path.dirname(path.rstrip('/')) or '/'
        cell['left'] = parent
        ftype = get_file_type(path)
        if ftype == 'text':
            try:
                cell['text'] = encode_file(path, 'r')
            except Exception:
                cell['file'] = encode_file(path)
        elif ftype == 'image':
            cell['image'] = encode_file(path)
        elif ftype == 'audio':
            cell['audio'] = encode_file(path)
        else:
            cell['file'] = encode_file(path)
    return cell

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            if 'get' in data:
                cell_id = data['get']
                if cell_id == '..':
                    cell_id = os.path.dirname(os.getcwd())
                cell = get_cell(cell_id)
                await websocket.send_json(cell)
            elif 'update' in data:
                # For now, just echo the update as a get
                cell_id = data['update'].get('cell-id')
                cell = get_cell(cell_id)
                await websocket.send_json(cell)
    except WebSocketDisconnect:
        pass 