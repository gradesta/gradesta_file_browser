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
    try:
        with open(path, mode) as f:
            data = f.read()
            if 'b' in mode:
                return base64.b64encode(data).decode('utf-8')
            return data
    except (OSError, IOError, UnicodeDecodeError) as e:
        return f"[Error reading file: {str(e)}]"

def get_cell(cell_id: str) -> dict:
    """
    Return a cell dict for the given cell_id, supporting both file:// and listing:// protocols.
    """
    if cell_id.startswith('listing://'):
        path = cell_id[len('listing://'):]
        parent = os.path.dirname(path.rstrip('/')) or '/'
        if not os.path.exists(parent):
            return {
                'cell-id': cell_id,
                'skeleton': False,
                'writeable': [],
                'text': f'[Not found] {path}'
            }
        try:
            entries = sorted(os.listdir(parent))
        except PermissionError:
            entries = []
        names = [os.path.join(parent, e) for e in entries]
        idx = names.index(path) if path in names else -1
        cell = {
            'cell-id': cell_id,
            'skeleton': False,
            'writeable': [],
            'text': os.path.basename(path) or path,
            'right': f'file://{path}'
        }
        if idx > 0:
            cell['up'] = f'listing://{names[idx-1]}'
        if idx < len(names) - 1:
            cell['down'] = f'listing://{names[idx+1]}'
        if parent != '/':
            cell['left'] = f'listing://{parent}'
        return cell

    elif cell_id.startswith('file://'):
        path = cell_id[len('file://'):]
        if not os.path.exists(path):
            return {
                'cell-id': cell_id,
                'skeleton': False,
                'writeable': [],
                'text': f'[Not found] {path}'
            }
        cell = {
            'cell-id': cell_id,
            'skeleton': False,
            'writeable': []
        }
        parent = os.path.dirname(path.rstrip('/')) or '/'
        cell['left'] = f'listing://{path}'
        if os.path.isdir(path):
            cell['text'] = path
            try:
                entries = sorted(os.listdir(path))
            except PermissionError:
                entries = []
                cell['text'] = f"[Permission denied] {path}"
            if entries:
                first_entry = os.path.join(path, entries[0])
                cell['down'] = f'listing://{first_entry}'
        else:
            # Check if we can read the file before attempting to encode it
            if not os.access(path, os.R_OK):
                cell['text'] = f"[Permission denied] {path}"
            else:
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
    else:
        return get_cell(f'file://{cell_id}')

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