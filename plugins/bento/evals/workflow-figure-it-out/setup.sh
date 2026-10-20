#!/bin/bash
source "$(dirname "$0")/../_fixtures/workflow.sh"
mkdir -p exports
printf '[{"id":1,"v":"a"},{"id":2,"v":"b"},{"id":3,"v":"old"}]
' > exports/a.json
printf '[{"id":1,"v":"a"},{"id":3,"v":"new"}]
' > exports/b.json
