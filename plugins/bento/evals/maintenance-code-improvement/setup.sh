#!/bin/bash
source "$(dirname "$0")/../_fixtures/maintenance.sh"
cat > src/shared.py <<'PY'
def normalize(value):
    return value.strip().casefold()
PY
cat > src/customer.py <<'PY'
def customer_key(value):
    return value.strip().casefold()
PY
cat > src/test_customer.py <<'PY'
import unittest
from customer import customer_key
from shared import normalize
class CustomerTests(unittest.TestCase):
    def test_keys(self):
        for value in (" A ", "Straße", "", "X\\t"):
            self.assertEqual(customer_key(value), normalize(value))
PY
git add -A
git commit -q -m "test: maintenance-code-improvement"
