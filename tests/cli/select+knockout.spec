# Grep for a field, then knock out another.
[".features > *:has(:contains(\"Aruba\"))", "-v", ".coordinates", "tests/cli/basic.geo.json"]
