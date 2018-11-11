# Unit Tests

In order to run these unit tests you need to make sure, 
that the root folder of the repository is called "VHDLMode".
This is required, such that the test scripts can import the
files in the root folder. This is a workaround to deal with
the weird way, relative imports work in Python.

## Dependencies
You will need to install the following dependencies: `sublime`,
`ruamel.yaml`. Alternatively, you can just create empty files
for the purpose of running the unit tests.

## Running the Tests using PyCharm
Set the content root to the directory *above* VHDLMode. Then
you should be able to run the unit tests without any further
changes.

## Running the Tests on the Command Line
Run the following command in the directory *above* the root 
of the repository:

```python -m unittest discover -s "VHDLMode/Test"```