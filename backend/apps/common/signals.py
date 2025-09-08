# apps/common/signals.py
from django.dispatch import Signal

# args attendus:
# - publish_status_changed: instance, old_status, new_status
# - soft_deleted: instance
publish_status_changed = Signal()
soft_deleted = Signal()
