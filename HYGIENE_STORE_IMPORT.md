# Hygiene Store project import

A dedicated branch `hygiene-store-project` has been created for this project. The source archive contains a Django e-commerce application (accounts, shop, cart, orders), Docker configuration, templates, and static assets. The uploaded ZIP has not yet been committed as source files; this note intentionally does not claim that the full project has been uploaded.

## Audit notes
- Python source files passed syntax compilation.
- Django runtime checks and automated tests could not be run in this environment because Django is not installed.
- No migration files were present in the archive; generate and commit migrations before deploying.
- Review production configuration, especially `ALLOWED_HOSTS`, `SECRET_KEY`, OTP delivery, payment gateway settings, and Docker startup migrations, before public deployment.
