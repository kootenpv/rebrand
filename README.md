## rebrand

Refactor your software using programming language independent string replacement.

Helps by renaming directories, filenames and file contents in a case-preserving manner.

![rebrand demo](/resources/demo.gif)

## How does it work

Imagine we want to rename a library called `SomeThing` to `AnotherName`.

It will first normalize `"SomeThing`" to `["some", "thing"]` and `"AnotherName`" to `["another", "name"]`, and build patterns on this.

Then, when matching and replacing, it will memorize the casing pattern and separator on e.g. `"Some-thing"` to replace it with the same convention, like so: `"Another-name"`.

This works for:

- filenames
- directories
- file contents

Binaries are just copied, and warnings are currently shown for png and jpg files containing logo or icon.

## Installation

    pip install rebrand

## Usage

    rebrand run <OLD> <NEW> <LOCATION>
    # e.g. rebrand run ancient modern .

## TODO:

- Implement radically faster matching
- More options (such as disabling image warnings, verbosity, ignore patterns)
- Switch from `fire` back to `argparse`
