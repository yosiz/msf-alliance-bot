from datetime import datetime

a = datetime.utcnow()

print(a)

print(a.isoformat())

print(getattr(a, "isoformat", lambda:None)())
