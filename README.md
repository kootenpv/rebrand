## rebrand

Refactor your software using programming language independent string replacement.

Helps by renaming directories, filenames and file contents in a case-preserving manner.

![rebrand demo](/resources/demo.gif)

## Installation

    pip install rebrand

## Usage

    rebrand run <OLD> <NEW> <LOCATION>
    # e.g. rebrand run ancient modern .

## TODO:

- Implement faster matching
- More options (such as disabling image warnings, verbose)
- Switch from `fire` back to `argparse`
