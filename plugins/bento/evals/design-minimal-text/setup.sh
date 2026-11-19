#!/bin/bash
set -euo pipefail
git init -q -b master .
cat > index.html <<'HTML'
<!doctype html>
<html>
<head><title>Projects</title></head>
<body>
  <header><h1>Projects</h1></header>
  <main id="projects"></main>
  <script>
    const projects = [];
    const main = document.getElementById("projects");
    for (const p of projects) main.insertAdjacentHTML("beforeend", `<article>${p.name}</article>`);
  </script>
</body>
</html>
HTML
git add -A && git -c user.name=Dev -c user.email=dev@example.com commit -qm "Add the projects page"
