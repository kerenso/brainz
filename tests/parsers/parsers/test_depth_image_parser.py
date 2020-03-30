import json
import os
import pathlib
from datetime import datetime, timezone

from brain_computer_interface.parsers.context import Context
from brain_computer_interface.parsers.parsers.depth_image_parser import parse_depth_image
from brain_computer_interface.protocol.parsers_saver import deserialize
from brain_computer_interface.protocol.server_parsers import serialize

RESOURCES = pathlib.Path(__file__).absolute().parent.parent.parent / 'resources' / 'parsers' / 'parsers'
_USER = {'user_id': '1', 'name': 'Keren Solodkin', 'birthday': datetime(1997, 2, 25, tzinfo=timezone.utc).timestamp(),
         'gender': 'f'}
_TIMESTAMP = datetime(2019, 10, 25, 15, 12, 5, 228000, tzinfo=timezone.utc)

with open(RESOURCES / 'depth_image.json', 'rb+') as f:
    image = json.load(f)
_SNAPSHOT = {'timestamp': _TIMESTAMP.timestamp() * 1000, 'depth_image': dict(height=172, width=224, data=image)}
with open(RESOURCES / 'depth_image.jpg', 'rb') as f:
    _DATA = f.read()


def test_parser():
    depth_image_path = _get_path(Context.BASE_DIR, _USER, _TIMESTAMP)
    if depth_image_path.exists():
        os.remove(depth_image_path)
    assert not depth_image_path.exists()

    result = deserialize(parse_depth_image(serialize(_USER, _SNAPSHOT)))

    assert result['user'] == _USER
    assert result['timestamp'] == _TIMESTAMP.timestamp()
    assert result['path'] == str(depth_image_path.absolute())
    assert depth_image_path.read_bytes() == _DATA

    os.remove(depth_image_path)


def _get_path(data_dir, user, timestamp):
    return data_dir / user['user_id'] / f'{timestamp:%Y-%m-%d_%H-%M-%S-%f}/depth_image.jpg'