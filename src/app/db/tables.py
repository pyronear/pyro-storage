# Copyright (C) 2022-2023, Pyronear.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.


from .models import Accesses, Annotations, Media
from .session import Base

__all__ = ["metadata", "accesses", "media", "annotations"]

accesses = Accesses.__table__
media = Media.__table__
annotations = Annotations.__table__

metadata = Base.metadata
