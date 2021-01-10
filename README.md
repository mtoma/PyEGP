# PyEGP
Pyton interface to SAS Enterprise Guide Project .egp files

```python
from py_egp import PyEGP

sas_process = PyEGP('/path/to/Project.egp')
sas_process.print_main_project()
```

```
Main
+-- Task 1
    +-- Task 2
        +-- Task 3
            +-- Task 4
                |-- Task 4.1
                +-- Task 4.2

```
