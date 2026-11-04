#!/bin/bash
source "$(dirname "$0")/../_fixtures/workflow.sh"
cat > charge.py <<'P'
import json
from urllib.request import Request, urlopen

GATEWAY = "https://payments.invalid/v1/charges"


def charge(cents):
    request = Request(GATEWAY, data=json.dumps({"amount": cents}).encode(), method="POST")
    with urlopen(request, timeout=3) as response:
        return json.load(response)["status"]
P
cat > test_live.py <<'P'
import unittest

from charge import charge


class LiveGateway(unittest.TestCase):
    def test_a_real_charge_is_accepted(self):
        self.assertEqual(charge(100), "accepted")


if __name__ == "__main__":
    unittest.main()
P
git add -A && git commit -qm "Add the gateway client and its live test"
