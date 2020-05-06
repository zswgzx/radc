# RADC MRI Python Utilities #

MRI_Python is a group of utilities used to inventory and manipulate MRI data using python.

### How do I get set up? ###

* Where can we run this code?

  The utilities should be able to run directly

* How is it developed and tested?

  You may clone this project locally for development purposes or edit on the server directly


### Helpful Snippets ###
``` python
result = check_output(["/u3/informix/bin/dbaccess", "radc", "<script path>"], encoding="UTF-8", stderr=DEVNULL).strip()
for line in result.splitlines():
    print( line.strip().split() )
```
