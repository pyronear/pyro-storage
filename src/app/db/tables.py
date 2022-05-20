# Copyright (C) 2022, Pyronear.

# This program is licensed under the Apache License version 2.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0.txt> for full license details.


from .models import Accesses, Annotations, Media
from .session import Base

__all__ = ['metadata', 'accesses', 'media', 'annotations']

accesses = Accesses.__table__
media = Media.__table__
annotations = Annotations.__table__

metadata = Base.metadata
