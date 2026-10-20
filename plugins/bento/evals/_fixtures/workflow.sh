#!/bin/bash
# A local-only repository with passing tests and three layers for continuation cases.
source "$(dirname "$0")/../_fixtures/repo.sh"
cat > formatter.py <<'CODE'
def greeting(name):
    return "hi " + name
CODE
cat > app.py <<'CODE'
from formatter import greeting


def greet(name):
    return greeting(name)


def shout(name):
    return greet(name).upper()
CODE
cat > cli.py <<'CODE'
import argparse
from app import greet

parser = argparse.ArgumentParser()
parser.add_argument("name")
args = parser.parse_args()
print(greet(args.name))
CODE
cat > test_app.py <<'CODE'
import unittest
from app import greet, shout


class GreetingTest(unittest.TestCase):
    def test_greet(self):
        self.assertEqual(greet("bob"), "hi bob")

    def test_shout(self):
        self.assertEqual(shout("bob"), "HI BOB")
CODE
git add app.py formatter.py cli.py test_app.py
git commit -q -m "test: add greeting layers and baseline tests"
